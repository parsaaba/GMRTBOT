import ccxt
import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

def test_exchange_connection():
    print("Testing Exchange Connection...")
    print(f"API Key exists: {'Yes' if API_KEY else 'No'}")
    print(f"API Secret exists: {'Yes' if API_SECRET else 'No'}")
    
    try:
        # Initialize exchange
        exchange = ccxt.gateio({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True
        })
        
        # Test public API
        print("\nTesting public API...")
        markets = exchange.load_markets()
        print(f"Available markets: {len(markets)} pairs")
        
        # Test private API
        print("\nTesting private API...")
        balance = exchange.fetch_balance()
        print("Successfully connected to private API")
        
        # Print available pairs
        print("\nLooking for GMRT pairs...")
        gmrt_pairs = [pair for pair in markets.keys() if 'GMRT' in pair]
        if gmrt_pairs:
            print(f"Found GMRT pairs: {gmrt_pairs}")
        else:
            print("No GMRT pairs found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_exchange_connection()
