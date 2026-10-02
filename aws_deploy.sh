#!/bin/bash
# ==============================================================================
# DHOODH PLUS AI WHATSAPP BOT - AWS EC2 1-CLICK DEPLOYMENT SCRIPT
# Target OS: Ubuntu 22.04 LTS / Ubuntu 24.04 LTS
# ==============================================================================

set -e

echo "================================================================================"
echo "🚀 Starting AWS EC2 Deployment for Dhoodh Plus AI WhatsApp Bot"
echo "================================================================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  Please run with sudo: sudo bash aws_deploy.sh"
  exit 1
fi

ACTUAL_USER="${SUDO_USER:-$USER}"

# ------------------------------------------------------------------------------
# 1. System Updates & Essential Utilities
# ------------------------------------------------------------------------------
echo "📦 [1/7] Updating Ubuntu packages and installing utilities..."
apt-get update -y
apt-get install -y curl wget git ufw htop ca-certificates gnupg lsb-release

# ------------------------------------------------------------------------------
# 2. Configure Swap Memory (Critical for t2.micro / t3.micro instances)
# ------------------------------------------------------------------------------
echo "🧠 [2/7] Checking system RAM and Swap..."
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM_MB" -lt 2500 ] && [ ! -f /swapfile ]; then
    echo "⚙️  Detected < 2.5GB RAM ($TOTAL_RAM_MB MB). Setting up 2GB Swap to prevent OOM build crashes..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "✅ 2GB Swap configured successfully."
else
    echo "ℹ️  RAM ($TOTAL_RAM_MB MB) or Swap already sufficient."
fi

# ------------------------------------------------------------------------------
# 3. Install Docker Engine & Docker Compose Plugin
# ------------------------------------------------------------------------------
echo "🐳 [3/7] Installing Docker and Docker Compose Plugin..."
if ! command -v docker &> /dev/null; then
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    usermod -aG docker "$ACTUAL_USER"
    echo "✅ Docker installed successfully."
else
    echo "ℹ️  Docker is already installed."
fi

# ------------------------------------------------------------------------------
# 4. Configure Firewall (UFW)
# ------------------------------------------------------------------------------
echo "🛡️  [4/7] Configuring UFW Firewall for AWS..."
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP / Nginx'
ufw allow 443/tcp comment 'HTTPS / SSL'
ufw --force enable

# ------------------------------------------------------------------------------
# 5. Environment Variables Check
# ------------------------------------------------------------------------------
echo "🔑 [5/7] Verifying .env configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "⚠️  No .env file found. Creating from .env.example..."
        cp .env.example .env
        echo "📝 Created .env template. Please edit .env with your real Supabase & OpenAI keys:"
        echo "    nano .env"
    else
        echo "⚠️  Please create a .env file before starting the stack."
    fi
else
    echo "✅ .env file exists."
fi

# ------------------------------------------------------------------------------
# 6. Build and Start All 5 Docker Containers
# ------------------------------------------------------------------------------
echo "🚀 [6/7] Building and starting Docker services..."
echo "   - redis:             Port 6379"
echo "   - backend:           Port 8000"
echo "   - whatsapp-gateway:  Port 3001"
echo "   - frontend:          Port 3000"
echo "   - nginx:             Port 80 / 443"

docker compose down --remove-orphans || true
docker compose build
docker compose up -d

# ------------------------------------------------------------------------------
# 7. Verification & Status Output
# ------------------------------------------------------------------------------
echo "⏳ [7/7] Waiting 10 seconds for containers to initialize..."
sleep 10

PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s https://ifconfig.me || echo "YOUR_SERVER_IP")

echo ""
echo "================================================================================"
echo "🎉 DHOODH PLUS AI WHATSAPP BOT IS LIVE ON AWS!"
echo "================================================================================"
echo "🌐 Admin Dashboard:     http://$PUBLIC_IP"
echo "🔌 Backend API:         http://$PUBLIC_IP/api"
echo "🩺 Health Check:        http://$PUBLIC_IP/api/health"
echo "📱 WhatsApp Gateway:    http://$PUBLIC_IP/gateway"
echo "📲 WhatsApp Pairing QR: http://$PUBLIC_IP/gateway/qr"
echo ""
echo "📊 Running Containers:"
docker compose ps
echo ""
echo "🛠️  Helpful AWS Management Commands:"
echo "   - Live Logs:         docker compose logs -f"
echo "   - Backend Logs:      docker compose logs -f backend"
echo "   - WhatsApp Logs:     docker compose logs -f whatsapp-gateway"
echo "   - Restart Stack:     docker compose restart"
echo "   - Stop Stack:        docker compose down"
echo "================================================================================"
