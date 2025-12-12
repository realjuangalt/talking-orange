#!/bin/bash

# Talking Orange AR - Unified Start Script
# Handles both localhost development and server production modes
# Usage: ./start.sh [--mode localhost|server] [--device cpu|gpu|auto] [--model small|medium] [--domain DOMAIN] [--skip-https]

cd "$(dirname "$0")"
source venv/bin/activate

# Default values
MODE=""
WHISPER_DEVICE=""
WHISPER_MODEL="small"
DOMAIN=""
SKIP_HTTPS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --device)
            WHISPER_DEVICE="$2"
            shift 2
            ;;
        --model)
            WHISPER_MODEL="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --skip-https)
            SKIP_HTTPS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode localhost|server    Run mode (default: prompt if not specified)"
            echo "  --device cpu|gpu|auto     Device mode (localhost default: auto, server default: cpu)"
            echo "  --model small|medium       Whisper model size (default: small)"
            echo "  --domain DOMAIN           Domain name for HTTPS setup (server mode)"
            echo "  --skip-https               Skip HTTPS setup check (server mode)"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Interactive mode selection"
            echo "  $0 --mode localhost                  # Localhost with auto GPU detection"
            echo "  $0 --mode server --domain example.com # Server mode with HTTPS setup"
            echo "  $0 --mode localhost --device gpu      # Force GPU mode"
            echo "  $0 --mode server --skip-https         # Server mode without HTTPS check"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to check if HTTPS is already configured
check_https_setup() {
    local domain=$1
    if [ -z "$domain" ]; then
        return 1
    fi
    
    # Check if nginx config exists and has SSL
    if [ -f "/etc/nginx/sites-available/talking-orange" ]; then
        if grep -q "ssl_certificate" "/etc/nginx/sites-available/talking-orange" 2>/dev/null; then
            # Check if certificate files exist
            if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
                return 0
            fi
        fi
    fi
    return 1
}

# Function to attempt HTTPS setup (graceful failure)
attempt_https_setup() {
    local domain=$1
    local email=${2:-"admin@${domain}"}
    local nginx_port=${3:-"80"}
    
    echo ""
    echo "🔒 Attempting to set up HTTPS..."
    echo "=================================="
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo "⚠️  HTTPS setup requires root privileges"
        echo "   Run with sudo to set up HTTPS, or use --skip-https to continue without HTTPS"
        return 1
    fi
    
    # Check if domain is provided
    if [ -z "$domain" ]; then
        echo "⚠️  No domain provided for HTTPS setup"
        echo "   Use --domain your-domain.com to set up HTTPS"
        return 1
    fi
    
    # Convert domain to lowercase
    domain=$(echo "$domain" | tr '[:upper:]' '[:lower:]')
    
    # Detect project root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$SCRIPT_DIR"
    
    echo "📋 Configuration:"
    echo "   Domain: $domain"
    echo "   Email: $email"
    echo "   Project Root: $PROJECT_ROOT"
    echo ""
    
    # Install certbot if not already installed
    if ! command -v certbot &> /dev/null; then
        echo "📦 Installing certbot..."
        if apt update && apt install -y certbot python3-certbot-nginx 2>/dev/null; then
            echo "✅ Certbot installed"
        else
            echo "⚠️  Failed to install certbot (continuing without HTTPS)"
            return 1
        fi
    else
        echo "✅ Certbot already installed"
    fi
    
    # Create nginx configuration
    echo "📝 Creating nginx configuration..."
    NGINX_CONFIG="/etc/nginx/sites-available/talking-orange"
    
    # Check if port 80 is available
    PORT_80_AVAILABLE=true
    if command -v lsof &> /dev/null; then
        if lsof -i :80 &> /dev/null; then
            PORT_80_AVAILABLE=false
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":80 "; then
            PORT_80_AVAILABLE=false
        fi
    fi
    
    if [ "$PORT_80_AVAILABLE" = false ]; then
        echo "⚠️  Port 80 is in use - cannot set up HTTPS via Let's Encrypt"
        echo "   Continuing without HTTPS setup"
        return 1
    fi
    
    # Create HTTP-only config first
    cat > "$NGINX_CONFIG" << EOF
# Talking Orange - HTTP server
server {
    listen $nginx_port;
    listen [::]:$nginx_port;
    server_name $domain;

    client_max_body_size 10M;

    location / {
        root $PROJECT_ROOT/frontend;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

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
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location ~ ^/(backend|data)/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable the site
    if [ ! -L "/etc/nginx/sites-enabled/talking-orange" ]; then
        ln -s "$NGINX_CONFIG" /etc/nginx/sites-enabled/talking-orange 2>/dev/null || true
    fi
    
    # Stop nginx temporarily for certbot
    systemctl stop nginx 2>/dev/null || true
    sleep 2
    
    # Test nginx configuration
    if ! nginx -t 2>/dev/null && ! /usr/sbin/nginx -t 2>/dev/null; then
        echo "⚠️  Nginx configuration test failed (continuing without HTTPS)"
        systemctl start nginx 2>/dev/null || true
        return 1
    fi
    
    # Get SSL certificate
    echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
    if certbot certonly --standalone -d "$domain" --non-interactive --agree-tos --email "$email" 2>/dev/null; then
        # Update nginx config with SSL
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            cat > "$NGINX_CONFIG" << EOF
# Talking Orange - HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $domain;
    return 301 https://\$server_name\$request_uri;
}

# Talking Orange - HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    listen $nginx_port ssl http2;
    listen [::]:$nginx_port ssl http2;
    server_name $domain;

    ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 10M;

    location / {
        root $PROJECT_ROOT/frontend;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

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
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location ~ ^/(backend|data)/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
            
            if nginx -t 2>/dev/null || /usr/sbin/nginx -t 2>/dev/null; then
                systemctl start nginx 2>/dev/null || true
                echo "✅ HTTPS set up successfully!"
                echo "   Your site is available at: https://$domain"
                return 0
            fi
        fi
    fi
    
    echo "⚠️  HTTPS setup failed (continuing without HTTPS)"
    echo "   Common issues: DNS not pointing to server, port 80 blocked, or firewall issues"
    systemctl start nginx 2>/dev/null || true
    return 1
}

# Interactive mode selection if not provided
if [ -z "$MODE" ]; then
    echo "🍊 Talking Orange AR - Start Script"
    echo "===================================="
    echo ""
    echo "Select run mode:"
    echo "  1) Localhost (development - auto GPU, debug mode)"
    echo "  2) Server (production - CPU default, HTTPS check)"
    echo ""
    read -p "Enter choice [1-2]: " choice
    
    case $choice in
        1)
            MODE="localhost"
            ;;
        2)
            MODE="server"
            ;;
        *)
            echo "Invalid choice. Defaulting to localhost mode."
            MODE="localhost"
            ;;
    esac
    echo ""
