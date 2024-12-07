
# from backtest import calculate_rsi
from config import *
from datetime import datetime
import pandas as pd
import ta
import decimal
from binance.client import Client
from decimal import Decimal, ROUND_DOWN
import request_load

start_date='3 hours ago UTC'
analize_period=80
rsi_analize_period = 8

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
            
    return available_balance / 3

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
    استرجاع الصفقات المفتوحة على Binance Futures
    """
    positions = client.futures_position_information()  # جلب جميع المراكز المفتوحة
    active_trades = {}  # Dictionary للاحتفاظ بالمعلومات المفتوحة

    for position in positions:
        symbol = position['symbol']
        position_amt = float(position['positionAmt'])  # الكمية المفتوحة
        if position_amt != 0:  # إذا كانت الكمية ليست صفرًا، فهذا يعني وجود صفقة مفتوحة
            active_trades[symbol] = {
                "symbol": symbol,
                "amount": position_amt,
                "entryPrice": float(position['entryPrice']),
                # "unrealizedProfit": float(position['unrealizedProfit']),
                # "leverage": int(position['leverage']),
                "markPrice": float(position['markPrice']),
            }
    return active_trades

def update_futuer_active_trades(client):
    """
    استرجاع الصفقات المفتوحة على Binance Futures وتحديث الحالة في Django.
    """
    active_trade = request_load.get_futuer_open_trad()
    positions = client.futures_position_information()  # جلب جميع المراكز المفتوحة
    for symbol, trade in list(active_trade.items()):
        is_open = False
        # print(f"Checking symbol: {symbol}")
        for position in positions:
            acive_symbol = position['symbol']
            position_amt = float(position['positionAmt'])  # الكمية المفتوحة
            # print(f"Position symbol: {acive_symbol}, Position amount: {position_amt}")
            
            # تحقق دقيق من الصفقات المفتوحة
            if position['symbol'] == symbol and position_amt != 0:
                is_open = True
                # print(f"Trade is open for {acive_symbol}")
                break
        
        # إذا لم يتم العثور على الصفقة، قم بتحديث الحالة بأنها مغلقة
        if not is_open:
            update_status = request_load.close_trad(trade)
            print(f"Trade closed for {symbol}")


def get_price_precision(client, symbol):
    resp = client.get_exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            # نبحث عن الفلتر المناسب لسعر السوق
            for filter in elem['filters']:
                if filter['filterType'] == 'PRICE_FILTER':
                    # نعيد الدقة الخاصة بالسعر
                    tick_size = filter['tickSize']
                    return len(tick_size.split('1')[1]) if '1' in tick_size else 0

def get_qty_precision(client, symbol):
    resp = client.get_exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            # نبحث عن الفلتر المناسب للكمية
            for filter in elem['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    # نعيد الدقة الخاصة بالكمية بناءً على stepSize
                    step_size = filter['stepSize']
                    return len(step_size.split('1')[1]) if '1' in step_size else 0


def get_precision(client:Client,symbol):
    resp = client.get_symbol_info(symbol=symbol)
            # نبحث عن الفلتر المناسب لسعر السوق
    return int(resp['baseAssetPrecision'])
            

            # for filter in elem['filters']:
            #     if filter['filterType'] == 'PRICE_FILTER':
            #         # نعيد الدقة الخاصة بالسعر
            #         tick_size = filter['tickSize']
            #         return len(tick_size.split('1')[1]) if '1' in tick_size else 0


# حساب مؤشر RSI
def calculate_rsi(prices, period=14):
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi


def fetch_ris_binance_data(client, symbol, intervel , limit):
    
    klines = client.get_klines(symbol=symbol, interval=intervel, limit=limit)
    
    closing_prices = [float(kline[4]) for kline in klines]

    return calculate_rsi(closing_prices,limit)


def should_open_futuer_rsi_trade(client,symbol,intervel, limit,rsi_limit):
    bollinger_data = fetch_binance_futuer_data(client, symbol, intervel, limit=limit)
    rsi = fetch_ris_binance_data(client, symbol, intervel, rsi_limit)
    # if data is None or len(data) < 20:
    #     print(f"بيانات غير كافية لـ {symbol}")
    #     return
    
    bol_h_band = bol_h(bollinger_data)
    bol_l_band = bol_l(bollinger_data)
    close_prices = bollinger_data['close']

    # فتح صفقة شراء إذا اخترق السعر الحد السفلي
    # if rsi > 25 and rsi < 45:

    # if close_prices.iloc[-3] > bol_l_band.iloc[-3] and close_prices.iloc[-2] < bol_l_band.iloc[-2] and  rsi < 40 :
    if close_prices.iloc[-3] > bol_l_band.iloc[-3] and close_prices.iloc[-2] < bol_l_band.iloc[-2] and  rsi < 40 :

    
        return True

    # إغلاق صفقة إذا اخترق السعر الحد العلوي
    # if close_prices.iloc[-3] < bol_h_band.iloc[-3] and close_prices.iloc[-2] > bol_h_band.iloc[-2] and  rsi > 25 and rsi < 45:
    # if rsi > 70:

    #     return True
    
    
    return False        
        



def detect_bos(data):
    """
    اكتشاف كسر الهيكل (BOS) في بيانات Pandas.
    """
    data['BOS'] = (data['Close'] > data['High'].shift(1)) | (data['Close'] < data['Low'].shift(1))
    return data['BOS'].iloc[-1]  # استخدام آخر قيمة BOS



def fetch_ict_data(client,symbol, interval, limit=500):
    """
    جلب بيانات الشموع التاريخية من Binance.
    """
    candles = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(candles, columns=[
        'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close_Time', 'Quote_Asset_Volume', 'Number_Of_Trades',
        'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore'
    ])
    df['Open'] = df['Open'].astype(float)
    df['High'] = df['High'].astype(float)
    df['Low'] = df['Low'].astype(float)
    df['Close'] = df['Close'].astype(float)
    df['Volume'] = df['Volume'].astype(float)
    df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
    return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume']]




def rsi_ict_should_open_futuer_trade(client, symbol, interval, limit, rsi_period):
    """
    التحقق مما إذا كانت هناك فرصة لفتح صفقة بناءً على استراتيجية RSI و BOS.
    
    Args:
        client: كائن العميل للتواصل مع Binance API.
        symbol (str): رمز الزوج (مثل BTCUSDT).
        interval (str): الإطار الزمني (مثل 5m، 15m).
        limit (int): عدد الشموع المطلوبة لتحليل BOS.
        rsi_period (int): فترة RSI المستخدمة في الحساب.
        
    Returns:
        bool: True إذا كانت الشروط متوفرة لفتح صفقة، False إذا لم تكن.
    """
    # جلب البيانات المطلوبة
    data = fetch_ict_data(client, symbol, interval, limit=limit)
    rsi = fetch_ris_binance_data(client, symbol, interval, rsi_period)
    
    # التحقق من كفاية البيانات
    if data is None or len(data) < limit:
        # print(f"⚠️ بيانات غير كافية لتحليل {symbol}")
        return False

    # التحقق من وجود إشارة BOS
    bos = detect_bos(data)
    if bos and rsi < 40:
        return True
    
    return False
