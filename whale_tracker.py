import ccxt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
import matplotlib.patheffects as path_effects
from matplotlib.colors import LinearSegmentedColormap

# Load environment variables
load_dotenv()

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('whale_alerts.log')
    ]
)

class WhaleTracker:
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
        
        # Configuration
        self.whale_threshold = 10000  # USDT value for whale alert
        self.significant_price_change = 0.02  # 2% price change
        
        # Setup plot with dark theme
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 12))
        self.setup_subplots()
        
        # Color scheme
        self.colors = {
            'gateio': '#00ffff',  # Cyan
            'mexc': '#ff00ff',    # Magenta
            'buy': '#00ff00',     # Bright Green
            'sell': '#ff4444',    # Bright Red
            'neutral': '#ffffff',  # White
            'alert': '#ffff00'    # Yellow
        }
        
        # Initialize data storage
        self.initialize_data_storage()
        
    def initialize_data_storage(self):
        self.exchange_data = {
            'gateio': self.create_exchange_storage(),
            'mexc': self.create_exchange_storage()
        }
    
    def create_exchange_storage(self):
        return {
            'timestamps': [],
            'prices': [],
            'volumes': [],
            'accumulated_volume': [],  # Add accumulated volume tracking
            'trades': [],
            'whale_alerts': [],
            'large_orders': {
                'bids': [],
                'asks': []
            },
            'volume_profile': pd.DataFrame(columns=['price', 'volume']),
            'last_trades': [],
            'price_changes': []
        }
    
    def setup_subplots(self):
        gs = GridSpec(8, 2, figure=self.fig)
        
        # Price and Volume (3 rows)
        self.price_vol_ax = self.fig.add_subplot(gs[0:2, :])
        
        # Exchange-specific plots (2 rows each)
        self.gateio_depth_ax = self.fig.add_subplot(gs[2:4, 0])
        self.mexc_depth_ax = self.fig.add_subplot(gs[2:4, 1])
        
        # Volume profiles (2 rows)
        self.gateio_vol_profile_ax = self.fig.add_subplot(gs[4:6, 0])
        self.mexc_vol_profile_ax = self.fig.add_subplot(gs[4:6, 1])
        
        # Whale alerts (2 rows)
        self.whale_alert_ax = self.fig.add_subplot(gs[6:8, :])
        
        self.fig.suptitle('🐋 GMRT/USDT Whale Activity Tracker 🐋', 
                         fontsize=16, color='white', y=0.95)
        
        # Add timestamp
        self.timestamp_text = self.fig.text(
            0.99, 0.01, '', 
            ha='right', va='bottom',
            color='gray', fontsize=8
        )
    
    def format_price_axis(self, ax):
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('gray')
    
    def update_plot(self, frame):
        try:
            # Fetch new data
            self.fetch_exchange_data(self.gateio, 'gateio')
            self.fetch_exchange_data(self.mexc, 'mexc')
            
            # Clear all axes
            for ax in [self.price_vol_ax, self.gateio_depth_ax, self.mexc_depth_ax,
                      self.gateio_vol_profile_ax, self.mexc_vol_profile_ax, 
                      self.whale_alert_ax]:
                ax.clear()
            
            # Update price and volume plot
            self.plot_price_and_volume()
            
            # Update order book and trades
            self.plot_order_book('gateio', self.gateio_depth_ax)
            self.plot_order_book('mexc', self.mexc_depth_ax)
            
            # Update volume profiles
            self.plot_volume_profile('gateio', self.gateio_vol_profile_ax)
            self.plot_volume_profile('mexc', self.mexc_vol_profile_ax)
            
            # Update whale alerts
            self.plot_whale_alerts()
            
            # Update timestamp
            self.timestamp_text.set_text(
                f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
            
            plt.tight_layout(rect=[0, 0.02, 1, 0.95])
            
        except Exception as e:
            logging.error(f"Error updating plot: {str(e)}")
    
    def plot_price_and_volume(self):
        ax1 = self.price_vol_ax
        ax2 = ax1.twinx()
        
        # Plot accumulated volume for both exchanges
        for exchange in ['gateio', 'mexc']:
            data = self.exchange_data[exchange]
            color = self.colors[exchange]
            
            # Plot price
            ax1.plot(data['timestamps'], data['prices'],
                    color=color, label=f'{exchange.upper()} Price',
                    linewidth=2)
            
            # Plot accumulated volume with enhanced visibility
            ax2.plot(data['timestamps'], data['accumulated_volume'],
                    color=color, label=f'{exchange.upper()} Acc. Vol',
                    linewidth=3, linestyle='-',
                    path_effects=[path_effects.SimpleLineShadow(),
                                path_effects.Normal()])
            
            # Add current accumulated volume annotation
            if data['accumulated_volume']:
                current_acc_vol = data['accumulated_volume'][-1]
                ax2.annotate(f'{current_acc_vol:,.0f}',
                           xy=(data['timestamps'][-1], current_acc_vol),
                           xytext=(10, 0), textcoords='offset points',
                           color=color, fontsize=10, fontweight='bold',
                           bbox=dict(facecolor='black', alpha=0.7))
        
        # Formatting
        ax1.set_title('Price and Accumulated Volume', 
                     color='white', pad=20, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price (USDT)', color='white', fontsize=12)
        ax2.set_ylabel('Accumulated Volume (GMRT)', color='white', fontsize=12)
        
        # Add legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2,
                  loc='upper left', bbox_to_anchor=(0, 1),
                  ncol=2, facecolor='black', edgecolor='white',
                  fontsize=10)
        
        self.format_price_axis(ax1)
        self.format_price_axis(ax2)
        ax1.grid(True, alpha=0.2, linestyle='--', color='white')
    
    def plot_order_book(self, exchange, ax):
        data = self.exchange_data[exchange]
        
        if data['last_trades']:
            trades_df = pd.DataFrame(data['last_trades'])
            
            # Plot trades with enhanced visibility
            for side in ['buy', 'sell']:
                side_trades = trades_df[trades_df['side'] == side]
                
                # Add trade points with glowing effect
                ax.scatter(side_trades['price'], side_trades['amount'],
                         color=self.colors[side], alpha=0.6, s=150,
                         label=f'{side.capitalize()} Trades',
                         marker='o' if side == 'buy' else 'v',
                         edgecolor='white', linewidth=1)
            
            # Highlight large orders with enhanced markers
            for order_type in ['bids', 'asks']:
                for order in data['large_orders'][order_type]:
                    price, volume, _ = order
                    # Add glowing effect for large orders
                    for size in [350, 300, 250]:
                        ax.scatter(price, volume,
                                 color=self.colors['alert'],
                                 s=size, alpha=0.3)
                    
                    ax.scatter(price, volume,
                             color=self.colors['alert'],
                             s=200, marker='*',
                             label=f'Large {order_type[:-1].capitalize()}',
                             edgecolor='white', linewidth=1)
                    
                    # Add value annotation with better visibility
                    value = price * volume
                    ax.annotate(f'${value:,.0f}',
                              (price, volume),
                              xytext=(10, 10),
                              textcoords='offset points',
                              color=self.colors['alert'],
                              fontsize=10,
                              fontweight='bold',
                              bbox=dict(facecolor='black', edgecolor='white',
                                      alpha=0.7))
        
        # Enhanced title and labels
        ax.set_title(f'{exchange.upper()} Order Book & Trades',
                    color='white', pad=20, fontsize=14, fontweight='bold')
        ax.set_xlabel('Price (USDT)', color='white', fontsize=12)
        ax.set_ylabel('Volume (GMRT)', color='white', fontsize=12)
        
        # Enhanced legend
        ax.legend(loc='upper right', facecolor='black',
                 edgecolor='white', fontsize=10,
                 markerscale=1.5)
        
        self.format_price_axis(ax)
        ax.grid(True, alpha=0.2, linestyle='--', color='white')
    
    def plot_volume_profile(self, exchange, ax):
        data = self.exchange_data[exchange]
        vp = data['volume_profile']
        
        if not vp.empty:
            # Create gradient colors for volume bars
            colors = plt.cm.get_cmap('plasma')(np.linspace(0, 1, len(vp)))
            
            bars = ax.barh(vp['price'], vp['volume'],
                         alpha=0.6, color=colors)
            
            # Add value labels for significant volumes
            mean_volume = np.mean(vp['volume'])
            for i, (price, volume) in enumerate(zip(vp['price'], vp['volume'])):
                if volume > mean_volume * 1.5:  # Significant volume
                    ax.text(volume, price, f' {volume:,.0f}',
                           va='center', ha='left',
                           color='white', fontsize=9,
                           fontweight='bold',
                           bbox=dict(facecolor='black', alpha=0.7))
        
        # Enhanced title and labels
        ax.set_title(f'{exchange.upper()} Volume Profile',
                    color='white', pad=20, fontsize=14, fontweight='bold')
        ax.set_xlabel('Volume (GMRT)', color='white', fontsize=12)
        ax.set_ylabel('Price (USDT)', color='white', fontsize=12)
        
        self.format_price_axis(ax)
        ax.grid(True, alpha=0.2, linestyle='--', color='white')
    
    def plot_whale_alerts(self):
        ax = self.whale_alert_ax
        
        for exchange in ['gateio', 'mexc']:
            data = self.exchange_data[exchange]
            alerts = data['whale_alerts'][-10:]  # Show last 10 alerts
            
            for i, alert in enumerate(alerts):
                # Enhanced marker sizes based on value
                size = min(400, max(200, alert['value_usdt'] / 100))
                
                # Create glowing effect
                for s in [size + 50, size + 25, size]:
                    ax.scatter(alert['timestamp'], i,
                             color=self.colors[alert['side']],
                             s=s, alpha=0.3, marker='o')
                
                # Main marker
                ax.scatter(alert['timestamp'], i,
                         color=self.colors[alert['side']],
                         s=size, marker='o',
                         edgecolor='white', linewidth=1)
                
                # Enhanced annotation with background
                ax.annotate(
                    f"🐋 {exchange.upper()}: "
                    f"{'BUY' if alert['side'] == 'buy' else 'SELL'} "
                    f"{alert['amount']:.2f} GMRT @ ${alert['price']:.4f}\n"
                    f"Value: ${alert['value_usdt']:,.2f}",
                    (alert['timestamp'], i),
                    xytext=(15, 0),
                    textcoords='offset points',
                    color=self.colors[alert['side']],
                    fontsize=11,
                    fontweight='bold',
                    bbox=dict(facecolor='black', edgecolor=self.colors[alert['side']],
                            alpha=0.7, pad=2)
                )
        
        # Enhanced title
        ax.set_title('Recent Whale Activities 🐋',
                    color='white', pad=20, fontsize=14, fontweight='bold')
        ax.set_yticks([])
        
        # Format time axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
        
        self.format_price_axis(ax)
        ax.grid(True, alpha=0.2, linestyle='--', color='white')
    
    def detect_whale_activity(self, trade, exchange_name):
        volume_usdt = trade['price'] * trade['amount']
        if volume_usdt >= self.whale_threshold:
            alert = {
                'timestamp': trade['timestamp'],
                'side': trade['side'],
                'price': trade['price'],
                'amount': trade['amount'],
                'value_usdt': volume_usdt
            }
            self.exchange_data[exchange_name]['whale_alerts'].append(alert)
            logging.warning(f"🐋 WHALE ALERT on {exchange_name.upper()}: "
                          f"{'BUY' if trade['side'] == 'buy' else 'SELL'} "
                          f"{trade['amount']:.2f} GMRT at ${trade['price']:.4f} "
                          f"(${volume_usdt:.2f} USDT)")
    
    def analyze_volume_profile(self, exchange_name, trades):
        df = pd.DataFrame(trades)
        if not df.empty:
            # Group by price and sum volumes
            volume_profile = df.groupby('price')['amount'].sum().reset_index()
            self.exchange_data[exchange_name]['volume_profile'] = volume_profile
    
    def detect_large_orders(self, orderbook, exchange_name, side='bids'):
        orders = orderbook[side]
        large_orders = []
        
        for price, volume in orders:
            value_usdt = price * volume
            if value_usdt >= self.whale_threshold:
                large_orders.append((price, volume, datetime.now()))
                logging.info(f"Large {side[:-1]} order detected on {exchange_name.upper()}: "
                           f"{volume:.2f} GMRT at ${price:.4f} (${value_usdt:.2f} USDT)")
        
        self.exchange_data[exchange_name]['large_orders'][side] = large_orders
    
    def fetch_exchange_data(self, exchange, exchange_name):
        try:
            # Fetch recent trades
            trades = exchange.fetch_trades('GMRT/USDT', limit=100)
            
            # Fetch order book
            orderbook = exchange.fetch_order_book('GMRT/USDT', limit=100)
            
            data = self.exchange_data[exchange_name]
            
            # Process trades
            for trade in trades:
                self.detect_whale_activity(trade, exchange_name)
            
            # Update trade history
            data['last_trades'] = trades
            
            # Analyze volume profile
            self.analyze_volume_profile(exchange_name, trades)
            
            # Detect large orders in order book
            self.detect_large_orders(orderbook, exchange_name, 'bids')
            self.detect_large_orders(orderbook, exchange_name, 'asks')
            
            # Update time series data
            current_time = datetime.now()
            last_price = trades[-1]['price'] if trades else None
            volume_1m = sum(t['amount'] for t in trades if t['timestamp'] > (current_time - timedelta(minutes=1)).timestamp() * 1000)
            
            data['timestamps'].append(current_time)
            data['prices'].append(last_price)
            data['volumes'].append(volume_1m)
            
            # Calculate accumulated volume
            if not data['accumulated_volume']:
                data['accumulated_volume'].append(volume_1m)
            else:
                data['accumulated_volume'].append(data['accumulated_volume'][-1] + volume_1m)
            
            # Keep only recent data
            max_points = 100
            for key in ['timestamps', 'prices', 'volumes', 'accumulated_volume']:
                if len(data[key]) > max_points:
                    data[key] = data[key][-max_points:]
            
            # Log summary
            logging.info(f"=== {exchange_name.upper()} Summary ===")
            logging.info(f"Current Price: ${last_price:.4f}")
            logging.info(f"1min Volume: {volume_1m:.2f} GMRT")
            logging.info(f"Accumulated Volume: {data['accumulated_volume'][-1]:.2f} GMRT")
            logging.info(f"Large Bids: {len(data['large_orders']['bids'])}")
            logging.info(f"Large Asks: {len(data['large_orders']['asks'])}")
            logging.info("-" * 50)
            
            return True
        except Exception as e:
            logging.error(f"Error fetching {exchange_name} data: {str(e)}")
            return False
    
    def run(self):
        logging.info("Starting enhanced whale tracker...")
        ani = FuncAnimation(self.fig, self.update_plot, interval=3000)
        plt.show()

if __name__ == "__main__":
    tracker = WhaleTracker()
    tracker.run()
