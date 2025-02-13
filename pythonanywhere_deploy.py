import os
import sys
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_bot():
    try:
        # Import your bot here
        from whale_tracker import WhaleTracker
        
        # Initialize and run
        tracker = WhaleTracker()
        tracker.run()
        
    except Exception as e:
        logging.error(f"Bot crashed: {str(e)}")
        # Wait before restart
        time.sleep(60)

def main():
    logging.info("Starting bot on PythonAnywhere")
    
    while True:
        try:
            run_bot()
        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
            break
        except Exception as e:
            logging.error(f"Main loop error: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main()
