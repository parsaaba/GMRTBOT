import ccxt
import time
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console for testing
    ]
)

# Load API keys from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize Gate.io Exchange in test mode
exchange = ccxt.gateio({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'rateLimit': 1000,
    'options': {'defaultType': 'spot'}
})

# Test Constants
PAIR = 'GMRT/USDT'
MIN_SELL_PRICE = 0.30
FLOOR_PRICE = 0.24
LAUNCH_PRICE = 0.12
TEST_BALANCE = 5000000  # Test balance
remaining_tokens = TEST_BALANCE

def test_get_price():
    """Test price fetching"""
    try:
        ticker = exchange.fetch_ticker(PAIR)
        price = ticker['last']
        logging.info(f"✅ Current Price: ${price}")
        return price
    except Exception as e:
        logging.error(f"❌ Error fetching price: {e}")
        return None

def test_get_order_book():
    """Test order book fetching"""
    try:
        order_book = exchange.fetch_order_book(PAIR)
        logging.info("✅ Order Book Fetched Successfully!")
        logging.info(f"Top Bid: ${order_book['bids'][0][0] if order_book['bids'] else 'No bids'}")
        logging.info(f"Top Ask: ${order_book['asks'][0][0] if order_book['asks'] else 'No asks'}")
        return order_book
    except Exception as e:
        logging.error(f"❌ Error fetching order book: {e}")
        return None

def test_place_orders(price):
    """Test order placement logic"""
    global remaining_tokens
    
    if price >= MIN_SELL_PRICE:
        sell_amount = min(250000, remaining_tokens)  # Test with smaller amounts
        logging.info(f"🔵 Would place SELL order: {sell_amount} GMRT at ${price}")
        remaining_tokens -= sell_amount
    
    if price > LAUNCH_PRICE and price >= FLOOR_PRICE:
        buy_amount = 250000
        logging.info(f"🟢 Would place BUY order: {buy_amount} GMRT at ${price}")

def main():
    """Main test function"""
    logging.info("🚀 Starting bot in TEST mode...")
    logging.info(f"Initial balance: {TEST_BALANCE} GMRT")
    
    test_cycles = 5  # Number of test cycles
    
    for cycle in range(test_cycles):
        logging.info(f"\n📊 Test Cycle {cycle + 1}/{test_cycles}")
        logging.info(f"Remaining tokens: {remaining_tokens} GMRT")
        
        # Test price fetching
        current_price = test_get_price()
        if not current_price:
            logging.error("Could not fetch price, skipping cycle")
            continue
            
        # Test order book
        order_book = test_get_order_book()
        if not order_book:
            logging.error("Could not fetch order book, skipping cycle")
            continue
            
        # Test order placement logic
        test_place_orders(current_price)
        
        time.sleep(2)  # Short delay between test cycles

if __name__ == "__main__":
    main()