fi

# Set defaults based on mode
if [ -z "$WHISPER_DEVICE" ]; then
    if [ "$MODE" = "localhost" ]; then
        WHISPER_DEVICE="auto"
    else
        WHISPER_DEVICE="cpu"
    fi
fi

# Validate model
if [[ "$WHISPER_MODEL" != "small" && "$WHISPER_MODEL" != "medium" ]]; then
    echo "Error: Model must be 'small' or 'medium'"
    exit 1
fi

# Validate device
if [[ "$WHISPER_DEVICE" != "auto" && "$WHISPER_DEVICE" != "cpu" && "$WHISPER_DEVICE" != "gpu" ]]; then
    echo "Error: Device must be 'auto', 'cpu', or 'gpu'"
    exit 1
fi

# Server mode: Check HTTPS setup
if [ "$MODE" = "server" ] && [ "$SKIP_HTTPS" = false ]; then
    # If domain not provided, try to detect from nginx config
    if [ -z "$DOMAIN" ]; then
        if [ -f "/etc/nginx/sites-available/talking-orange" ]; then
            DOMAIN=$(grep -oP 'server_name\s+\K[^;]+' /etc/nginx/sites-available/talking-orange 2>/dev/null | head -1 | tr -d ' ' || echo "")
        fi
    fi
    
    if [ -n "$DOMAIN" ]; then
        if check_https_setup "$DOMAIN"; then
            echo "✅ HTTPS is already configured for $DOMAIN"
        else
            echo "⚠️  HTTPS is not configured for $DOMAIN"
            read -p "Attempt to set up HTTPS now? (y/n) [n]: " setup_https
            if [[ "$setup_https" =~ ^[Yy]$ ]]; then
                attempt_https_setup "$DOMAIN" || echo "   Continuing without HTTPS..."
            else
                echo "   Continuing without HTTPS..."
            fi
        fi
    else
        echo "⚠️  No domain detected - skipping HTTPS check"
        echo "   Use --domain your-domain.com to set up HTTPS"
    fi
    echo ""
fi

# Set environment variables
export WHISPER_MODEL_NAME="$WHISPER_MODEL"

# Configure device settings
if [[ "$WHISPER_DEVICE" == "cpu" ]]; then
    export WHISPER_FORCE_CPU="true"
    echo "🔧 Forcing CPU mode"
elif [[ "$WHISPER_DEVICE" == "gpu" ]]; then
    export WHISPER_FORCE_CPU="false"
    echo "🔧 GPU mode requested - will use GPU if available"
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    echo "💾 Set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"
    # Check CUDA availability
    python3 -c "import torch; \
        if torch.cuda.is_available(): \
            print('✅ CUDA available'); \
            for i in range(torch.cuda.device_count()): \
                props = torch.cuda.get_device_properties(i); \
                total_mem = props.total_memory / (1024**3); \
                reserved = torch.cuda.memory_reserved(i) / (1024**3); \
                free = total_mem - reserved; \
                print(f'   GPU {i} ({props.name}): {total_mem:.2f} GB total, {free:.2f} GB free'); \
        else: \
            print('⚠️  CUDA not available')" 2>/dev/null || echo "⚠️  Could not check CUDA availability"
else
    export WHISPER_FORCE_CPU="false"
    echo "🔧 Auto-detecting device (GPU if available, else CPU)"
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    # Check CUDA availability
    python3 -c "import torch; \
        if torch.cuda.is_available(): \
            print('✅ CUDA available'); \
            for i in range(torch.cuda.device_count()): \
                props = torch.cuda.get_device_properties(i); \
                total_mem = props.total_memory / (1024**3); \
                reserved = torch.cuda.memory_reserved(i) / (1024**3); \
                free = total_mem - reserved; \
                print(f'   GPU {i} ({props.name}): {total_mem:.2f} GB total, {free:.2f} GB free'); \
        else: \
            print('⚠️  CUDA not available')" 2>/dev/null || echo "⚠️  Could not check CUDA availability"
fi

# Set DEBUG mode for localhost
if [ "$MODE" = "localhost" ]; then
    export DEBUG=true
    echo "🐛 Debug mode enabled (Flask debug mode)"
fi

echo "🔧 Whisper model: $WHISPER_MODEL"
echo "🚀 Starting backend server..."
echo ""

cd backend
python3 app.py
