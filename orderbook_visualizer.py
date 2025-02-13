import ccxt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('orderbook_data.log')
    ]
)

class OrderBookVisualizer:
    def __init__(self):
        # Initialize Gate.io API
        self.exchange = ccxt.gateio({
            'apiKey': os.getenv('API_KEY'),
            'secret': os.getenv('API_SECRET'),
            'enableRateLimit': True
        })
        
        # Initialize plot
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 10))
        self.fig.suptitle('GMRT/USDT Order Book Depth (Gate.io)', fontsize=14)
        
        # Data storage
        self.bids_prices = []
        self.bids_volumes = []
        self.asks_prices = []
        self.asks_volumes = []
        self.last_price = None
        self.bid_total = 0
        self.ask_total = 0
        
    def fetch_orderbook(self):
        try:
            # Fetch full order book
            orderbook = self.exchange.fetch_order_book('GMRT/USDT', limit=100)
            
            # Get current price from recent trades
            trades = self.exchange.fetch_trades('GMRT/USDT', limit=1)
            self.last_price = trades[0]['price'] if trades else None
            
            # Process bids and asks
            bids = orderbook['bids']  # [[price, volume], ...]
            asks = orderbook['asks']
            
            # Sort and accumulate volumes
            bids = sorted(bids, key=lambda x: x[0], reverse=True)  # High to low
            asks = sorted(asks, key=lambda x: x[0])  # Low to high
            
            # Separate prices and volumes
            self.bids_prices = [bid[0] for bid in bids]
            self.bids_volumes = [bid[1] for bid in bids]
            self.asks_prices = [ask[0] for ask in asks]
            self.asks_volumes = [ask[1] for ask in asks]
            
            # Calculate cumulative volumes
            self.bids_cumulative = np.cumsum(self.bids_volumes)
            self.asks_cumulative = np.cumsum(self.asks_volumes)
            
            # Calculate totals
            self.bid_total = sum(self.bids_volumes)
            self.ask_total = sum(self.asks_volumes)
            
            # Log data
            logging.info(f"Current Price: ${self.last_price:.4f}")
            logging.info(f"Total Bid Volume: {self.bid_total:.2f} GMRT")
            logging.info(f"Total Ask Volume: {self.ask_total:.2f} GMRT")
            logging.info(f"Bid/Ask Ratio: {(self.bid_total/self.ask_total if self.ask_total > 0 else 0):.2f}")
            logging.info("-" * 50)
            
            return True
            
        except Exception as e:
            logging.error(f"Error fetching order book: {str(e)}")
            return False
            
    def update_plot(self, frame):
        try:
            # Fetch new data
            success = self.fetch_orderbook()
            if not success:
                return
            
            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()
            
            # Plot order book depth
            self.ax1.fill_between(self.bids_prices, self.bids_cumulative, color='green', alpha=0.3, label='Bids')
            self.ax1.fill_between(self.asks_prices, self.asks_cumulative, color='red', alpha=0.3, label='Asks')
            
            if self.last_price:
                self.ax1.axvline(x=self.last_price, color='white', linestyle='--', alpha=0.5, label=f'Last Price: ${self.last_price:.4f}')
            
            self.ax1.set_title('Order Book Depth')
            self.ax1.set_xlabel('Price (USDT)')
            self.ax1.set_ylabel('Cumulative Volume (GMRT)')
            self.ax1.grid(True, alpha=0.2)
            self.ax1.legend()
            
            # Plot volume distribution
            max_bars = 20  # Number of price levels to show
            bar_width = 0.0004  # Width of the bars
            
            # Bids distribution
            bid_volumes = self.bids_volumes[:max_bars]
            bid_prices = self.bids_prices[:max_bars]
            self.ax2.bar(bid_prices, bid_volumes, width=bar_width, color='green', alpha=0.3, label='Bid Volume')
            
            # Asks distribution
            ask_volumes = self.asks_volumes[:max_bars]
            ask_prices = self.asks_prices[:max_bars]
            self.ax2.bar(ask_prices, ask_volumes, width=bar_width, color='red', alpha=0.3, label='Ask Volume')
            
            if self.last_price:
                self.ax2.axvline(x=self.last_price, color='white', linestyle='--', alpha=0.5)
            
            self.ax2.set_title('Volume Distribution')
            self.ax2.set_xlabel('Price (USDT)')
            self.ax2.set_ylabel('Volume (GMRT)')
            self.ax2.grid(True, alpha=0.2)
            self.ax2.legend()
            
            # Add market stats
            stats_text = f'Bid Total: {self.bid_total:.2f} GMRT\n'
            stats_text += f'Ask Total: {self.ask_total:.2f} GMRT\n'
            stats_text += f'Bid/Ask Ratio: {(self.bid_total/self.ask_total if self.ask_total > 0 else 0):.2f}'
            
            plt.figtext(0.02, 0.02, stats_text, fontsize=10, color='white')
            
            plt.tight_layout()
            
        except Exception as e:
            logging.error(f"Error updating plot: {str(e)}")
    
    def run(self):
        logging.info("Starting order book visualizer...")
        # Create animation that updates every 2 seconds
        ani = FuncAnimation(self.fig, self.update_plot, interval=2000)
        plt.show()

if __name__ == "__main__":
    visualizer = OrderBookVisualizer()
    visualizer.run()
