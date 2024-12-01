
from config import *
from datetime import datetime
import pandas as pd
import ta
import decimal


start_date='3 hours ago UTC'

def get_klines(client, symbol, interval, start_date):
    # klines = client.get_historical_klines(symbol, interval, start_date)
    return  client.get_historical_klines(symbol, interval, start_date)



# setup Bollinger Bands
def bol_h(df):
    return ta.volatility.BollingerBands(pd.Series(df['close'])).bollinger_hband() 

def bol_l(df):
    return ta.volatility.BollingerBands(pd.Series(df['close'])).bollinger_lband() 




# دالة ضبط الكمية بناءً على دقة السوق
def adjust_quantity(client,symbol, quantity):
    step_size = get_lot_size(client,symbol)
    if step_size is None:
        return quantity
    # Adjust quantity to be a multiple of step_size
    precision = decimal.Decimal(str(step_size))
    quantity = decimal.Decimal(str(quantity))
    return float((quantity // precision) * precision)

def get_lot_size( client,symbol):
    exchange_info = client.get_symbol_info(symbol)
    for filter in exchange_info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            step_size = float(filter['stepSize'])
            return step_size
    return None



def check_bnb_balance(client,min_bnb_balance=0.0001):  # تقليل الحد الأدنى المطلوب
    # تحقق من رصيد BNB للتأكد من تغطية الرسوم
    account_info = client.get_asset_balance(asset='BNB')
    if account_info:
        bnb_balance = float(account_info['free'])
        return bnb_balance >= min_bnb_balance
    return False

start_date='3 hours ago UTC'

# دالة لجلب البيانات من Binance
def fetch_binance_data(client,symbol, interval, start_date):
    # klines =  client.get_historical_klines(symbol, interval, start_date)
    klines = client.get_klines(symbol=symbol, interval=interval, limit=60)

    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'number_of_trades', 
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    data['close'] = data['close'].astype(float)
    return data[['close']]

# ملف CSV لتسجيل التداولات


def get_usdt_balance(client):

    return float(client.get_asset_balance(asset='USDT')['free'])


def should_open_trade(client,symbol):
    data = fetch_binance_data(client, symbol, Client.KLINE_INTERVAL_3MINUTE, start_date)
    
    # if data is None or len(data) < 20:
    #     print(f"بيانات غير كافية لـ {symbol}")
    #     return
    
    bol_h_band = bol_h(data)
    bol_l_band = bol_l(data)
    close_prices = data['close']

    # فتح صفقة شراء إذا اخترق السعر الحد السفلي
    if close_prices.iloc[-3] > bol_l_band.iloc[-3] and close_prices.iloc[-2] < bol_l_band.iloc[-2]:
        return True

    # إغلاق صفقة إذا اخترق السعر الحد العلوي
    if close_prices.iloc[-3] < bol_h_band.iloc[-3] and close_prices.iloc[-2] > bol_h_band.iloc[-2]:
        return False
    
    
    return False        
        





