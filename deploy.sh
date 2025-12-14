#!/bin/bash

# Pishgoo VPS Deployment Script for Ubuntu
# This script installs and sets up Pishgoo on an Ubuntu VPS

set -e

echo " Starting Pishgoo Deployment..."

# Update system
echo " Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
echo " Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl

# Create project directory (adjust path as needed)
PROJECT_DIR="/root/Pishgoo"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "� Creating project directory..."
    mkdir -p $PROJECT_DIR
fi

cd $PROJECT_DIR

# Create virtual environment
echo " Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo " Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo " Creating directories..."
mkdir -p logs
mkdir -p models
mkdir -p backtest_results

# Set permissions
echo " Setting permissions..."
chmod +x services/trader_service.py
chmod +x deploy.sh

# Install systemd service (optional)
echo "� Installing systemd service..."
if [ -f "services/pishgoo.service" ]; then
    sudo cp services/pishgoo.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo " Systemd service installed (enable with: sudo systemctl enable pishgoo.service)"
fi

echo " Deployment completed!"
echo ""
echo " Next steps:"
echo "1. Configure API keys in config/user_config.json"
echo "2. Run dashboard: streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0"
echo "3. Start trading service: sudo systemctl start pishgoo.service"
echo "4. Enable auto-start: sudo systemctl enable pishgoo.service"







