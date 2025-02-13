#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies
install_dependencies() {
    echo "Installing/Updating dependencies..."
    pip3 install -r requirements.txt
}

# Function to setup environment
setup_environment() {
    echo "Setting up environment..."
    if [ ! -f .env ]; then
        echo "Creating .env file..."
        cp .env.example .env
        echo "Please edit .env file with your API keys"
        exit 1
    fi
}

# Function to start the bot
start_bot() {
    echo "Starting GMRT Bot..."
    if command_exists screen; then
        screen -dmS gmrt_bot python3 whale_tracker.py
        echo "Bot started in screen session 'gmrt_bot'"
        echo "To attach to the session, use: screen -r gmrt_bot"
    else
        nohup python3 whale_tracker.py > bot.log 2>&1 &
        echo "Bot started in background. Check bot.log for output"
    fi
}

# Function to stop the bot
stop_bot() {
    echo "Stopping GMRT Bot..."
    pkill -f "python3 whale_tracker.py"
}

# Function to check bot status
check_status() {
    if pgrep -f "python3 whale_tracker.py" > /dev/null; then
        echo "Bot is running"
    else
        echo "Bot is not running"
    fi
}

# Main script
case "$1" in
    "install")
        install_dependencies
        setup_environment
        ;;
    "start")
        start_bot
        ;;
    "stop")
        stop_bot
        ;;
    "restart")
        stop_bot
        sleep 2
        start_bot
        ;;
    "status")
        check_status
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status}"
        exit 1
        ;;
esac
