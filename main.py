import math, os
from dotenv import load_dotenv

from datetime import datetime

import alpaca
from alpaca.trading.client import *
from alpaca.trading.requests import *
from alpaca.common.exceptions import APIError

#import nest_asyncio

pf_allocs = {
    'VOO': 0.25,
    'AVUV': 0.25,
    'VEA': 0.1,
    'AVDV': 0.1,
    'VWO': 0.1,
    'DGS': 0.1,
    'EDV': 0.1
}
pf_symbols = set(pf_allocs.keys())
pf_symbols

def get_env():
    load_dotenv()
    return os.getenv('api_key'), os.getenv('secret_key'), os.getenv('paper')

def get_client(api_key, secret_key, paper):
    # for testing only
    trade_api_url = None
    trade_api_wss = None
    data_api_url = None
    stream_data_wss = None

    trade_client = TradingClient(
        api_key=api_key, secret_key=secret_key,
        paper=paper, url_override=trade_api_url
    )
    return trade_client

def set_settings(trade_client):
    acct_config = trade_client.get_account_configurations()
    req = acct_config
    req.fractional_trading = True
    req.max_margin_multiplier = '1'
    acct_config_new = trade_client.set_account_configurations(req)
    return acct_config_new

def close_non_portfolio(trade_client, pf_symbols):
    positions = trade_client.get_all_positions()
    current_symbols = [pos.symbol for pos in trade_client.get_all_positions()]
    closed = []
    for symbol in current_symbols:
        if symbol not in pf_symbols:
            #print(f'{symbol} not in portfolio, will be liquidated')
            closed.append(symbol)
            res = trade_client.close_position(symbol)
    return closed

def set_portfolio(trade_client, pf_allocs):
    adjustments = []
    acct = trade_client.get_account()
    for symbol in pf_allocs:
        # shouldn't happen if max margin is set to '1'
        if float(acct.cash) < 0:
            raw_alloc = pf_allocs[symbol]*(float(acct.portfolio_value) + float(acct.cash))
        else:
            raw_alloc = pf_allocs[symbol]*(float(acct.portfolio_value))
        try:
            cur_alloc = float(trade_client.get_open_position(symbol_or_asset_id=symbol).market_value)
        except:
            cur_alloc = 0
        adj_alloc = round(raw_alloc - cur_alloc, 2)
        # notional (fractional) orders must be at least 1.0
        if adj_alloc >= 1.0:
            order_side = OrderSide.BUY
        elif adj_alloc <= -1.0:
            order_side = OrderSide.SELL
        # all orders must be positive
        # should only trigger due to rounding off by 0.01 or price fluctuations while script is running
        if abs(adj_alloc) > float(acct.cash):
            adj_alloc = float(acct.cash)
        if adj_alloc < 1.0:
            continue
        adjustments.append([symbol, raw_alloc, cur_alloc, adj_alloc, order_side])
        req = MarketOrderRequest(
            symbol = symbol,
            notional = adj_alloc,
            side = order_side,
            type = OrderType.MARKET,
            time_in_force = TimeInForce.DAY,
        )
        res = trade_client.submit_order(req)
    return adjustments

def create_log(closed, adjustments):
    logname = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(logname+'.txt', 'w') as logfile:
        to_write = []
        to_write.append('The following positions were closed:\n')
        to_write.append('\n'.join(closed))
        to_write.append('\nThe following portfolio positions were adjusted:\n')
        to_write.append('symbol, raw_alloc, cur_alloc, adj_alloc, order_side')
        for adjustment in adjustments:
            to_write.append(', '.join([str(field) for field in adjustment]))
            to_write.append('\n')
        logfile.writelines(to_write)

def main():
    #nest_asyncio.apply()
    api_key, secret_key, paper = get_env()
    trade_client = get_client(api_key, secret_key, paper)
    acct_config_new = set_settings(trade_client)
    closed = close_non_portfolio(trade_client, pf_symbols)
    adjustments = set_portfolio(trade_client, pf_allocs)
    create_log(closed, adjustments)

if __name__ == '__main__':
    main()