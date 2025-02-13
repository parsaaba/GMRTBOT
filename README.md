# GMRT Trading Bot

A sophisticated trading bot for monitoring GMRT token across multiple exchanges (Gate.io and MEXC).

## Features

- Real-time price tracking
- Accumulated volume monitoring
- Whale activity detection
- Multi-exchange support (Gate.io & MEXC)
- Advanced visualizations
- Market share analysis

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
- Copy `.env.example` to `.env`
- Add your API keys:
  - Gate.io API credentials
  - MEXC API credentials

3. Run the bot:
```bash
python whale_tracker.py
```

## Components

- `whale_tracker.py`: Main tracking script with visualizations
- `volume_visualizer.py`: Dedicated volume analysis
- `multi_exchange_tracker.py`: Multi-exchange data collection
- `market_tracker.py`: Market analysis tools

## Deployment

Multiple deployment options available:
- GitHub Actions (automated)
- Local deployment
- Cloud deployment (Oracle, AWS, etc.)

## License

MIT License
