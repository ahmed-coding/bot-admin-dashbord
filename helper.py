
from config import *
from datetime import datetime
import pandas as pd
import ta
import decimal
from binance.client import Client
from decimal import Decimal, ROUND_DOWN


start_date='3 hours ago UTC'
analize_period=80

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
def fetch_binance_data(client,symbol, interval, limit):
    # klines =  client.get_historical_klines(symbol, interval, start_date)
    klines = client.get_klines(symbol=symbol, interval=interval, limit= limit)

    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'number_of_trades', 
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    data['close'] = data['close'].astype(float)
    return data[['close']]



def fetch_binance_futuer_data(client,symbol, interval, limit):
    # klines =  client.get_historical_klines(symbol, interval, start_date)
    klines = client.futures_klines(symbol=symbol, interval=interval, limit= limit)

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

def get_futuer_usdt_balance(client):
    futures_account_info = client.futures_account()

    # البحث عن الرصيد المتاح
    for asset in futures_account_info['assets']:
        if asset['asset'] == 'USDT':  # إذا كنت تتداول بعملة USDT
            available_balance = float(asset['availableBalance'])
            total_balance = float(asset['walletBalance'])
            print(f"الرصيد الإجمالي: {total_balance} USDT")
            print(f"الرصيد المتاح: {available_balance} USDT")
            
    return available_balance - 7

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
        


def should_open_trade(client,symbol,intervel, limit):
    data = fetch_binance_data(client, symbol, intervel, limit)
    
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
        

def should_close_trade(client,symbol):
    data = fetch_binance_data(client, symbol, Client.KLINE_INTERVAL_3MINUTE, start_date)
    
    # if data is None or len(data) < 20:
    #     print(f"بيانات غير كافية لـ {symbol}")
    #     return
    
    bol_h_band = bol_h(data)
    bol_l_band = bol_l(data)
    close_prices = data['close']

    # فتح صفقة شراء إذا اخترق السعر الحد السفلي
    if close_prices.iloc[-3] > bol_l_band.iloc[-3] and close_prices.iloc[-2] < bol_l_band.iloc[-2]:
        return False

    # إغلاق صفقة إذا اخترق السعر الحد العلوي
    if close_prices.iloc[-3] < bol_h_band.iloc[-3] and close_prices.iloc[-2] > bol_h_band.iloc[-2]:
        return True
    
    
    
    return False        
        




def should_open_futuer_trade(client,symbol):
    data = fetch_binance_futuer_data(client, symbol, Client.KLINE_INTERVAL_3MINUTE, start_date)
    
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
        

def should_open_futuer_trade(client,symbol,intervel, limit):
    data = fetch_binance_futuer_data(client, symbol, intervel, limit=limit)
    
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
        



def adjust_futuser_price_precision(client, symbol, price):
    # استرجاع معلومات الرمز
    symbol_info = client.get_symbol_info(symbol)
    for filter in symbol_info['filters']:
        if filter['filterType'] == 'PRICE_FILTER':
            tick_size = Decimal(filter['tickSize'])  # الحصول على أصغر وحدة سعرية
            price = (Decimal(price) // tick_size) * tick_size  # تقليص السعر ليتماشى مع tick_size
            return float(price)
    return price  # إذا لم يكن هناك filter لـ PRICE_FILTER


def adjust_futuer_quantity(client, symbol, quantity):
    step_size = get_futuer_lot_size(client, symbol)
    if step_size is None:
        return quantity
    # Adjust quantity to be a multiple of step_size
    precision = Decimal(str(step_size))
    quantity = Decimal(str(quantity))
    return float((quantity // precision) * precision)


def get_futuer_lot_size(client, symbol):
    symbol_info = client.get_symbol_info(symbol)
    for filter in symbol_info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            step_size = float(filter['stepSize'])
            return step_size
    return None

def get_open_positions_count(client):
    positions = client.futures_position_information()
    open_positions = [position for position in positions if float(position['positionAmt']) != 0.0]
    # print(f"عدد الصفقات المفتوحة حاليًا: {len(open_positions)}")

    return len(open_positions)

def get_futuer_active_trades(client):
    """
    استرجاع الرموز التي تحتوي على صفقات مفتوحة.
    """
    active_trades = set()
    positions = client.futures_position_information()
    for position in positions:
        symbol = position['symbol']
        position_amt = float(position['positionAmt'])  # الكمية المفتوحة
        if position_amt != 0:  # إذا كانت الكمية ليست صفراً، يعني أن هناك صفقة مفتوحة
            active_trades.add(symbol)
    return active_trades