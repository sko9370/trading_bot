#!/usr/bin/env python3

# https://github.com/alpacahq/alpaca-trade-api-python
import alpaca_trade_api as api

API_KEY = ''
SECRET_KEY = ''
BASE_URL = 'https://api.alpaca.markets'

alpaca = api.REST(API_KEY, SECRET_KEY, BASE_URL)

# allocations
# allocations are in decimal form, should not be greater than 1
# cash is not specified, it'll be the remaining allocation
target_allocation = {'VOO': 0.5, 'XYLD': 0.3, 'BST': 0.1}

def check_fractionable(ticker):
    return alpaca.get_asset(ticker).fractionable

def get_mid_price(ticker):
    mid = (alpaca.get_quotes(ticker, limit=1)[0].ap + alpaca.get_quotes(ticker, limit=1)[0].bp) / 2
    return mid

def get_current_allocation():
    positions = alpaca.list_positions()
    current_allocation = {}
    equity = float(alpaca.get_account().equity)
    for p in positions:
        current_allocation[p.symbol] = round(float(p.market_value) / equity, 4)
    return current_allocation

def clear_unallocated(target_allocation):
    for p in alpaca.list_positions():
        if p.symbol not in target_allocation:
            alpaca.submit_order(
                p.symbol,
                side='sell',
                qty=p.qty,
                time_in_force = 'day')
            print('Order submitted to sell {} shares of {} because not in the current allocation'.format(p.qty, p.symbol))

def get_allocation_diff(current_allocation, target_allocation):
    allocation_diff = {}
    for symbol in target_allocation.keys():
        if symbol not in current_allocation:
            allocation_diff[symbol] = target_allocation[symbol]
        else:
            allocation_diff[symbol] = target_allocation[symbol] - current_allocation[symbol]
    return allocation_diff

def check_rebalance_trigger(allocation_diff, trigger=0.05):
    for symbol, diff in allocation_diff.items():
        if abs(diff) >= trigger:
            print('Portfolio needs to be rebalanced: beyond {}% difference from targets'.format(trigger*100))
            return True
    print('Portfolio does not fulfill rebalance trigger')
    return False

def rebalance_diff(allocation_diff, trigger=0.05):
    equity = float(alpaca.get_account().equity)
    for symbol, diff in allocation_diff.items():
        if check_fractionable(symbol):
            if diff > 0:
                side = 'buy'
                amount = round(diff * equity)
            else:
                side = 'sell'
                amount = round(-diff * equity)
            if amount != 0:
                order = alpaca.submit_order(
                    symbol = symbol,
                    notional = amount,
                    side = side,
                    type = 'market',
                    time_in_force = 'day',
                )
                print('Order submitted to {} ${} of {} to adjust {}% to target_allocation.'.format(side, diff * equity, symbol, diff * 100))
        else:
            mid = get_mid_price(symbol)
            change = diff * equity
            shares = abs(round(change/mid))
            if diff > 0:
                side = 'buy'
            else:
                side = 'sell'
            if shares != 0:
                order = alpaca.submit_order(
                    symbol = symbol,
                    qty = shares,
                    side = side,
                    type = 'market',
                    time_in_force = 'day',
                )
                print('Order submitted to {} ${} of {} to adjust {}% to target_allocation.'.format(side, diff * equity, symbol, diff * 100))
            else:
                print('Rebalance needed but shares needed to buy rounds down to 0 due to {} being unfractionable.'.format(symbol))

def main():
    alpaca.cancel_all_orders()
    current_allocation = get_current_allocation()
    print('Current allocation: {}'.format(current_allocation))
    clear_unallocated(target_allocation)
    allocation_diff = get_allocation_diff(current_allocation, target_allocation)
    print('Allocation difference: {}'.format(allocation_diff))
    if check_rebalance_trigger(allocation_diff):
        rebalance_diff(allocation_diff)

    print()
    print('Current positions:')
    for p in alpaca.list_positions():
        print("{}: ${}".format(p.symbol, round(float(p.market_value), 2)))

if __name__ == '__main__':
    main()
