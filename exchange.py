from binance.client import Client, BinanceAPIException
import time
import telegrambot
import math
import config


binance_key = config.authenticate._binance_key
binance_secret = config.authenticate._binance_secret


client = Client(binance_key, binance_secret)


def compute_position_size(boolprint):
    ratio = config.position_ratio
    leverage = config.leverage
    curr_doge_price = float(client.get_symbol_ticker(symbol="DOGEUSDT")['price'])
    future_USD_balance = float(client.futures_account_balance()[1]['balance'])
    position_size_doge = math.floor(ratio * leverage * future_USD_balance / curr_doge_price)

    if boolprint:
        # Send to Telegram Bot
        telegrambot.send_msg('Initial USDT future wallet: ' + str(future_USD_balance) + ' USDT \n' \
                             'Bought: ' + str(position_size_doge) + ' DOGE \n' \
                             'At price: ' + str(curr_doge_price) + ' DOGE / USD \n' \
                             'Leverage: ' + str(leverage) + ' times \n')
    return position_size_doge


def get_binance_tickers():
    info = client.get_exchange_info()
    margin_list = [{symbol['baseAsset']: symbol['symbol']} for symbol in info['symbols'] if symbol['quoteAsset']=='USDT' and symbol['isMarginTradingAllowed']]
    spot_list = [{symbol['baseAsset']: symbol['symbol']} for symbol in info['symbols'] if symbol['quoteAsset']=='USDT' and symbol['isSpotTradingAllowed']]
    return margin_list, spot_list


def set_trailing_stop_loss(ticker):
    callbackRate = config.callbackRate
    position_size = compute_position_size(boolprint=False)
    client.futures_create_order(
        symbol= str(ticker)+'USDT',
        side='SELL',
        type='TRAILING_STOP_MARKET',
        callbackRate = callbackRate,
        quantity=position_size)


def set_market_order(ticker):
    position_size = compute_position_size(boolprint=True)
    try:
        client.futures_create_order(symbol=str(ticker)+'USDT', side='BUY', type='MARKET', quantity=position_size)

    except BinanceAPIException as e:
        # error handling goes here
        print(e)