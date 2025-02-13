import ccxt
import time
import logging
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
import numpy as np
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
        logging.FileHandler('market_data.log')
    ]
)

class MarketTracker:
    def __init__(self):
        # Initialize Gate.io API
        self.exchange = ccxt.gateio({
            'apiKey': os.getenv('API_KEY'),
            'secret': os.getenv('API_SECRET'),
            'enableRateLimit': True
        })
        
        # Data storage
        self.timestamps = []
        self.prices = []
        self.buy_volumes = []
        self.sell_volumes = []
        self.buy_pressure = []
        self.sell_pressure = []
        
        # Initialize plot
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('GMRT/USDT Market Data (Gate.io)')
        
    def fetch_market_data(self):
        try:
            # Fetch order book
            orderbook = self.exchange.fetch_order_book('GMRT/USDT', limit=20)
            
            # Get current price from recent trades
            trades = self.exchange.fetch_trades('GMRT/USDT', limit=1)
            current_price = trades[0]['price'] if trades else None
            
            # Calculate buy and sell pressure
            buy_volume = sum(bid[1] for bid in orderbook['bids'][:10])
            sell_volume = sum(ask[1] for ask in orderbook['asks'][:10])
            
            # Calculate pressure ratio
            total_volume = buy_volume + sell_volume
            buy_pressure_ratio = buy_volume / total_volume if total_volume > 0 else 0.5
            sell_pressure_ratio = sell_volume / total_volume if total_volume > 0 else 0.5
            
            current_time = datetime.now()
            
            # Store data
            self.timestamps.append(current_time)
            self.prices.append(current_price)
            self.buy_volumes.append(buy_volume)
            self.sell_volumes.append(sell_volume)
            self.buy_pressure.append(buy_pressure_ratio)
            self.sell_pressure.append(sell_pressure_ratio)
            
            # Keep only last 100 data points
            max_points = 100
            if len(self.timestamps) > max_points:
                self.timestamps = self.timestamps[-max_points:]
                self.prices = self.prices[-max_points:]
                self.buy_volumes = self.buy_volumes[-max_points:]
                self.sell_volumes = self.sell_volumes[-max_points:]
                self.buy_pressure = self.buy_pressure[-max_points:]
                self.sell_pressure = self.sell_pressure[-max_points:]
            
            # Log data
            logging.info(f"Price: ${current_price:.4f}")
            logging.info(f"Buy Volume: {buy_volume:.2f} GMRT")
            logging.info(f"Sell Volume: {sell_volume:.2f} GMRT")
            logging.info(f"Buy Pressure: {buy_pressure_ratio:.2%}")
            logging.info(f"Sell Pressure: {sell_pressure_ratio:.2%}")
            logging.info("-" * 50)
            
            return True
            
        except Exception as e:
            logging.error(f"Error fetching market data: {str(e)}")
            return False
    
    def update_plot(self, frame):
        try:
            # Fetch new data
            success = self.fetch_market_data()
            if not success:
                return
            
            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()
            
            # Plot price
            self.ax1.plot(self.timestamps, self.prices, 'b-', label='Price')
            self.ax1.set_ylabel('Price (USDT)')
            self.ax1.set_title('GMRT/USDT Price')
            self.ax1.grid(True, alpha=0.3)
            self.ax1.legend()
            
            # Plot buy/sell pressure
            self.ax2.plot(self.timestamps, self.buy_pressure, 'g-', label='Buy Pressure', alpha=0.7)
            self.ax2.plot(self.timestamps, self.sell_pressure, 'r-', label='Sell Pressure', alpha=0.7)
            self.ax2.set_ylabel('Pressure Ratio')
            self.ax2.set_title('Market Pressure (Buy/Sell Ratio)')
            self.ax2.grid(True, alpha=0.3)
            self.ax2.legend()
            
            # Rotate x-axis labels for better readability
            for ax in [self.ax1, self.ax2]:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
        except Exception as e:
            logging.error(f"Error updating plot: {str(e)}")
    
    def run(self):
        logging.info("Starting market tracker...")
        # Create animation that updates every 5 seconds
        ani = FuncAnimation(self.fig, self.update_plot, interval=5000)
        plt.show()

if __name__ == "__main__":
    tracker = MarketTracker()
    tracker.run()
