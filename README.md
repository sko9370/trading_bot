# Alpaca Trading Bot

## Background
Alpaca released their v2 [API](https://github.com/alpacahq/alpaca-py) at some point after I created my first bot a few years ago. The 2024 version of my script updates the functions to use the latest API.

## Purpose
This bot simply rebalances the portfolio according to allocations set in the `pf_allocs` dictionary at the top of the script. The current portfolio is called the [Ginger Ale Portfolio](https://www.optimizedportfolio.com/ginger-ale-portfolio/), developed by John Williamson at Optimized Portfolio. In short, historical data shows that international stock market diversity, small caps, and treasury bonds will help diversify S&P500-like positions, resulting in improved risk-adjusted return over time.

## Usage
Create a `.env` file in the same directory with `api_key`, `secret_key`, and `paper` variables defined. The first two values are provided by Alpaca when you create a free account. Their paper trading account requires no deposits.

You can decide to run this rebalancing script once a week, once a month, once a quarter, or other desired period. I would recommend starting with once a month to mitigate too much slippage since this script uses market orders (you lose a small percentage of the share price for every trade).

If you don't want to manually run the script periodically, you can set a cronjob to run it or create a simple python Docker container. I may work on that next.

## Future Works
- Dockerfile with environment variable for rebalancing conditions/frequency.
- Try out Alpaca's rebalancing API
- Improve logging format
- Implement live stream logging for trade confirmation