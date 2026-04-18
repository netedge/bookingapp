#!/bin/bash
# ============================================================================
#  Spancle - Multi-Tenant SaaS Venue Booking Platform
#  Installation Script for Ubuntu 24.04.4 LTS
# ============================================================================
#
#  Usage:
#    chmod +x install_spancle.sh
#    sudo ./install_spancle.sh
#
#  What this script does:
#    1. Installs system dependencies (Python 3.11, Node.js 20, MongoDB 7, Nginx)
#    2. Sets up the backend (Python venv, pip install, environment config)
#    3. Sets up the frontend (yarn install, production build)
#    4. Configures Nginx reverse proxy
#    5. Creates systemd services for auto-start
#    6. Optional: SSL via Let's Encrypt (Certbot)
#
# ============================================================================

set -e

# ==================== COLORS ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log()    { echo -e "${GREEN}[SPANCLE]${NC} $1"; }
warn()   { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error()  { echo -e "${RED}[ERROR]${NC} $1"; }
header() { echo -e "\n${CYAN}========================================${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}========================================${NC}\n"; }

# ==================== PRE-FLIGHT CHECKS ====================
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo ./install_spancle.sh"
    exit 1
fi

if ! grep -q "24.04" /etc/os-release 2>/dev/null; then
    warn "This script is designed for Ubuntu 24.04. Your OS may differ."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# ==================== CONFIGURATION ====================
header "Spancle Installation Configuration"

# Defaults
INSTALL_DIR="/opt/spancle"
DOMAIN=""
ADMIN_EMAIL="admin@spancle.com"
ADMIN_PASSWORD="admin123"
MONGO_URL="mongodb://localhost:27017"
DB_NAME="spancle_db"
JWT_SECRET=$(openssl rand -hex 32)
BACKEND_PORT=8001
FRONTEND_PORT=3000
SETUP_SSL="n"
NODE_VERSION="20"

echo -e "${BLUE}Configure your Spancle installation:${NC}"
echo ""

read -p "Installation directory [$INSTALL_DIR]: " input
INSTALL_DIR="${input:-$INSTALL_DIR}"

read -p "Domain name (e.g., spancle.com or leave blank for IP-based): " DOMAIN

read -p "Admin email [$ADMIN_EMAIL]: " input
ADMIN_EMAIL="${input:-$ADMIN_EMAIL}"

read -p "Admin password [$ADMIN_PASSWORD]: " input
ADMIN_PASSWORD="${input:-$ADMIN_PASSWORD}"

read -p "MongoDB URL [$MONGO_URL]: " input
MONGO_URL="${input:-$MONGO_URL}"

read -p "Database name [$DB_NAME]: " input
DB_NAME="${input:-$DB_NAME}"

echo ""
echo -e "${BLUE}Payment Gateway Keys (press Enter to skip/use demo):${NC}"

read -p "Stripe API Key [sk_test_spancle_demo]: " STRIPE_KEY
STRIPE_KEY="${STRIPE_KEY:-sk_test_spancle_demo}"

read -p "Razorpay Key ID [rzp_test_demo]: " RAZORPAY_KEY_ID
RAZORPAY_KEY_ID="${RAZORPAY_KEY_ID:-rzp_test_demo}"

read -p "Razorpay Key Secret [razorpay_secret_demo]: " RAZORPAY_KEY_SECRET
RAZORPAY_KEY_SECRET="${RAZORPAY_KEY_SECRET:-razorpay_secret_demo}"

read -p "PayPal Client ID [paypal_client_id_demo]: " PAYPAL_CLIENT_ID
PAYPAL_CLIENT_ID="${PAYPAL_CLIENT_ID:-paypal_client_id_demo}"

read -p "PayPal Secret [paypal_secret_demo]: " PAYPAL_SECRET
PAYPAL_SECRET="${PAYPAL_SECRET:-paypal_secret_demo}"

read -p "PayPal Mode (sandbox/live) [sandbox]: " PAYPAL_MODE
PAYPAL_MODE="${PAYPAL_MODE:-sandbox}"

read -p "Skrill Merchant Email [merchant@example.com]: " SKRILL_EMAIL
SKRILL_EMAIL="${SKRILL_EMAIL:-merchant@example.com}"

read -p "Skrill API Password [skrill_api_password]: " SKRILL_PASS
SKRILL_PASS="${SKRILL_PASS:-skrill_api_password}"

read -p "Skrill Secret Word [skrill_secret_word]: " SKRILL_SECRET
SKRILL_SECRET="${SKRILL_SECRET:-skrill_secret_word}"

echo ""
echo -e "${BLUE}Email Configuration:${NC}"

read -p "Resend API Key [re_demo_key]: " RESEND_KEY
RESEND_KEY="${RESEND_KEY:-re_demo_key}"

read -p "Sender Email [onboarding@resend.dev]: " SENDER_EMAIL
SENDER_EMAIL="${SENDER_EMAIL:-onboarding@resend.dev}"

if [ -n "$DOMAIN" ]; then
    read -p "Setup SSL with Let's Encrypt? (y/n) [n]: " SETUP_SSL
    SETUP_SSL="${SETUP_SSL:-n}"
fi

APP_DOMAIN="${DOMAIN:-localhost}"

echo ""
log "Configuration complete. Starting installation..."
echo ""

# ==================== STEP 1: SYSTEM DEPENDENCIES ====================
header "Step 1/8: Installing System Dependencies"

apt-get update -y
apt-get install -y \
    software-properties-common \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    gnupg \
    lsb-release \
    ca-certificates \
    apt-transport-https

log "System packages installed"

# ==================== STEP 2: PYTHON 3.11 ====================
header "Step 2/8: Setting Up Python 3.11"

if python3.11 --version &>/dev/null; then
    log "Python 3.11 already installed: $(python3.11 --version)"
else
    add-apt-repository ppa:deadsnakes/ppa -y
    apt-get update -y
    apt-get install -y python3.11 python3.11-venv python3.11-dev
    log "Python 3.11 installed: $(python3.11 --version)"
fi

# ==================== STEP 3: NODE.JS 20 & YARN ====================
header "Step 3/8: Setting Up Node.js ${NODE_VERSION} & Yarn"

if node --version &>/dev/null; then
    log "Node.js already installed: $(node --version)"
else
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y nodejs
    log "Node.js installed: $(node --version)"
fi

if ! yarn --version &>/dev/null; then
    npm install -g yarn
fi
log "Yarn installed: $(yarn --version)"

# ==================== STEP 4: MONGODB 7 ====================
header "Step 4/8: Setting Up MongoDB 7"

if mongosh --version &>/dev/null || mongod --version &>/dev/null; then
    log "MongoDB already installed"
else
    # MongoDB 8.0 is required for Ubuntu 24.04 (noble) — 7.0 has no noble packages
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
        gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | \
        tee /etc/apt/sources.list.d/mongodb-org-8.0.list

    apt-get update -y
    apt-get install -y mongodb-org
    log "MongoDB 8.0 installed"
fi

systemctl enable mongod
systemctl start mongod
sleep 2

if systemctl is-active --quiet mongod; then
    log "MongoDB is running"
else
    error "MongoDB failed to start. Check: journalctl -u mongod"
    exit 1
fi

# ==================== STEP 5: NGINX ====================
header "Step 5/8: Setting Up Nginx"

apt-get install -y nginx
systemctl enable nginx
log "Nginx installed"

# ==================== STEP 6: APPLICATION SETUP ====================
header "Step 6/8: Setting Up Spancle Application"

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy application files (assumes script is run from the project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
    if [ "$(realpath "$SCRIPT_DIR")" = "$(realpath "$INSTALL_DIR")" ]; then
        log "Project already at install directory. Skipping copy."
    else
        log "Copying application files from $SCRIPT_DIR..."
        cp -r "$SCRIPT_DIR/backend" "$INSTALL_DIR/"
        cp -r "$SCRIPT_DIR/frontend" "$INSTALL_DIR/"
    fi
else
    error "Cannot find backend/ and frontend/ directories."
    error "Run this script from the Spancle project root directory."
    exit 1
fi

# Set PROJECT_DIR to where backend/ and frontend/ actually are
PROJECT_DIR="$INSTALL_DIR"
if [ ! -d "$PROJECT_DIR/backend" ] && [ -d "$SCRIPT_DIR/backend" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
fi

# --- BACKEND SETUP ---
log "Setting up backend..."

cd "$PROJECT_DIR/backend"

python3.11 -m venv venv
source venv/bin/activate

# Determine protocol
if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
    PROTOCOL="https"
else
    PROTOCOL="http"
fi

if [ -n "$DOMAIN" ]; then
    APP_URL="${PROTOCOL}://${DOMAIN}"
else
    APP_URL="http://$(hostname -I | awk '{print $1}')"
fi

# Write backend .env
cat > "$PROJECT_DIR/backend/.env" << ENVEOF
MONGO_URL="${MONGO_URL}"
DB_NAME="${DB_NAME}"
CORS_ORIGINS="${APP_URL},http://${APP_DOMAIN},https://${APP_DOMAIN},http://www.${APP_DOMAIN},https://www.${APP_DOMAIN}"
JWT_SECRET="${JWT_SECRET}"
ADMIN_EMAIL="${ADMIN_EMAIL}"
ADMIN_PASSWORD="${ADMIN_PASSWORD}"
STRIPE_API_KEY="${STRIPE_KEY}"
RAZORPAY_KEY_ID="${RAZORPAY_KEY_ID}"
RAZORPAY_KEY_SECRET="${RAZORPAY_KEY_SECRET}"
PAYPAL_CLIENT_ID="${PAYPAL_CLIENT_ID}"
PAYPAL_SECRET="${PAYPAL_SECRET}"
PAYPAL_MODE="${PAYPAL_MODE}"
SKRILL_MERCHANT_EMAIL="${SKRILL_EMAIL}"
SKRILL_API_PASSWORD="${SKRILL_PASS}"
SKRILL_SECRET_WORD="${SKRILL_SECRET}"
RESEND_API_KEY="${RESEND_KEY}"
SENDER_EMAIL="${SENDER_EMAIL}"
APP_DOMAIN="${APP_DOMAIN}"
ENVEOF

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

deactivate
log "Backend setup complete"

# --- FRONTEND SETUP ---
log "Setting up frontend..."

cd "$PROJECT_DIR/frontend"

# Write frontend .env
cat > "$PROJECT_DIR/frontend/.env" << ENVEOF
REACT_APP_BACKEND_URL=${APP_URL}
ENVEOF

yarn install --frozen-lockfile 2>/dev/null || yarn install
yarn build

log "Frontend build complete"

# ==================== STEP 7: SYSTEMD SERVICES ====================
header "Step 7/8: Creating System Services"

# Create a system user for spancle
if ! id "spancle" &>/dev/null; then
    useradd -r -s /bin/false spancle
fi

chown -R spancle:spancle "$INSTALL_DIR"

# Backend service
cat > /etc/systemd/system/spancle-backend.service << SVCEOF
[Unit]
Description=Spancle Backend API
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=spancle
Group=spancle
WorkingDirectory=${PROJECT_DIR}/backend
Environment=PATH=${PROJECT_DIR}/backend/venv/bin:/usr/bin:/bin
ExecStart=${PROJECT_DIR}/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port ${BACKEND_PORT} --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

# Frontend serve (using serve for production build)
cd "$PROJECT_DIR/frontend"
source "$PROJECT_DIR/backend/venv/bin/activate"
npm install -g serve 2>/dev/null || true
deactivate

cat > /etc/systemd/system/spancle-frontend.service << SVCEOF
[Unit]
Description=Spancle Frontend
After=network.target

[Service]
Type=simple
User=spancle
Group=spancle
WorkingDirectory=${PROJECT_DIR}/frontend
ExecStart=/usr/bin/npx serve -s build -l ${FRONTEND_PORT}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable spancle-backend
systemctl enable spancle-frontend
systemctl start spancle-backend
systemctl start spancle-frontend

sleep 3

if systemctl is-active --quiet spancle-backend; then
    log "Backend service is running on port ${BACKEND_PORT}"
else
    warn "Backend service may need attention. Check: journalctl -u spancle-backend -f"
fi

if systemctl is-active --quiet spancle-frontend; then
    log "Frontend service is running on port ${FRONTEND_PORT}"
else
    warn "Frontend service may need attention. Check: journalctl -u spancle-frontend -f"
fi

# ==================== STEP 8: NGINX CONFIGURATION ====================
header "Step 8/8: Configuring Nginx Reverse Proxy"

SERVER_NAME="${DOMAIN:-_}"

cat > /etc/nginx/sites-available/spancle << NGINXEOF
server {
    listen 80;
    server_name ${SERVER_NAME};

    client_max_body_size 50M;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 90s;
        proxy_connect_timeout 90s;
    }

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
NGINXEOF

# Enable site and remove default
ln -sf /etc/nginx/sites-available/spancle /etc/nginx/sites-enabled/spancle
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx
log "Nginx configured and running"

# ==================== OPTIONAL: SSL WITH LET'S ENCRYPT ====================
if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
    header "Optional: Setting Up SSL (Let's Encrypt)"

    if [ -z "$DOMAIN" ]; then
        warn "SSL requires a domain name. Skipping."
    else
        apt-get install -y certbot python3-certbot-nginx

        log "Requesting SSL certificate for ${DOMAIN}..."
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL" --redirect

        # Auto-renewal
        systemctl enable certbot.timer
        systemctl start certbot.timer

        log "SSL certificate installed and auto-renewal enabled"
    fi
fi

# ==================== DONE ====================
header "Installation Complete!"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Spancle has been installed successfully!  ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  ${CYAN}Installation directory:${NC} ${INSTALL_DIR}"
echo -e "  ${CYAN}Backend service:${NC}       spancle-backend (port ${BACKEND_PORT})"
echo -e "  ${CYAN}Frontend service:${NC}      spancle-frontend (port ${FRONTEND_PORT})"
echo -e "  ${CYAN}Database:${NC}              ${DB_NAME} @ ${MONGO_URL}"
echo ""

if [ -n "$DOMAIN" ]; then
    if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
        echo -e "  ${CYAN}Application URL:${NC}       https://${DOMAIN}"
    else
        echo -e "  ${CYAN}Application URL:${NC}       http://${DOMAIN}"
    fi
else
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo -e "  ${CYAN}Application URL:${NC}       http://${SERVER_IP}"
fi

echo ""
echo -e "  ${CYAN}Admin Login:${NC}"
echo -e "    Email:    ${ADMIN_EMAIL}"
echo -e "    Password: ${ADMIN_PASSWORD}"
echo ""
echo -e "  ${YELLOW}Useful Commands:${NC}"
echo -e "    sudo systemctl status spancle-backend"
echo -e "    sudo systemctl status spancle-frontend"
echo -e "    sudo journalctl -u spancle-backend -f"
echo -e "    sudo journalctl -u spancle-frontend -f"
echo -e "    sudo systemctl restart spancle-backend"
echo -e "    sudo systemctl restart spancle-frontend"
echo ""

if [ "$STRIPE_KEY" = "sk_test_spancle_demo" ]; then
    warn "You are using demo payment keys. Update ${PROJECT_DIR}/backend/.env with real keys for production."
fi

log "Setup complete. Visit your application URL to get started!"
