#!/bin/bash
# ============================================================================
#  Spancle - Update Script
#  Run this after: git pull
# ============================================================================
#
#  Usage:
#    cd /var/www/spancle/bookingapp
#    git pull https://github.com/netedge/bookingapp.git
#    sudo bash update_spancle.sh
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

# Project root is where this script lives
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

log "Project directory: $PROJECT_DIR"

if [ ! -f "$BACKEND_DIR/server.py" ]; then
    err "server.py not found at $BACKEND_DIR/server.py"
    exit 1
fi

# Step 1: Backend dependencies
log "Step 1/5: Updating backend dependencies..."
cd "$BACKEND_DIR"
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt --quiet 2>&1 | tail -3
    deactivate
    log "Backend dependencies updated (venv)"
else
    log "No venv found. Installing globally..."
    pip3 install -r requirements.txt --quiet 2>&1 | tail -3
    log "Backend dependencies updated (global)"
fi

# Step 2: Frontend dependencies
log "Step 2/5: Updating frontend dependencies..."
cd "$FRONTEND_DIR"
yarn install --frozen-lockfile 2>/dev/null || yarn install
log "Frontend dependencies updated"

# Step 3: Rebuild frontend
log "Step 3/5: Rebuilding frontend (this takes 1-2 minutes)..."
yarn build
log "Frontend rebuilt successfully"

# Step 4: Verify build contains new code
if grep -rq "forgot-password" "$FRONTEND_DIR/build/" 2>/dev/null; then
    log "Build verification: Forgot Password link found in build output"
else
    warn "Build verification: 'forgot-password' NOT found in build. Something may be wrong."
fi

# Step 5: Restart services
log "Step 5/5: Restarting services..."

if systemctl list-units --type=service | grep -q spancle-backend; then
    sudo systemctl restart spancle-backend
    sleep 2
    if systemctl is-active --quiet spancle-backend; then
        log "Backend restarted successfully"
    else
        err "Backend failed to start. Check: sudo journalctl -u spancle-backend -n 20"
    fi
else
    warn "spancle-backend systemd service not found."
    warn "If you use a different service name, restart it manually."
fi

if systemctl list-units --type=service | grep -q spancle-frontend; then
    sudo systemctl restart spancle-frontend
    sleep 2
    if systemctl is-active --quiet spancle-frontend; then
        log "Frontend restarted successfully"
    else
        err "Frontend failed to start. Check: sudo journalctl -u spancle-frontend -n 20"
    fi
else
    warn "spancle-frontend systemd service not found."
    warn "If you use a different service name, restart it manually."
fi

# Restart nginx to clear any caches
if systemctl is-active --quiet nginx; then
    sudo systemctl restart nginx
    log "Nginx restarted"
fi

echo ""
log "====================================="
log "  Update complete!"
log "====================================="
log ""
log "If pages still look old, try:"
log "  1. Hard refresh in browser: Ctrl+Shift+R"
log "  2. Check service logs: sudo journalctl -u spancle-frontend -n 20"
log "  3. Check build output: ls -la $FRONTEND_DIR/build/static/js/"
echo ""
