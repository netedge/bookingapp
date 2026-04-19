#!/bin/bash
# ============================================================================
#  Spancle - Fix Service Paths
#  Reconfigures systemd services to run from /var/www/spancle/bookingapp
#  and rebuilds the frontend.
#
#  Usage:
#    cd /var/www/spancle/bookingapp
#    sudo bash fix_services.sh
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[SPANCLE]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_DIR="/var/www/spancle/bookingapp"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_PORT=8001
FRONTEND_PORT=3000

if [ ! -f "$BACKEND_DIR/server.py" ]; then
    err "server.py not found at $BACKEND_DIR. Check your path."
    exit 1
fi

log "Fixing Spancle services to use: $PROJECT_DIR"

# ---- Step 1: Ensure venv exists ----
log "Step 1/6: Setting up backend virtual environment..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log "Created new venv"
fi
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
deactivate
log "Backend dependencies installed"

# ---- Step 2: Frontend dependencies ----
log "Step 2/6: Installing frontend dependencies..."
cd "$FRONTEND_DIR"
yarn install --frozen-lockfile 2>/dev/null || yarn install
log "Frontend dependencies installed"

# ---- Step 3: Build frontend ----
log "Step 3/6: Building frontend (1-2 minutes)..."
yarn build
log "Frontend built"

# ---- Step 4: Rewrite systemd services ----
log "Step 4/6: Updating systemd service files..."

# Backend service
cat > /etc/systemd/system/spancle-backend.service << SVCEOF
[Unit]
Description=Spancle Backend
After=network.target mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=${BACKEND_DIR}
ExecStart=${BACKEND_DIR}/venv/bin/uvicorn server:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

# Frontend service
cat > /etc/systemd/system/spancle-frontend.service << SVCEOF
[Unit]
Description=Spancle Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${FRONTEND_DIR}
ExecStart=/usr/bin/npx serve -s build -l ${FRONTEND_PORT}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

log "Service files updated"

# ---- Step 5: Reload and restart ----
log "Step 5/6: Restarting services..."
systemctl daemon-reload
systemctl enable spancle-backend spancle-frontend
systemctl restart spancle-backend
sleep 2
systemctl restart spancle-frontend
sleep 2

# ---- Step 6: Verify ----
log "Step 6/6: Verifying..."

if systemctl is-active --quiet spancle-backend; then
    log "Backend is running"
else
    err "Backend FAILED. Check: sudo journalctl -u spancle-backend -n 30"
fi

if systemctl is-active --quiet spancle-frontend; then
    log "Frontend is running"
else
    err "Frontend FAILED. Check: sudo journalctl -u spancle-frontend -n 30"
fi

# Restart nginx
if systemctl is-active --quiet nginx; then
    systemctl restart nginx
    log "Nginx restarted"
fi

# Verify build has new code
if grep -rq "forgot-password" "$FRONTEND_DIR/build/" 2>/dev/null; then
    log "Build verified: Forgot Password link is present"
else
    warn "Build may be outdated. 'forgot-password' not found in build."
fi

echo ""
log "====================================="
log "  Services now running from:"
log "  $PROJECT_DIR"
log "====================================="
echo ""
log "Future updates — just run:"
log "  cd $PROJECT_DIR"
log "  git pull https://github.com/netedge/bookingapp.git"
log "  sudo bash update_spancle.sh"
echo ""
