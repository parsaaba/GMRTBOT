import ccxt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.patheffects as path_effects
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VolumeVisualizer:
    def __init__(self):
        load_dotenv()
        
        # Initialize exchanges
        self.exchanges = {
            'gateio': ccxt.gateio({
                'apiKey': os.getenv('API_KEY'),
                'secret': os.getenv('API_SECRET')
            }),
            'mexc': ccxt.mexc({
                'apiKey': os.getenv('MEXC_API_KEY'),
                'secret': os.getenv('MEXC_SECRET_KEY')
            })
        }
        
        # Data storage
        self.exchange_data = {
            'gateio': self.create_data_storage(),
            'mexc': self.create_data_storage()
        }
        
        # Color scheme
        self.colors = {
            'gateio': '#00ffff',    # Cyan
            'mexc': '#ff00ff',      # Magenta
            'background': '#1c1c1c', # Dark gray
            'text': '#ffffff'        # White
        }
        
        # Setup plot
        plt.style.use('dark_background')
        self.fig, (self.vol_ax, self.ratio_ax) = plt.subplots(2, 1, figsize=(15, 10), 
                                                             gridspec_kw={'height_ratios': [2, 1]})
        self.fig.patch.set_facecolor(self.colors['background'])
        
    def create_data_storage(self):
        return {
            'timestamps': [],
            'volumes': [],
            'accumulated_volume': [],
            'market_share': []
        }
        
    def fetch_data(self):
        total_volume = 0
        
        # Fetch data from each exchange
        for exchange_name, exchange in self.exchanges.items():
            try:
                trades = exchange.fetch_trades('GMRT/USDT', limit=100)
                data = self.exchange_data[exchange_name]
                
                # Calculate volumes
                current_time = datetime.now()
                volume_1m = sum(t['amount'] for t in trades if t['timestamp'] > (current_time - timedelta(minutes=1)).timestamp() * 1000)
                
                # Update data
                data['timestamps'].append(current_time)
                data['volumes'].append(volume_1m)
                
                # Calculate accumulated volume
                if not data['accumulated_volume']:
                    data['accumulated_volume'].append(volume_1m)
                else:
                    data['accumulated_volume'].append(data['accumulated_volume'][-1] + volume_1m)
                
                total_volume += volume_1m
                
                logging.info(f"{exchange_name.upper()} - Volume: {volume_1m:.2f} GMRT, "
                           f"Accumulated: {data['accumulated_volume'][-1]:.2f} GMRT")
                
            except Exception as e:
                logging.error(f"Error fetching {exchange_name} data: {str(e)}")
        
        # Calculate market share
        if total_volume > 0:
            for exchange_name in self.exchanges:
                data = self.exchange_data[exchange_name]
                if data['volumes']:
                    share = (data['volumes'][-1] / total_volume) * 100
                    data['market_share'].append(share)
                    
                    # Keep arrays in sync
                    while len(data['market_share']) > len(data['timestamps']):
                        data['market_share'].pop(0)
                    while len(data['market_share']) < len(data['timestamps']):
                        data['market_share'].append(share)
                        
                    logging.info(f"{exchange_name.upper()} market share: {share:.1f}%")
        
        # Keep only recent data
        max_points = 100
        for exchange_name in self.exchanges:
            data = self.exchange_data[exchange_name]
            for key in ['timestamps', 'volumes', 'accumulated_volume', 'market_share']:
                if len(data[key]) > max_points:
                    data[key] = data[key][-max_points:]

    def update_plot(self, frame):
        self.fetch_data()
        
        # Clear axes
        self.vol_ax.clear()
        self.ratio_ax.clear()
        
        # Plot accumulated volume
        for exchange_name, data in self.exchange_data.items():
            color = self.colors[exchange_name]
            
            if data['timestamps'] and data['accumulated_volume']:
                # Plot accumulated volume
                self.vol_ax.plot(data['timestamps'], data['accumulated_volume'],
                               color=color, label=f'{exchange_name.upper()} Volume',
                               linewidth=3, path_effects=[path_effects.SimpleLineShadow(),
                                                        path_effects.Normal()])
                
                # Add current volume annotation
                current_vol = data['accumulated_volume'][-1]
                self.vol_ax.annotate(f'{current_vol:,.0f} GMRT',
                                   xy=(data['timestamps'][-1], current_vol),
                                   xytext=(10, 0), textcoords='offset points',
                                   color=color, fontsize=10, fontweight='bold',
                                   bbox=dict(facecolor='black', alpha=0.7))
                
                # Plot market share
                if data['market_share']:
                    self.ratio_ax.plot(data['timestamps'], data['market_share'],
                                     color=color, label=f'{exchange_name.upper()} Share',
                                     linewidth=2)
                    
                    # Add current share annotation
                    current_share = data['market_share'][-1]
                    self.ratio_ax.annotate(f'{current_share:.1f}%',
                                         xy=(data['timestamps'][-1], current_share),
                                         xytext=(10, 0), textcoords='offset points',
                                         color=color, fontsize=10, fontweight='bold',
                                         bbox=dict(facecolor='black', alpha=0.7))
        
        # Format volume plot
        self.vol_ax.set_title('Accumulated Trading Volume by Exchange',
                             color=self.colors['text'], pad=20, fontsize=14, fontweight='bold')
        self.vol_ax.set_ylabel('Volume (GMRT)', color=self.colors['text'], fontsize=12)
        self.vol_ax.legend(loc='upper left', facecolor='black', edgecolor='white')
        self.vol_ax.grid(True, alpha=0.2)
        
        # Format ratio plot
        self.ratio_ax.set_title('Exchange Volume Share (%)',
                               color=self.colors['text'], pad=20, fontsize=14, fontweight='bold')
        self.ratio_ax.set_ylabel('Market Share (%)', color=self.colors['text'], fontsize=12)
        self.ratio_ax.set_ylim(0, 100)
        self.ratio_ax.legend(loc='upper left', facecolor='black', edgecolor='white')
        self.ratio_ax.grid(True, alpha=0.2)
        
        # Format time axis
        for ax in [self.vol_ax, self.ratio_ax]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax.tick_params(colors=self.colors['text'])
            for spine in ax.spines.values():
                spine.set_color(self.colors['text'])
        
        plt.tight_layout()
        
    def save_data(self):
        """Save volume data to JSON file"""
        data = {
            'gateio': {
                'timestamps': [t.isoformat() for t in self.exchange_data['gateio']['timestamps']],
                'accumulated_volume': self.exchange_data['gateio']['accumulated_volume'],
                'market_share': self.exchange_data['gateio']['market_share'],
                'last_update': datetime.now().isoformat()
            },
            'mexc': {
                'timestamps': [t.isoformat() for t in self.exchange_data['mexc']['timestamps']],
                'accumulated_volume': self.exchange_data['mexc']['accumulated_volume'],
                'market_share': self.exchange_data['mexc']['market_share'],
                'last_update': datetime.now().isoformat()
            }
        }
        
        with open('docs/volume_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def run(self):
        """Run the volume visualizer"""
        # Create docs directory if it doesn't exist
        os.makedirs('docs', exist_ok=True)
        
        while True:
            try:
                self.fetch_data()
                self.save_data()
                time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(5)

if __name__ == '__main__':
    visualizer = VolumeVisualizer()
    visualizer.run()
