import math, os, csv, time
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

import alpaca
from alpaca.trading.client import *
from alpaca.trading.requests import *
from alpaca.common.exceptions import APIError

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

def get_env():
    load_dotenv()
    return os.getenv('api_key'), os.getenv('secret_key'), os.getenv('paper')

def get_client(api_key, secret_key, paper):
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
            cur_alloc = trade_client.get_open_position(symbol_or_asset_id=symbol).market_value
            closed.append(
                {
                    'symbol': symbol,
                    'raw_alloc': 0,
                    'cur_alloc': cur_alloc,
                    'adj_alloc': cur_alloc,
                    'order_side': OrderSide.SELL
                }
            )
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
        if abs(adj_alloc) > float(acct.cash):
            adj_alloc = float(acct.cash)
        if adj_alloc < 1.0:
            continue
        adjustments.append(
            {
                'symbol': symbol,
                'raw_alloc': raw_alloc,
                'cur_alloc': cur_alloc,
                'adj_alloc': adj_alloc,
                'order_side': order_side
            }
        )
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
    row_dicts = closed+adjustments
    logname = datetime.now(
        tz=ZoneInfo('America/New_York')
    ).strftime("%Y%m%d-%H%M%S") + f'-{len(row_dicts)}_trades'

    try:
        os.mkdir('logs')
    except FileExistsError:
        print('Directory already exists')

    full_logname = 'logs/'+logname+'.csv'
    with open(full_logname, 'w', newline='') as logfile:
        fieldnames = ['symbol', 'raw_alloc', 'cur_alloc', 'adj_alloc', 'order_side']
        writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        writer.writeheader()
        for row_dict in row_dicts:
            writer.writerow(row_dict)

    print(f'Log available at {full_logname}')
    return full_logname

def check_orders(trade_client, symbols):
    req = GetOrdersRequest(
        status = QueryOrderStatus.OPEN,
        symbols = symbols
    )
    open_orders = trade_client.get_orders(req)
    while len(open_orders) > 0:
        print(f'Waiting on {len(open_orders)} open orders')
        print([order.symbol for order in open_orders])
        time.sleep(5)
    print('Trades submitted')
    return

def main():
    api_key, secret_key, paper = get_env()
    trade_client = get_client(api_key, secret_key, paper)
    acct_config_new = set_settings(trade_client)
    closed = close_non_portfolio(trade_client, pf_symbols)
    adjustments = set_portfolio(trade_client, pf_allocs)
    full_logname = create_log(closed, adjustments)
    check_orders(trade_client, pf_symbols)

if __name__ == '__main__':
    main()