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
    echo "         sudo ./setup_https.sh AR.juangalt.com juan@juangalt.com 9090"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"juan@juangalt.com"}
NGINX_PORT=${3:-"80"}

# Convert domain to lowercase (DNS is case-insensitive, Let's Encrypt uses lowercase)
DOMAIN=$(echo "$DOMAIN" | tr '[:upper:]' '[:lower:]')

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

# Stop nginx FIRST before any port checks or config changes
echo "🛑 Stopping nginx..."
systemctl stop nginx 2>/dev/null || true
sleep 2

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

# Check if the nginx port is available (after stopping nginx)
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
    echo "❌ Port $NGINX_PORT is still in use. Please choose a different port."
    echo "   Usage: sudo ./setup_https.sh $DOMAIN [email] [port]"
    echo ""
    exit 1
fi

# Note: Certbot will temporarily need port 80 for validation
echo "ℹ️  Note: Certbot will temporarily use port 80 for SSL validation"
echo "   (This is required by Let's Encrypt)"

# Check if port 80 is available for HTTP validation
PORT_80_AVAILABLE=true
PORT_80_PROCESS=""
if command -v lsof &> /dev/null; then
    PORT_80_PROCESS=$(lsof -i :80 2>/dev/null | tail -n +2 | head -1 || true)
    if [ -n "$PORT_80_PROCESS" ]; then
        PORT_80_AVAILABLE=false
    fi
fi

if [ "$PORT_80_AVAILABLE" = false ]; then
    echo "⚠️  Port 80 is still in use by another service:"
    echo "$PORT_80_PROCESS"
    echo ""
    echo "❌ Cannot use HTTP validation (port 80 required)"
    echo ""
    echo "Please stop the service using port 80, then run this script again."
    echo ""
    exit 1
fi

# Port 80 is available, proceed with HTTP validation
echo "✅ Port 80 is available for Let's Encrypt validation"
echo "   Using HTTP validation method..."
echo ""

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
echo ""

# Use standalone mode (certbot runs its own server on port 80)
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"

# Now manually configure nginx with SSL
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    # Update nginx config to use SSL certificates
    cat > "$NGINX_CONFIG" << EOF
# Talking Orange - HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# Talking Orange - HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    listen $NGINX_PORT ssl http2;
    listen [::]:$NGINX_PORT ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration (use certbot's if available, otherwise use basic settings)
    if [ -f "/etc/letsencrypt/options-ssl-nginx.conf" ]; then
        include /etc/letsencrypt/options-ssl-nginx.conf;
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    else
        # Basic SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
    fi

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

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

    # Test and reload nginx
    if command -v nginx &> /dev/null; then
        nginx -t
    else
        /usr/sbin/nginx -t
    fi
    
    if [ $? -eq 0 ]; then
        systemctl start nginx
        echo "✅ Nginx configured with SSL and started"
    else
        echo "❌ Nginx configuration test failed!"
        exit 1
    fi
else
    echo "❌ SSL certificate files not found!"
    exit 1
fi

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
