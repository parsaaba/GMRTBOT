import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import os
import ccxt
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="GMRT Market Tracker",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("GMRT Market Analysis 📊")

# Initialize exchanges
@st.cache_resource
def init_exchanges():
    return {
        'gateio': ccxt.gateio({
            'apiKey': os.getenv('API_KEY'),
            'secret': os.getenv('API_SECRET')
        }),
        'mexc': ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY')
        })
    }

exchanges = init_exchanges()

# Function to fetch market data
def fetch_market_data():
    data = {
        'gateio': {'prices': [], 'volumes': [], 'timestamps': []},
        'mexc': {'prices': [], 'volumes': [], 'timestamps': []}
    }
    
    for name, exchange in exchanges.items():
        try:
            trades = exchange.fetch_trades('GMRT/USDT', limit=100)
            if trades:
                data[name]['prices'] = [t['price'] for t in trades]
                data[name]['volumes'] = [t['amount'] for t in trades]
                data[name]['timestamps'] = [datetime.fromtimestamp(t['timestamp']/1000) for t in trades]
        except Exception as e:
            st.error(f"Error fetching {name} data: {str(e)}")
    
    return data

# Create dashboard layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Price Comparison")
    price_fig = go.Figure()
    
    market_data = fetch_market_data()
    
    # Add price lines for each exchange
    for exchange, data in market_data.items():
        if data['timestamps']:
            price_fig.add_trace(
                go.Scatter(
                    x=data['timestamps'],
                    y=data['prices'],
                    name=f"{exchange.upper()} Price",
                    line=dict(width=2),
                )
            )
    
    price_fig.update_layout(
        template="plotly_dark",
        title="GMRT Price Across Exchanges",
        xaxis_title="Time",
        yaxis_title="Price (USDT)",
        height=400
    )
    
    st.plotly_chart(price_fig, use_container_width=True)

with col2:
    st.subheader("Volume Analysis")
    volume_fig = go.Figure()
    
    # Add volume bars for each exchange
    for exchange, data in market_data.items():
        if data['timestamps']:
            volume_fig.add_trace(
                go.Bar(
                    x=data['timestamps'],
                    y=data['volumes'],
                    name=f"{exchange.upper()} Volume",
                    opacity=0.7
                )
            )
    
    volume_fig.update_layout(
        template="plotly_dark",
        title="Trading Volume Comparison",
        xaxis_title="Time",
        yaxis_title="Volume (GMRT)",
        height=400,
        barmode='group'
    )
    
    st.plotly_chart(volume_fig, use_container_width=True)

# Market Statistics
st.subheader("Market Statistics")
stats_cols = st.columns(4)

for idx, (exchange, data) in enumerate(market_data.items()):
    if data['prices']:
        with stats_cols[idx]:
            st.metric(
                f"{exchange.upper()} Price",
                f"${data['prices'][-1]:.4f}",
                f"{((data['prices'][-1] - data['prices'][0]) / data['prices'][0] * 100):.2f}%"
            )
        with stats_cols[idx+2]:
            st.metric(
                f"{exchange.upper()} Volume",
                f"{sum(data['volumes']):.2f} GMRT",
                None
            )

# Auto-refresh
if st.button('Refresh Data'):
    st.experimental_rerun()
else:
    time.sleep(5)
    st.experimental_rerun()
