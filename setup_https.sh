#!/bin/bash

# Talking Orange - HTTPS Setup Script
# This script sets up free HTTPS using Let's Encrypt and nginx

set -e

echo "🔒 Setting up HTTPS for Talking Orange"
echo "========================================"
echo ""

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: sudo ./setup_https.sh your-domain.com [email] [test]"
    echo ""
    echo "Example: sudo ./setup_https.sh talking-orange.example.com"
    echo "Test mode: ./setup_https.sh example.com test@example.com test"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@${DOMAIN}"}
TEST_MODE=${3:-""}

# Check if running as root (skip in test mode)
if [ "$TEST_MODE" != "test" ] && [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Detect project root (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL (for Let's Encrypt notifications)"
echo "   Project Root: $PROJECT_ROOT"
if [ "$TEST_MODE" == "test" ]; then
    echo "   ⚠️  TEST MODE - No changes will be made"
fi
echo ""

# Install certbot if not already installed
if [ "$TEST_MODE" != "test" ]; then
    if ! command -v certbot &> /dev/null; then
        echo "📦 Installing certbot..."
        apt update
        apt install -y certbot python3-certbot-nginx
        echo "✅ Certbot installed"
    else
        echo "✅ Certbot already installed"
    fi
else
    echo "🧪 TEST MODE: Skipping certbot installation"
fi

# Create nginx configuration
echo "📝 Creating nginx configuration..."
NGINX_CONFIG="/etc/nginx/sites-available/talking-orange"

if [ "$TEST_MODE" == "test" ]; then
    echo "🧪 TEST MODE: Would create nginx config at: $NGINX_CONFIG"
    echo "🧪 TEST MODE: Config preview:"
    echo "---"
    cat << EOF
# Talking Orange - HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Redirect all HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# Talking Orange - HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration (will be added by certbot)
    # include /etc/letsencrypt/options-ssl-nginx.conf;
    # ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

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
    if [ "$TEST_MODE" != "test" ]; then
        cat > "$NGINX_CONFIG" << EOF
# Talking Orange - HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Redirect all HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# Talking Orange - HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration (will be added by certbot)
    # include /etc/letsencrypt/options-ssl-nginx.conf;
    # ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

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
    fi

if [ "$TEST_MODE" == "test" ]; then
    echo "---"
    echo "🧪 TEST MODE: Skipping actual file creation"
else
    echo "✅ Nginx configuration created at $NGINX_CONFIG"
fi
echo ""

# Enable the site
if [ "$TEST_MODE" != "test" ]; then
    if [ ! -L "/etc/nginx/sites-enabled/talking-orange" ]; then
        ln -s "$NGINX_CONFIG" /etc/nginx/sites-enabled/talking-orange
        echo "✅ Enabled nginx site"
    else
        echo "✅ Nginx site already enabled"
    fi

    # Test nginx configuration
    echo "🧪 Testing nginx configuration..."
    nginx -t
    if [ $? -ne 0 ]; then
        echo "❌ Nginx configuration test failed!"
        exit 1
    fi

    # Reload nginx
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "🧪 TEST MODE: Would enable site and reload nginx"
fi
echo ""

# Get SSL certificate
if [ "$TEST_MODE" != "test" ]; then
    echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
    echo "   This may take a few moments..."
    echo ""

    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

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
        echo "   https://$DOMAIN"
        echo ""
        echo "📝 Important notes:"
        echo "   1. Update your DNS A record to point $DOMAIN to this server's IP"
        echo "   2. Certificates auto-renew every 90 days via certbot"
        echo "   3. Check renewal status: sudo certbot certificates"
        echo "   4. Manual renewal: sudo certbot renew"
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
fi
else
    echo "🧪 TEST MODE: Would run certbot to obtain SSL certificate"
    echo "🧪 TEST MODE: Command would be: certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect"
    echo ""
    echo "✅ TEST MODE completed - No changes were made"
    echo ""
    echo "To actually run the setup, use:"
    echo "   sudo ./setup_https.sh $DOMAIN $EMAIL"
    exit 0
fi

