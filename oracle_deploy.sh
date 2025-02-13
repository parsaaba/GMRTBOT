#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required tools
sudo apt install -y python3-pip python3-venv git screen

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup systemd service
sudo cp gmrt-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gmrt-bot
sudo systemctl start gmrt-bot

# Show status
sudo systemctl status gmrt-bot
