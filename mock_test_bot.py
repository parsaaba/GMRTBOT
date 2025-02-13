import time
import logging
import random
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mock_bot_test.log')
    ]
)

# Mock Market Parameters
INITIAL_PRICE = 0.35  # Starting above MIN_SELL_PRICE
VOLATILITY = 0.03     # 3% price movement volatility
TEST_BALANCE = 5000000  # Test balance
SIMULATION_CYCLES = 30  # Number of test cycles

# Bot Parameters (from original bot)
MIN_SELL_PRICE = 0.30  # 2.5x listing price
FLOOR_PRICE = 0.24    # 2x launch price (MM floor)
LAUNCH_PRICE = 0.12   # Launch price
BASE_TRADE_AMOUNT = 250000

class MockMarket:
    def __init__(self):
        self.current_price = INITIAL_PRICE
        self.order_book = {
            'bids': [],  # [[price, amount], ...]
            'asks': []   # [[price, amount], ...]
        }
        self.mm_orders = []
        self.price_history = []
        self.timestamps = []
        
    def update_price(self):
        """Simulate price movement with trend"""
        trend = -0.001 if len(self.price_history) % 10 < 5 else 0.001  # Alternate trend
        change = random.uniform(-VOLATILITY, VOLATILITY) + trend
        self.current_price *= (1 + change)
        self.price_history.append(self.current_price)
        self.timestamps.append(datetime.now())
        return self.current_price
        
    def generate_order_book(self):
        """Generate mock order book"""
        spread = self.current_price * 0.01  # 1% spread
        
        # Generate 5 bids and asks
        self.order_book['bids'] = [
            [self.current_price - spread * (i+1), random.uniform(1000, 10000)]
            for i in range(5)
        ]
        self.order_book['asks'] = [
            [self.current_price + spread * (i+1), random.uniform(1000, 10000)]
            for i in range(5)
        ]
        
        return self.order_book
        
    def simulate_mm_orders(self):
        """Simulate market maker orders"""
        self.mm_orders = [
            {'side': 'buy', 'price': self.current_price * 0.99, 'amount': 5000},
            {'side': 'buy', 'price': self.current_price * 0.98, 'amount': 10000},
            {'side': 'sell', 'price': self.current_price * 1.01, 'amount': 5000},
        ]
        return self.mm_orders

    def plot_price_history(self, trades):
        """Plot price history and trades"""
        plt.figure(figsize=(12, 6))
        
        # Plot price history
        plt.plot(range(len(self.price_history)), self.price_history, 'b-', label='Price', alpha=0.7)
        
        # Plot threshold lines
        plt.axhline(y=MIN_SELL_PRICE, color='r', linestyle='--', label='Min Sell Price', alpha=0.5)
        plt.axhline(y=FLOOR_PRICE, color='g', linestyle='--', label='Floor Price', alpha=0.5)
        
        # Plot trades
        sell_points = [(i, trade['price']) for i, trade in enumerate(trades) if trade['type'] == 'SELL']
        buy_points = [(i, trade['price']) for i, trade in enumerate(trades) if trade['type'] == 'BUY']
        
        if sell_points:
            x_sell, y_sell = zip(*sell_points)
            plt.scatter(x_sell, y_sell, color='red', marker='v', label='Sell', alpha=0.6)
        
        if buy_points:
            x_buy, y_buy = zip(*buy_points)
            plt.scatter(x_buy, y_buy, color='green', marker='^', label='Buy', alpha=0.6)
        
        plt.title('GMRT/USDT Price Movement and Trading Activity')
        plt.xlabel('Time (cycles)')
        plt.ylabel('Price (USDT)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot
        plt.savefig('trading_activity.png')
        plt.close()

class MockBot:
    def __init__(self):
        self.market = MockMarket()
        self.remaining_tokens = TEST_BALANCE
        self.total_sold = 0
        self.total_bought = 0
        self.trades = []
        self.total_sell_value = 0
        self.total_buy_value = 0
        
    def simulate_trade(self):
        """Simulate one trading cycle"""
        # Get current market conditions
        price = self.market.update_price()
        order_book = self.market.generate_order_book()
        mm_orders = self.market.simulate_mm_orders()
        
        logging.info(f"\n{'='*50}")
        logging.info(f"📊 Market Price: ${price:.4f}")
        logging.info(f"💰 Remaining Tokens: {self.remaining_tokens:,}")
        logging.info(f"📈 Total Sold: {self.total_sold:,} (${self.total_sell_value:.2f})")
        logging.info(f"📉 Total Bought: {self.total_bought:,} (${self.total_buy_value:.2f})")
        
        # Simulate sell logic
        if price >= MIN_SELL_PRICE:
            sell_amount = min(BASE_TRADE_AMOUNT, self.remaining_tokens)
            if sell_amount > 0:
                self.remaining_tokens -= sell_amount
                self.total_sold += sell_amount
                self.total_sell_value += sell_amount * price
                self.trades.append({
                    'type': 'SELL',
                    'price': price,
                    'amount': sell_amount,
                    'value': sell_amount * price,
                    'time': datetime.now()
                })
                logging.info(f"🔴 SELL: {sell_amount:,} tokens at ${price:.4f} (Value: ${sell_amount * price:,.2f})")
        
        # Simulate buy logic
        if price > LAUNCH_PRICE and price >= FLOOR_PRICE:
            buy_amount = BASE_TRADE_AMOUNT
            self.remaining_tokens += buy_amount
            self.total_bought += buy_amount
            self.total_buy_value += buy_amount * price
            self.trades.append({
                'type': 'BUY',
                'price': price,
                'amount': buy_amount,
                'value': buy_amount * price,
                'time': datetime.now()
            })
            logging.info(f"🟢 BUY: {buy_amount:,} tokens at ${price:.4f} (Value: ${buy_amount * price:,.2f})")
            
        # Show order book summary
        top_bid = order_book['bids'][0] if order_book['bids'] else [0, 0]
        top_ask = order_book['asks'][0] if order_book['asks'] else [0, 0]
        logging.info(f"📚 Order Book - Top Bid: ${top_bid[0]:.4f}, Top Ask: ${top_ask[0]:.4f}")
        
    def run_simulation(self):
        """Run the complete simulation"""
        logging.info("\n🚀 Starting Mock Trading Bot Simulation")
        logging.info(f"Initial Balance: {TEST_BALANCE:,} tokens")
        logging.info(f"Initial Price: ${INITIAL_PRICE:.4f}")
        logging.info(f"Min Sell Price: ${MIN_SELL_PRICE:.4f}")
        logging.info(f"Floor Price: ${FLOOR_PRICE:.4f}")
        
        for i in range(SIMULATION_CYCLES):
            logging.info(f"\n📍 Simulation Cycle {i+1}/{SIMULATION_CYCLES}")
            self.simulate_trade()
            time.sleep(1)  # Short delay between cycles
            
        # Show final summary
        logging.info("\n" + "="*50)
        logging.info("📊 Simulation Complete - Final Summary")
        logging.info(f"💰 Final Token Balance: {self.remaining_tokens:,}")
        logging.info(f"📈 Total Tokens Sold: {self.total_sold:,} (${self.total_sell_value:,.2f})")
        logging.info(f"📉 Total Tokens Bought: {self.total_bought:,} (${self.total_buy_value:,.2f})")
        logging.info(f"💵 Net Value: ${self.total_sell_value - self.total_buy_value:,.2f}")
        logging.info(f"🔄 Total Trades: {len(self.trades)}")
        
        # Price movement summary
        price_changes = [100 * (b/a - 1) for a, b in zip(self.market.price_history[:-1], self.market.price_history[1:])]
        if price_changes:
            avg_price_change = sum(price_changes) / len(price_changes)
            logging.info(f"📈 Average Price Change: {avg_price_change:.2f}%")
            logging.info(f"📊 Price Range: ${min(self.market.price_history):.4f} - ${max(self.market.price_history):.4f}")
        
        # Generate and save the price chart
        self.market.plot_price_history(self.trades)
        logging.info("\n📈 Price chart has been saved as 'trading_activity.png'")

if __name__ == "__main__":
    bot = MockBot()
    bot.run_simulation()
