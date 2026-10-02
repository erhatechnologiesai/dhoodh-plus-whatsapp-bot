#!/bin/bash
# ==============================================================================
# Dhoodh Plus AI WhatsApp Bot - 1-Click Ubuntu/Debian Production Deployment Script
# (Native PM2 + Redis + Python + Node.js)
# ==============================================================================

set -e

echo "🚀 [1/6] Updating server packages and installing dependencies..."
sudo apt update -y && sudo apt upgrade -y
sudo apt install -y curl git build-essential python3 python3-pip python3-venv ffmpeg redis-server nginx ufw

# Ensure Redis is running
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo "📦 [2/6] Installing Node.js 20.x & PM2..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

echo "🐍 [3/6] Setting up Python FastAPI Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

echo "📱 [4/6] Setting up WhatsApp Baileys Gateway..."
cd whatsapp-gateway
npm install
cd ..

echo "💻 [5/6] Building Next.js Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "⚡ [6/6] Starting all services under PM2 24/7 supervision..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup

PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s https://ifconfig.me || echo "YOUR_SERVER_IP")

echo ""
echo "================================================================================"
echo "✅ DHOODH PLUS AI BOT DEPLOYED SUCCESSFULLY VIA PM2!"
echo "   - Frontend:         http://$PUBLIC_IP:3000"
echo "   - FastAPI Backend:  http://$PUBLIC_IP:8000"
echo "   - WhatsApp Gateway: http://$PUBLIC_IP:3001"
echo "   - Redis Server:     localhost:6379 (Active)"
echo ""
echo "   To view live logs:  pm2 logs"
echo "   To view status:     pm2 status"
echo "================================================================================"
