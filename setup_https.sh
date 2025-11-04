#!/bin/bash

# Talking Orange - HTTPS Setup Script
# This script sets up free HTTPS using Let's Encrypt and nginx

set -e

echo "🔒 Setting up HTTPS for Talking Orange"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: sudo ./setup_https.sh your-domain.com [email] [port]"
    echo ""
    echo "Example: sudo ./setup_https.sh AR.juangalt.com"
    echo "         sudo ./setup_https.sh AR.juangalt.com juan@juangalt.com 8080"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"juan@juangalt.com"}
NGINX_PORT=${3:-"8080"}

# Detect project root (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL (for Let's Encrypt notifications)"
echo "   Project Root: $PROJECT_ROOT"
echo "   Nginx Port: $NGINX_PORT (certbot will use port 80 temporarily)"
echo ""

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
    echo "✅ Certbot installed"
else
    echo "✅ Certbot already installed"
fi

# Create nginx configuration
echo "📝 Creating nginx configuration..."
NGINX_CONFIG="/etc/nginx/sites-available/talking-orange"

# Create HTTP-only config first (certbot will add SSL)
cat > "$NGINX_CONFIG" << EOF
# Talking Orange - HTTP server (certbot will add HTTPS)
server {
    listen $NGINX_PORT;
    listen [::]:$NGINX_PORT;
    server_name $DOMAIN;

    # Increase upload size for audio files
    client_max_body_size 10M;

    # Frontend static files
    location / {
        root $PROJECT_ROOT/frontend;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Increase timeouts for long-running requests (audio processing)
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Backend static files (fallback)
    location ~ ^/(backend|uploads|data)/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "✅ Nginx configuration created at $NGINX_CONFIG (HTTP only - certbot will add HTTPS)"
echo ""

# Enable the site
if [ ! -L "/etc/nginx/sites-enabled/talking-orange" ]; then
    ln -s "$NGINX_CONFIG" /etc/nginx/sites-enabled/talking-orange
    echo "✅ Enabled nginx site"
else
    echo "✅ Nginx site already enabled"
fi

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if command -v nginx &> /dev/null; then
    nginx -t
else
    /usr/sbin/nginx -t
fi
if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

# Check if the nginx port is in use
echo "🔍 Checking if port $NGINX_PORT is available..."
PORT_IN_USE=false
if command -v lsof &> /dev/null; then
    if lsof -i :$NGINX_PORT &> /dev/null; then
        PORT_IN_USE=true
        echo "⚠️  Port $NGINX_PORT is already in use:"
        lsof -i :$NGINX_PORT || true
    fi
elif command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":$NGINX_PORT "; then
        PORT_IN_USE=true
        echo "⚠️  Port $NGINX_PORT is already in use:"
        ss -tulpn | grep ":$NGINX_PORT " || true
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":$NGINX_PORT "; then
        PORT_IN_USE=true
        echo "⚠️  Port $NGINX_PORT is already in use:"
        netstat -tulpn | grep ":$NGINX_PORT " || true
    fi
fi

if [ "$PORT_IN_USE" = true ]; then
    echo ""
    echo "❌ Port $NGINX_PORT is already in use. Please choose a different port."
    echo "   Usage: sudo ./setup_https.sh $DOMAIN [email] [port]"
    echo ""
    exit 1
fi

# Note: Certbot will temporarily need port 80 for validation
echo "ℹ️  Note: Certbot will temporarily use port 80 for SSL validation"
echo "   (This is required by Let's Encrypt)"

# Start or reload nginx
if systemctl is-active --quiet nginx; then
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "🚀 Starting nginx..."
    if systemctl start nginx; then
        systemctl enable nginx
        echo "✅ Nginx started and enabled"
    else
        echo "❌ Failed to start nginx"
        echo ""
        echo "Checking nginx status..."
        systemctl status nginx --no-pager -l || true
        echo ""
        echo "Please check the error above and fix it before continuing."
        exit 1
    fi
fi
echo ""

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
echo "   This may take a few moments..."
echo "   Note: Certbot will temporarily bind to port 80 for validation"
echo ""

# Temporarily stop Docker if it's using port 80
DOCKER_STOPPED=false
if command -v docker &> /dev/null && lsof -i :80 2>/dev/null | grep -q docker; then
    echo "🛑 Temporarily stopping Docker to free port 80 for certbot..."
    systemctl stop docker 2>/dev/null || service docker stop 2>/dev/null || true
    DOCKER_STOPPED=true
    sleep 2
fi

# Update nginx config to listen on port 80 temporarily for certbot
sed -i "s/listen $NGINX_PORT;/listen 80;\n    # listen $NGINX_PORT;/" "$NGINX_CONFIG"
sed -i "s/listen \[::\]:$NGINX_PORT;/listen [::]:80;\n    # listen [::]:$NGINX_PORT;/" "$NGINX_CONFIG"
systemctl reload nginx || systemctl start nginx

certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

# After certbot, update config back to use the custom port
# Certbot will have added SSL, so we need to update the HTTPS server block too
sed -i "s/listen 443 ssl http2;/listen 443 ssl http2;\n    listen $NGINX_PORT ssl http2;/" "$NGINX_CONFIG" 2>/dev/null || true

# Restart Docker if we stopped it
if [ "$DOCKER_STOPPED" = true ]; then
    echo "🔄 Restarting Docker..."
    systemctl start docker 2>/dev/null || service docker start 2>/dev/null || true
fi

systemctl reload nginx

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate obtained successfully!"
    echo ""
    
    # Test auto-renewal
    echo "🔄 Testing certificate renewal..."
    certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        echo "✅ Auto-renewal test passed"
    else
        echo "⚠️  Auto-renewal test failed (check logs)"
    fi
    
    echo ""
    echo "🎉 HTTPS setup complete!"
    echo ""
    echo "📋 Your site is now available at:"
    echo "   https://$DOMAIN:$NGINX_PORT"
    echo ""
    echo "📝 Important notes:"
    echo "   1. Certificates auto-renew every 90 days via certbot"
    echo "   2. Check renewal status: sudo certbot certificates"
    echo "   3. Manual renewal: sudo certbot renew"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - Check nginx: sudo systemctl status nginx"
    echo "   - Check logs: sudo tail -f /var/log/nginx/error.log"
    echo "   - Test SSL: sudo certbot certificates"
    echo ""
else
    echo ""
    echo "❌ Failed to obtain SSL certificate"
    echo ""
    echo "Common issues:"
    echo "   1. DNS not pointing to this server"
    echo "   2. Port 80 not accessible from internet"
    echo "   3. Firewall blocking Let's Encrypt validation"
    echo ""
    echo "Fix DNS first, then run: sudo certbot --nginx -d $DOMAIN"
    exit 1
fi
