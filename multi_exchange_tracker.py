import ccxt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_exchange_data.log')
    ]
)

class MultiExchangeTracker:
    def __init__(self):
        # Initialize exchanges
        self.gateio = ccxt.gateio({
            'apiKey': os.getenv('API_KEY'),
            'secret': os.getenv('API_SECRET'),
            'enableRateLimit': True
        })
        
        self.mexc = ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY'),
            'enableRateLimit': True
        })
        
        # Setup plot
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(15, 12))
        self.setup_subplots()
        
        # Data storage
        self.exchange_data = {
            'gateio': {
                'timestamps': [],
                'prices': [],
                'bids_prices': [],
                'bids_volumes': [],
                'asks_prices': [],
                'asks_volumes': [],
                'buy_pressure': [],
                'sell_pressure': [],
            },
            'mexc': {
                'timestamps': [],
                'prices': [],
                'bids_prices': [],
                'bids_volumes': [],
                'asks_prices': [],
                'asks_volumes': [],
                'buy_pressure': [],
                'sell_pressure': [],
            }
        }
        
    def setup_subplots(self):
        gs = self.fig.add_gridspec(3, 2)
        self.price_ax = self.fig.add_subplot(gs[0, :])
        self.gateio_depth_ax = self.fig.add_subplot(gs[1, 0])
        self.mexc_depth_ax = self.fig.add_subplot(gs[1, 1])
        self.gateio_pressure_ax = self.fig.add_subplot(gs[2, 0])
        self.mexc_pressure_ax = self.fig.add_subplot(gs[2, 1])
        
        self.fig.suptitle('GMRT/USDT Market Comparison (Gate.io vs MEXC)', fontsize=14)
        
    def fetch_exchange_data(self, exchange, exchange_name):
        try:
            # Fetch order book
            orderbook = exchange.fetch_order_book('GMRT/USDT', limit=50)
            trades = exchange.fetch_trades('GMRT/USDT', limit=1)
            current_price = trades[0]['price'] if trades else None
            
            # Process order book
            bids = sorted(orderbook['bids'], key=lambda x: x[0], reverse=True)
            asks = sorted(orderbook['asks'], key=lambda x: x[0])
            
            data = self.exchange_data[exchange_name]
            
            # Update price data
            current_time = datetime.now()
            data['timestamps'].append(current_time)
            data['prices'].append(current_price)
            
            # Update order book data
            data['bids_prices'] = [bid[0] for bid in bids]
            data['bids_volumes'] = [bid[1] for bid in bids]
            data['asks_prices'] = [ask[0] for ask in asks]
            data['asks_volumes'] = [ask[1] for ask in asks]
            
            # Calculate pressure
            bid_volume = sum(bid[1] for bid in bids[:10])
            ask_volume = sum(ask[1] for ask in asks[:10])
            total_volume = bid_volume + ask_volume
            
            buy_pressure = bid_volume / total_volume if total_volume > 0 else 0.5
            sell_pressure = ask_volume / total_volume if total_volume > 0 else 0.5
            
            data['buy_pressure'].append(buy_pressure)
            data['sell_pressure'].append(sell_pressure)
            
            # Keep only last 100 points
            max_points = 100
            for key in ['timestamps', 'prices', 'buy_pressure', 'sell_pressure']:
                if len(data[key]) > max_points:
                    data[key] = data[key][-max_points:]
            
            # Log data
            logging.info(f"=== {exchange_name.upper()} ===")
            logging.info(f"Price: ${current_price:.4f}")
            logging.info(f"Buy Volume: {bid_volume:.2f} GMRT")
            logging.info(f"Sell Volume: {ask_volume:.2f} GMRT")
            logging.info(f"Buy Pressure: {buy_pressure:.2%}")
            logging.info(f"Sell Pressure: {sell_pressure:.2%}")
            logging.info("-" * 50)
            
            return True
        except Exception as e:
            logging.error(f"Error fetching {exchange_name} data: {str(e)}")
            return False
    
    def update_plot(self, frame):
        try:
            # Fetch new data
            self.fetch_exchange_data(self.gateio, 'gateio')
            self.fetch_exchange_data(self.mexc, 'mexc')
            
            # Clear all axes
            for ax in [self.price_ax, self.gateio_depth_ax, self.mexc_depth_ax,
                      self.gateio_pressure_ax, self.mexc_pressure_ax]:
                ax.clear()
            
            # Plot price comparison
            gateio_data = self.exchange_data['gateio']
            mexc_data = self.exchange_data['mexc']
            
            self.price_ax.plot(gateio_data['timestamps'], gateio_data['prices'], 
                             label='Gate.io', color='cyan', alpha=0.8)
            self.price_ax.plot(mexc_data['timestamps'], mexc_data['prices'], 
                             label='MEXC', color='magenta', alpha=0.8)
            self.price_ax.set_title('Price Comparison')
            self.price_ax.set_ylabel('Price (USDT)')
            self.price_ax.grid(True, alpha=0.2)
            self.price_ax.legend()
            
            # Plot order book depth
            for exchange, ax in [('gateio', self.gateio_depth_ax), 
                               ('mexc', self.mexc_depth_ax)]:
                data = self.exchange_data[exchange]
                
                # Calculate cumulative volumes
                bids_cumulative = np.cumsum(data['bids_volumes'])
                asks_cumulative = np.cumsum(data['asks_volumes'])
                
                ax.fill_between(data['bids_prices'], bids_cumulative, 
                              color='green', alpha=0.3, label='Bids')
                ax.fill_between(data['asks_prices'], asks_cumulative, 
                              color='red', alpha=0.3, label='Asks')
                
                if data['prices']:
                    ax.axvline(x=data['prices'][-1], color='white', 
                             linestyle='--', alpha=0.5)
                
                ax.set_title(f'{exchange.upper()} Order Book Depth')
                ax.set_xlabel('Price (USDT)')
                ax.set_ylabel('Cumulative Volume (GMRT)')
                ax.grid(True, alpha=0.2)
                ax.legend()
            
            # Plot pressure
            for exchange, ax in [('gateio', self.gateio_pressure_ax), 
                               ('mexc', self.mexc_pressure_ax)]:
                data = self.exchange_data[exchange]
                
                ax.plot(data['timestamps'], data['buy_pressure'], 
                       'g-', label='Buy Pressure', alpha=0.7)
                ax.plot(data['timestamps'], data['sell_pressure'], 
                       'r-', label='Sell Pressure', alpha=0.7)
                ax.set_title(f'{exchange.upper()} Market Pressure')
                ax.set_ylabel('Pressure Ratio')
                ax.grid(True, alpha=0.2)
                ax.legend()
            
            plt.tight_layout()
            
        except Exception as e:
            logging.error(f"Error updating plot: {str(e)}")
    
    def save_market_data(self):
        market_data = {
            'gateio': {
                'timestamps': [t.isoformat() for t in self.exchange_data['gateio']['timestamps']],
                'prices': self.exchange_data['gateio']['prices'],
                'volumes': self.exchange_data['gateio']['bids_volumes'],
                'last_update': datetime.now().isoformat()
            },
            'mexc': {
                'timestamps': [t.isoformat() for t in self.exchange_data['mexc']['timestamps']],
                'prices': self.exchange_data['mexc']['prices'],
                'volumes': self.exchange_data['mexc']['bids_volumes'],
                'last_update': datetime.now().isoformat()
            }
        }
        
        os.makedirs('docs', exist_ok=True)
        with open('docs/market_data.json', 'w') as f:
            json.dump(market_data, f, indent=2)
            
    def run(self):
        """Run the market tracker"""
        logging.info("Starting multi-exchange tracker...")
        while True:
            try:
                self.fetch_exchange_data(self.gateio, 'gateio')
                self.fetch_exchange_data(self.mexc, 'mexc')
                self.save_market_data()  # Save data after each update
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logging.error(f"Error in run loop: {str(e)}")
                time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    tracker = MultiExchangeTracker()
    tracker.run()
