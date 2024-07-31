# Alpaca Trading Bot

## Setup
Use the included `requirements.txt` and run `pip install -r /path/to/requirements.txt`.

## Background
Alpaca released their v2 [API](https://github.com/alpacahq/alpaca-py) at some point after I created my first bot a few years ago. The 2024 version of my script updates the functions to use the latest API.

## Purpose
This bot simply rebalances the portfolio according to allocations set in the `pf_allocs` dictionary at the top of the script. The current portfolio is called the [Ginger Ale Portfolio](https://www.optimizedportfolio.com/ginger-ale-portfolio/), developed by John Williamson at Optimized Portfolio. In short, historical data shows that international stock market diversity, small caps, and treasury bonds will help diversify S&P500-like positions, resulting in improved risk-adjusted return over time.

## Usage
Create a `.env` file in the same directory with `api_key`, `secret_key`, and `paper` variables defined. The first two values are provided by Alpaca when you create a free account. Their paper trading account requires no deposits.

You can decide to run this rebalancing script once a week, once a month, once a quarter, or other desired period. I would recommend starting with once a month to mitigate too much slippage since this script uses market orders (you lose a small percentage of the share price for every trade).

If you don't want to manually run the script periodically, you can set a cronjob to run it or create a simple python Docker container. I may work on that next.

## References
- [alpaca-py example: stocks-trading-basic.ipynb](https://github.com/alpacahq/alpaca-py/blob/master/examples/stocks-trading-basic.ipynb)

## Future Works
- [ ] Develop solution for bug where market is not open, a sell/close order for non-portfolio position is submitted but not executed yet (taking up buying power), proper portfolio allocation cannot be completed because all buy orders cannot be submitted without full buying power
    - Enable margin to allow for order to go through during market close, but be precise enough to not actually use margin
    - Wait to submit orders until next market open, but need to wait for allocation calculations until market open as well
    - Will eventually resolve itself after multiple iterations if only portfolio positions are open, just show warning to rerun after market open
- [ ] Fix edge case where market is not open, orders are submitted, and then the script is run again; script needs to check for open orders first and cancel them selectively as necessary
- [ ] Dockerfile with environment variable for rebalancing conditions/frequency.
- [ ] Try out Alpaca's rebalancing API
- [x] Improve logging format
- [ ] Implement live stream logging for trade confirmation