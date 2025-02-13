import ccxt
import time
import os
import logging
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize logging
logging.basicConfig(filename="gmrt_trading.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def log_trade(action, amount, price):
    log_message = f"{action} order: {amount} GMRT at ${price}"
    print(log_message)
    logging.info(log_message)

# Initialize Gate.io Exchange
exchange = ccxt.gateio({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'rateLimit': 1000,
    'options': {'defaultType': 'spot'}
})

# Constants
PAIR = 'GMRT/USDT'
MIN_SELL_PRICE = 0.30  # Minimum sell price (2.5x listing price)
FLOOR_PRICE = 0.24  # 2x launch price (MM floor)
LAUNCH_PRICE = 0.12
TOTAL_TOKENS = 5000000  # Tokens to sell
remaining_tokens = TOTAL_TOKENS
DEPTH_PERCENTAGE = 0.02  # 2% market depth tracking
BASE_TRADE_AMOUNT = 250000  # Default trade size
MM_UID = '20368306'  # Market Maker UID
active_orders = []  # Track active orders

# Function to fetch the current price
def get_price():
    try:
        ticker = exchange.fetch_ticker(PAIR)
        price = ticker['last']
        print(f"✅ Current Price: ${price}")
        return price
    except Exception as e:
        logging.error(f"Error fetching price: {e}")
        print("❌ Error: Could not fetch price from Gate.io. Retrying in 5 seconds...")
        return None

# Function to get order book data
def get_order_book():
    try:
        order_book = exchange.fetch_order_book(PAIR)
        print("✅ Order Book Fetched Successfully!")
        return order_book
    except Exception as e:
        logging.error(f"Error fetching order book: {e}")
        print("❌ Error: Could not fetch order book. Retrying in 5 seconds...")
        return None

# Function to fetch MM orders
def get_mm_orders():
    try:
        all_orders = exchange.fetch_open_orders(PAIR)
        mm_orders = [order for order in all_orders if order['user'] == MM_UID]
        return mm_orders
    except Exception as e:
        logging.error(f"Error fetching MM orders: {e}")
        return []

# Function to cancel all active orders
def cancel_active_orders():
    global active_orders
    for order_id in active_orders:
        try:
            exchange.cancel_order(order_id, PAIR)
            logging.info(f"Cancelled order: {order_id}")
        except Exception as e:
            logging.error(f"Error cancelling order {order_id}: {e}")
    active_orders = []  # Reset active orders list

# Function to dynamically calculate trade size based on liquidity
def get_dynamic_trade_amount(order_book):
    bids = order_book['bids'][:5]  # Consider top 5 buy orders
    total_liquidity = sum([bid[1] for bid in bids])  # Sum of GMRT in top orders
    dynamic_amount = min(remaining_tokens, max(BASE_TRADE_AMOUNT, total_liquidity * 0.5))  # Max 50% of liquidity
    return dynamic_amount

# Function to place a buy order
def place_buy_order(price, amount):
    try:
        order = exchange.create_limit_buy_order(PAIR, amount, price)
        log_trade("Placed buy", amount, price)
        active_orders.append(order['id'])  # Store active order ID
    except Exception as e:
        logging.error(f"Error placing buy order: {e}")

# Function to place a sell order
def place_sell_order(price, amount):
    try:
        order = exchange.create_limit_sell_order(PAIR, amount, price)
        log_trade("Placed sell", amount, price)
        active_orders.append(order['id'])  # Store active order ID
    except Exception as e:
        logging.error(f"Error placing sell order: {e}")

# Main trading loop
while remaining_tokens > 0:
    current_price = get_price()
    if not current_price:
        time.sleep(5)
        continue

    order_book = get_order_book()
    if not order_book:
        time.sleep(5)
        continue

    mm_orders = get_mm_orders()
    
    # Cancel all existing orders to adjust to market conditions
    cancel_active_orders()

    # Maintain market depth of 2%
    min_depth_price = current_price * (1 - DEPTH_PERCENTAGE)
    max_depth_price = current_price * (1 + DEPTH_PERCENTAGE)

    logging.info(f"Current price: ${current_price}, Depth Range: ${min_depth_price} - ${max_depth_price}")

    if current_price >= MIN_SELL_PRICE:
        sell_price = max(min_depth_price, MIN_SELL_PRICE)  # Never sell below 2.5x
        sell_amount = get_dynamic_trade_amount(order_book)  # Adjust sell size dynamically
        place_sell_order(sell_price, sell_amount)
        remaining_tokens -= sell_amount
    
    # Only place buy orders if price is above launch price ($0.12)
    if current_price > LAUNCH_PRICE and current_price >= FLOOR_PRICE:
        mm_buy_price = min([order['price'] for order in mm_orders if order['side'] == 'buy'], default=min_depth_price)
        buy_price = max(min_depth_price, mm_buy_price)  # Align with MM buy levels
        buy_amount = get_dynamic_trade_amount(order_book)
        place_buy_order(buy_price, buy_amount)
    
    time.sleep(5)  # Wait before checking market again