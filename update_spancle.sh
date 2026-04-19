#!/bin/bash
# ============================================================================
#  Spancle - Update Script
#  Run this after: git pull https://github.com/netedge/bookingapp.git
# ============================================================================
#
#  Usage:
#    chmod +x update_spancle.sh
#    sudo ./update_spancle.sh
#
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[SPANCLE]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

# Auto-detect install directory
if [ -d "/opt/spancle" ]; then
    INSTALL_DIR="/opt/spancle"
elif [ -d "/var/www/spancle" ]; then
    INSTALL_DIR="/var/www/spancle"
else
    read -p "Enter Spancle installation directory: " INSTALL_DIR
fi

PROJECT_DIR="$INSTALL_DIR"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

if [ ! -f "$BACKEND_DIR/server.py" ]; then
    err "server.py not found in $BACKEND_DIR. Check your install directory."
    exit 1
fi

log "Updating Spancle at: $PROJECT_DIR"

# Step 1: Install any new backend dependencies
log "Step 1/4: Updating backend dependencies..."
cd "$BACKEND_DIR"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    deactivate
    log "Backend dependencies updated"
else
    warn "No venv found at $BACKEND_DIR/venv — skipping pip install"
    warn "If you use a virtual environment, activate it and run: pip install -r requirements.txt"
fi

# Step 2: Install any new frontend dependencies
log "Step 2/4: Updating frontend dependencies..."
cd "$FRONTEND_DIR"
yarn install --frozen-lockfile 2>/dev/null || yarn install
log "Frontend dependencies updated"

# Step 3: Rebuild the frontend (this is the critical step!)
log "Step 3/4: Rebuilding frontend production bundle..."
yarn build
log "Frontend rebuilt successfully"

# Step 4: Restart services
log "Step 4/4: Restarting services..."
if systemctl is-active --quiet spancle-backend; then
    systemctl restart spancle-backend
    log "Backend restarted"
else
    warn "spancle-backend service not found. Restart your backend manually."
fi

if systemctl is-active --quiet spancle-frontend; then
    systemctl restart spancle-frontend
    log "Frontend restarted"
else
    warn "spancle-frontend service not found. Restart your frontend manually."
fi

echo ""
log "Update complete! Changes should now be visible in the browser."
log "If you still don't see changes, clear your browser cache (Ctrl+Shift+R)."
echo ""
