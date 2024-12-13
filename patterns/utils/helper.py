
# from backtest import calculate_rsi
from utils.config import *
from datetime import datetime
import pandas as pd
import ta
import decimal
from binance.client import Client
from binance.exceptions import BinanceAPIException
from decimal import Decimal, ROUND_DOWN
import utils.request_load as request_load

start_date='3 hours ago UTC'
analize_period=80
rsi_analize_period = 8


def get_futuer_top_symbols(client, klines_interval,limit=20, excluded_symbols=[],black_list=[]):
    tickers = client.futures_ticker()
    exchange_info = client.futures_exchange_info()  # جلب معلومات التداول
    valid_symbols = {info['symbol'] for info in exchange_info['symbols']}  # الرموز المسموح بها
    sorted_tickers = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
    top_symbols = []
    
    for ticker in sorted_tickers:
        if ticker['symbol'].endswith("USDT") and ticker['symbol'] in valid_symbols and ticker['symbol'] not in excluded_symbols and ticker['symbol'] not in black_list :  # تحقق من صلاحية الرمز
            try:
                klines = client.get_klines(symbol=ticker['symbol'], interval=klines_interval, limit=limit)
                if klines is None or klines == []:
                    continue
                top_symbols.append(ticker['symbol'])
                if len(top_symbols) >= limit:
                    break
            except BinanceAPIException as e:
                # print(f"خطأ في جلب بيانات {ticker['symbol']}: {e}")
                excluded_symbols.append(ticker['symbol'])
    return top_symbols


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
            
    return available_balance / 2

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



# حساب مؤشر RSI
def ict_calculate_rsi(prices, period=14):
    """
    حساب مؤشر RSI بناءً على فترة محددة.
    
    Args:
        prices (list): قائمة بأسعار الإغلاق.
        period (int): فترة الحساب (default: 14).
    
    Returns:
        list: قائمة بقيم RSI لكل فترة.
    """
    if len(prices) < period + 1:
        raise ValueError("عدد البيانات أقل من الفترة المطلوبة لحساب RSI.")
    
    # حساب التغيرات (Deltas)
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    
    # المكاسب والخسائر الأولية
    gains = [max(delta, 0) for delta in deltas]
    losses = [abs(min(delta, 0)) for delta in deltas]
    
    # حساب متوسط المكاسب والخسائر الأولية
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # قائمة لقيم RSI
    rsis = []
    
    # البدء من الفترة بعد حساب المتوسطات الأولية
    for i in range(period, len(prices) - 1):
        gain = gains[i]
        loss = losses[i]
        
        # المتوسطات الملساء
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        
        # حساب RSI
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        rsis.append(rsi)
    
    return rsis


def fetch_ris_binance_data(client, symbol, intervel , limit):
    
    klines = client.get_klines(symbol=symbol, interval=intervel, limit=limit +1)
    
    closing_prices = [float(kline[4]) for kline in klines]

    return calculate_rsi(closing_prices,limit)




def fetch_ict_ris_binance_data(client, symbol, interval, period=14, limit=500):
    """
    جلب بيانات RSI بناءً على أسعار الإغلاق.
    
    Args:
        client: كائن العميل للتواصل مع Binance API.
        symbol (str): رمز الزوج (مثل BTCUSDT).
        interval (str): الإطار الزمني (مثل 5m، 15m).
        period (int): فترة حساب RSI.
        limit (int): عدد الشموع المطلوبة.
        
    Returns:
        float: قيمة RSI الأخيرة.
    """
    # جلب بيانات الشموع
    candles = client.futures_klines(symbol=symbol, interval=interval, limit=limit + period)
    closing_prices = [float(candle[4]) for candle in candles]
    
    # حساب RSI
    rsi_values = ict_calculate_rsi(closing_prices, period=period)
    
    # إعادة آخر قيمة RSI
    return rsi_values[-1] if rsi_values else None



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
        



def detect_bos(data, is_sell=False):
    """
    اكتشاف كسر الهيكل (BOS) في بيانات Pandas.
    
    Parameters:
        data (pd.DataFrame): البيانات التي تحتوي على الأعمدة Open, High, Low, Close.
        is_sell (bool): إذا كان True يتم فحص كسر الهيكل للبيع، إذا كان False يتم فحص كسر الهيكل للشراء.
    
    Returns:
        bool: True إذا كان هناك كسر هيكل بناءً على الاتجاه المحدد، False إذا لم يكن هناك كسر.
    """
    if len(data) < 2:
        print("⚠️ البيانات غير كافية لتحليل BOS")
        return False  # لا توجد بيانات كافية
    
    if is_sell:
        # كسر هيكل هبوطي: الإغلاق أقل من القاع السابق، والإغلاق أقل من الإغلاق السابق
        data['BOS'] = (data['Close'] < data['Low'].shift(1)) & (data['Close'] < data['Close'].shift(1))
    else:
        # كسر هيكل صعودي: الإغلاق أعلى من القمة السابقة، والإغلاق أعلى من الإغلاق السابق
        data['BOS'] = (data['Close'] > data['High'].shift(1)) & (data['Close'] > data['Close'].shift(1))
    
    # إرجاع النتيجة لأحدث صف فقط
    return data['BOS'].iloc[-1]


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
    rsi = fetch_ict_ris_binance_data(client, symbol, interval, rsi_period)
    
    # التحقق من كفاية البيانات
    if data is None or len(data) < limit:
        # print(f"⚠️ بيانات غير كافية لتحليل {symbol}")
        return False

    # التحقق من وجود إشارة BOS
    bos = detect_bos(data)
    if bos and  rsi < 40:
        return True
    
    return False


# def getTickerPricePrecision(client, symbol):
#     resp = client.exchange_info()['symbols']
#     for elem in resp:
#         if elem['symbol'] == symbol:
#             return elem['pricePrecision']

# def getTickerQtyPrecision(client, symbol):
#     resp = client.exchange_info()['symbols']
#     for elem in resp:
#         if elem['symbol'] == symbol:
#             return elem['quantityPrecision']
        
        
def Pric_Precision(client, price, symbol):

    return str(round(float(price),[x['pricePrecision'] for x in client.futures_exchange_info()['symbols'] if x['symbol'] == symbol][0]))


def QUN_Precision(client,quantity, symbol):
    return str(round(float(quantity),[x['quantityPrecision'] for x in client.futures_exchange_info()['symbols'] if x['symbol'] == symbol][0]))





# -------------------- الانماط الصاعدة----------

"""
    قائمة الانماط الصاعدة 
    1-     اكتشاف نمط القاع المزدوج في البيانات.
    2-     اكتشاف نمط الرأس والكتفين المقلوب.
    3-     كشف نمط المطرقة (Hammer)
    4-     كشف نمط الابتلاع الشرائي (Bullish Engulfing)
    5-    كشف نمط نجمة الصباح (Morning Star)
    5-    كشف نمط اختراق الخط (Piercing Line)
    6-     كشف نمط الجنود الثلاثة البيض (Three White Soldiers)
    7-     كشف نمط القاعدة الكبيرة.
    8-     كشف نمط الاندفاع الكبير.
    9-     كشف نمط الاختراق الصاعد.
    10-     كشف نمط الكوب والعروة.
    11-     كشف نمط العلم الصاعد.
"""

def detect_double_bottom(data):
    """
    اكتشاف نمط القاع المزدوج في البيانات.
    
    Args:
        data (DataFrame): بيانات الشموع (Pandas DataFrame).
    
    Returns:
        bool: True إذا تم اكتشاف القاع المزدوج، False إذا لم يتم.
    """
    if len(data) < 5:  # التأكد من وجود بيانات كافية
        return False
    
    lows = data['Low']
    # التحقق من القاعين المتساويين نسبياً
    if (
        lows.iloc[-3] < lows.iloc[-4] and  # القاع الأول أقل من السابق
        abs(lows.iloc[-3] - lows.iloc[-1]) < (min(lows[-5:]) * 0.01) and  # القاع الأول يساوي القاع الثاني
        data['Close'].iloc[-1] > data['High'].iloc[-2]  # الإغلاق بعد القاع الثاني أعلى من القمة بين القاعين
    ):
        return True
    
    return False


def detect_inverse_head_and_shoulders(data):
    """
    اكتشاف نمط الرأس والكتفين المقلوب.
    
    Args:
        data (DataFrame): بيانات الشموع (Pandas DataFrame).
    
    Returns:
        bool: True إذا تم اكتشاف النمط، False إذا لم يتم.
    """
    if len(data) < 7:  # التأكد من وجود بيانات كافية
        return False
    
    lows = data['Low']
    highs = data['High']
    # تحقق من الرأس والكتفين
    if (
        lows.iloc[-5] > lows.iloc[-3] and  # الكتف الأيسر
        lows.iloc[-3] < lows.iloc[-1] and  # الرأس
        highs.iloc[-3] > highs.iloc[-5] and highs.iloc[-3] > highs.iloc[-1]  # الرأس أعلى
    ):
        return True
    
    return False




def detect_hammer(data):
    """
    كشف نمط المطرقة (Hammer)
    """
    open_price = data['Open'].iloc[-1]
    close_price = data['Close'].iloc[-1]
    high_price = data['High'].iloc[-1]
    low_price = data['Low'].iloc[-1]

    body = abs(close_price - open_price)
    lower_shadow = min(open_price, close_price) - low_price
    upper_shadow = high_price - max(open_price, close_price)

    return (
        body < (high_price - low_price) * 0.25 and
        lower_shadow > body * 3 and
        upper_shadow < body * 0.1
    )



def detect_bullish_engulfing(data):
    """
    كشف نمط الابتلاع الشرائي (Bullish Engulfing)
    """
    open_price_1 = data['Open'].iloc[-2]
    close_price_1 = data['Close'].iloc[-2]
    open_price_2 = data['Open'].iloc[-1]
    close_price_2 = data['Close'].iloc[-1]

    return (
        close_price_1 < open_price_1 and  # الشمعة الأولى هابطة
        open_price_2 < close_price_1 and  # افتتاح الشمعة الثانية أقل من إغلاق الأولى
        close_price_2 > open_price_1      # إغلاق الشمعة الثانية أعلى من افتتاح الأولى
    )


def detect_morning_star(data):
    """
    كشف نمط نجمة الصباح (Morning Star)
    """
    open_price_1 = data['Open'].iloc[-3]
    close_price_1 = data['Close'].iloc[-3]
    open_price_2 = data['Open'].iloc[-2]
    close_price_2 = data['Close'].iloc[-2]
    open_price_3 = data['Open'].iloc[-1]
    close_price_3 = data['Close'].iloc[-1]

    return (
        close_price_1 < open_price_1 and  # الشمعة الأولى هابطة
        abs(close_price_2 - open_price_2) < (close_price_1 - open_price_1) * 0.5 and  # الشمعة الثانية صغيرة
        close_price_3 > open_price_1      # الشمعة الثالثة تغلق فوق افتتاح الأولى
    )


def detect_piercing_line(data):
    """
    كشف نمط اختراق الخط (Piercing Line)
    """
    open_price_1 = data['Open'].iloc[-2]
    close_price_1 = data['Close'].iloc[-2]
    open_price_2 = data['Open'].iloc[-1]
    close_price_2 = data['Close'].iloc[-1]

    return (
        close_price_1 < open_price_1 and  # الشمعة الأولى هابطة
        open_price_2 < close_price_1 and  # الشمعة الثانية تفتح أدنى من إغلاق الأولى
        close_price_2 > (open_price_1 + close_price_1) / 2  # إغلاق الشمعة الثانية أعلى منتصف الأولى
    )


def detect_three_white_soldiers(data):
    """
    كشف نمط الجنود الثلاثة البيض (Three White Soldiers)
    """
    close_1 = data['Close'].iloc[-3]
    open_1 = data['Open'].iloc[-3]
    close_2 = data['Close'].iloc[-2]
    open_2 = data['Open'].iloc[-2]
    close_3 = data['Close'].iloc[-1]
    open_3 = data['Open'].iloc[-1]

    return (
        close_1 > open_1 and  # الشمعة الأولى صاعدة
        close_2 > open_2 and  # الشمعة الثانية صاعدة
        close_3 > open_3 and  # الشمعة الثالثة صاعدة
        open_2 > close_1 and  # الشمعة الثانية تفتح فوق إغلاق الأولى
        open_3 > close_2      # الشمعة الثالثة تفتح فوق إغلاق الثانية
    )
    
    
def detect_large_base(data):
    """
    كشف نمط القاعدة الكبيرة.
    """
    lows = data['Low']
    highs = data['High']
    return (
        lows.iloc[-5:].min() > lows.iloc[-6] and  # قاعدة قوية
        highs.iloc[-1] > highs.iloc[-2] and      # اختراق القمة السابقة
        highs.iloc[-1] > highs.iloc[-3]
    )



def detect_big_move_up(data):
    """
    كشف نمط الاندفاع الكبير.
    """
    close_1 = data['Close'].iloc[-2]
    close_2 = data['Close'].iloc[-1]
    return (
        close_2 > close_1 * 1.05  # ارتفاع كبير بنسبة 5% أو أكثر
    )


def detect_bullish_breakout(data):
    """
    كشف نمط الاختراق الصاعد.
    """
    close_1 = data['Close'].iloc[-2]
    close_2 = data['Close'].iloc[-1]
    high_1 = data['High'].iloc[-2]
    return (
        close_2 > high_1 * 1.01 and  # اختراق القمة السابقة بنسبة 1% أو أكثر
        close_2 > close_1
    )


def detect_cup_and_handle(data):
    """
    كشف نمط الكوب والعروة.
    """
    if len(data) < 15:  # التحقق من بيانات كافية
        return False
    
    highs = data['High']
    lows = data['Low']
    # تحقق من شكل الكوب والعروة
    return (
        highs.iloc[-10:].max() == highs.iloc[-15] and  # الكوب
        lows.iloc[-10:].min() < lows.iloc[-15] and      # القاع
        highs.iloc[-1] > highs.iloc[-15]               # اختراق العروة
    )

def detect_bullish_flag(data):
    """
    كشف نمط العلم الصاعد.
    """
    if len(data) < 10:  # التحقق من بيانات كافية
        return False
    
    highs = data['High']
    lows = data['Low']
    return (
        highs.iloc[-5:].mean() < highs.iloc[-10:].mean() and  # التصحيح
        highs.iloc[-1] > highs.iloc[-10:].max()              # الاختراق
    )


def detect_evening_star(data):
    """
    تم تغيير النمط من هبوطي الى صعودي
    كشف نمط نجمة المساء (Evening Star)
    """
    open_price_1 = data['Open'].iloc[-3]
    close_price_1 = data['Close'].iloc[-3]
    open_price_2 = data['Open'].iloc[-2]
    close_price_2 = data['Close'].iloc[-2]
    open_price_3 = data['Open'].iloc[-1]
    close_price_3 = data['Close'].iloc[-1]

    return (
        close_price_1 > open_price_1 and  # الشمعة الأولى صاعدة
        close_price_2 > close_price_1 and  # الشمعة الثانية صاعدة أكثر
        close_price_3 < (open_price_1 + close_price_1) / 2 and  # الشمعة الثالثة تغلق تحت منتصف الأولى
        close_price_3 < open_price_3  # الشمعة الثالثة هابطة
    )



# -------------------- الانماط الهابطة----------
"""
    قائمة الانماط الهابطة 
    1- كشف نمط الشهاب (Shooting Star)
    2-     كشف نمط الابتلاع البيعي (Bearish Engulfing)
    3-     كشف نمط القمم المزدوجة (Double Top)
    4-     كشف نمط الرأس والكتفين (Head and Shoulders)
    5-     كشف نمط المطرقة المقلوبة (Inverted Hammer)
    5-     كشف نمط نجمة المساء (Evening Star)
    6-     كشف نمط القاعدة الكبيرة الهابطة.
    7-     كشف نمط الاندفاع الكبير الهابط.
    8-     كشف نمط الاختراق الهابط.
    9-     كشف نمط المتاجرة الهابطة في الاتجاه.
    10-     كشف نمط العلم الهابط.
    11-     كشف نمط القمة الثلاثية.    
"""

def detect_shooting_star(data):
    """
    كشف نمط الشهاب (Shooting Star)
    """
    open_price = data['Open'].iloc[-1]
    close_price = data['Close'].iloc[-1]
    high_price = data['High'].iloc[-1]
    low_price = data['Low'].iloc[-1]
    
    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    return (
        body < (high_price - low_price) * 0.3 and
        upper_shadow > body * 2 and
        lower_shadow < body * 0.2
    )


def detect_bearish_engulfing(data):
    """
    كشف نمط الابتلاع البيعي (Bearish Engulfing)
    """
    open_price_1 = data['Open'].iloc[-2]
    close_price_1 = data['Close'].iloc[-2]
    open_price_2 = data['Open'].iloc[-1]
    close_price_2 = data['Close'].iloc[-1]

    return (
        close_price_1 > open_price_1 and
        open_price_2 > close_price_1 and
        close_price_2 < open_price_1
    )


def detect_double_top(data):
    """
    كشف نمط القمم المزدوجة (Double Top)
    """
    highs = data['High']
    return (
        highs.iloc[-2] == max(highs.iloc[-5:]) and
        highs.iloc[-3] == max(highs.iloc[-5:]) and
        highs.iloc[-2] == highs.iloc[-3]
    )


def detect_head_and_shoulders(data):
    """
    كشف نمط الرأس والكتفين (Head and Shoulders)
    """
    
    if len(data) < 7:  # التحقق من بيانات كافية
        return False

    highs = data['High']
    lows = data['Low']  # تعريف القيعان

    neckline = lows.iloc[-3:].mean()  # خط العنق
    return (
        highs.iloc[-4] < highs.iloc[-3] and  # الكتف الأول
        highs.iloc[-3] > highs.iloc[-2] and  # الرأس
        highs.iloc[-2] < highs.iloc[-3] and  # الكتف الثاني
        lows.iloc[-1] < neckline  # كسر خط العنق
    )


def detect_inverted_hammer(data):
    """
    كشف نمط المطرقة المقلوبة (Inverted Hammer)
    """
    open_price = data['Open'].iloc[-1]
    close_price = data['Close'].iloc[-1]
    high_price = data['High'].iloc[-1]
    low_price = data['Low'].iloc[-1]

    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    return (
        body < (high_price - low_price) * 0.3 and
        upper_shadow > body * 2 and
        lower_shadow < body * 0.2
    )



def detect_large_top(data):
    """
    كشف نمط القاعدة الكبيرة الهابطة.
    """
    highs = data['High']
    lows = data['Low']
    return (
        highs.iloc[-5:].max() < highs.iloc[-6] and  # قاعدة هابطة
        lows.iloc[-1] < lows.iloc[-2] and           # انخفاض كبير تحت القاع السابق
        lows.iloc[-1] < lows.iloc[-3]
    )


def detect_big_move_down(data):
    """
    كشف نمط الاندفاع الكبير الهابط.
    """
    close_1 = data['Close'].iloc[-2]
    close_2 = data['Close'].iloc[-1]
    return (
        close_2 < close_1 * 0.95  # انخفاض كبير بنسبة 5% أو أكثر
    )

def detect_bearish_breakout(data):
    """
    كشف نمط الاختراق الهابط.
    """
    close_1 = data['Close'].iloc[-2]
    close_2 = data['Close'].iloc[-1]
    low_1 = data['Low'].iloc[-2]
    return (
        close_2 < low_1 * 0.99 and  # اختراق القاع السابق بنسبة 1% أو أكثر
        close_2 < close_1
    )

def detect_bearish_trend(data):
    """
    كشف نمط المتاجرة الهابطة في الاتجاه.
    """
    close_1 = data['Close'].iloc[-5]
    close_2 = data['Close'].iloc[-1]
    return (
        close_2 < close_1 and  # إغلاق الشمعة الأخيرة أقل من الشمعة قبلها
        close_2 < data['Open'].iloc[-1]  # سعر الإغلاق أقل من سعر الافتتاح
    )

def detect_bearish_flag(data):
    """
    كشف نمط العلم الهابط.
    """
    if len(data) < 10:  # التحقق من بيانات كافية
        return False
    
    highs = data['High']
    lows = data['Low']
    return (
        lows.iloc[-5:].mean() > lows.iloc[-10:].mean() and  # التصحيح
        lows.iloc[-1] < lows.iloc[-10:].min()              # الكسر
    )


def detect_triple_top(data):
    """
    كشف نمط القمة الثلاثية.
    """
    highs = data['High']
    return (
        highs.iloc[-6] == highs.iloc[-4] and
        highs.iloc[-4] == highs.iloc[-2] and
        highs.iloc[-1] < highs.iloc[-2]  # انخفاض بعد القمم الثلاثة
    )



# ---------------------------------------------------

def pattern_should_open_trade(client, symbol, interval, limit, rsi_period):
    """
    التحقق مما إذا كانت هناك فرصة لفتح صفقة بناءً على RSI و BOS والأنماط.
    
    Returns:
        bool: True إذا كانت الشروط متوفرة لفتح صفقة، False إذا لم تكن.
    """
    # جلب البيانات
    data = fetch_ict_data(client, symbol, interval, limit=limit)
    bos_data = data
    data = data[:-1]
    
    
    # rsi = fetch_ict_ris_binance_data(client, symbol, interval, period=rsi_period, limit=limit)
    
    # # if data is None or len(data) < limit or rsi is None:
    # #     print(f"⚠️ بيانات غير كافية لتحليل {symbol}")
    # #     return False

    # # التحقق من الشروط
    is_buy = False
    is_sell = False
    side = ""
    
    
    bos_sell = detect_bos(bos_data, is_sell=True)
    shooting_star = detect_shooting_star(data)
    bearish_engulfing = detect_bearish_engulfing(data)
    evening_star = detect_evening_star(data)
    triple_top =  detect_triple_top(data)  # تبديل النمط من بيع الى شراء 
    head_and_shoulders = detect_head_and_shoulders(data) # checkd
    inverted_hammer = detect_inverted_hammer(data)
    large_top = detect_large_top(data) # checkd ملغي
    big_move_down = detect_big_move_down(data) # checkd
    bearish_breakout = detect_bearish_breakout(data)
    bearish_trend = detect_bearish_trend(data)
    
    bearish_flag = detect_bearish_flag(data) 
    # if bos and (shooting_star or bearish_engulfing or evening_star or double_top or head_and_shoulders or inverted_hammer or large_top or big_move_down or bearish_breakout or bearish_trend):
    if bos_sell and (
    # if  (
                head_and_shoulders or   # 95% - نمط قوي جدًا يشير إلى انعكاس الاتجاه إلى الهبوط
                # double_top #or          # 90% - نمط قوي لانعكاس هبوطي بعد قمتين
                triple_top or          # 85% - نمط ثلاث قمم يشير إلى انعكاس هبوطي قوي
                bearish_engulfing or   # 80% - نمط ابتلاعي هبوطي موثوق
                # shooting_star or       # 75% - نمط شمعة يشير إلى انعكاس الاتجاه للأسفل
                bearish_flag  #or       # 70% - نمط يشير إلى استمرارية الاتجاه الهبوطي
                ## evening_star #or        # 65% - نمط انعكاسي يشير إلى بداية اتجاه هبوطي
                # large_top  #or           # 60% - نمط قمة كبيرة يشير إلى احتمال الهبوط
                # inverted_hammer #or     # 55% - نمط شمعة انعكاسي متوسط القوة
                # big_move_down #or       # 50% - حركة هبوط كبيرة ولكن قد تكون مؤقتة
                # bearish_breakout# or    # 50% - كسر هبوطي ولكن يحتاج إلى تأكيد
                # bearish_trend          # 50% - استمرار الاتجاه الهبوطي ولكن يعتمد على الظروف
            ):
        is_sell = True  # إشارة بيع قوية
        side = "sell"

    
    
    # صفقات الشراء
    
    bos_buy = detect_bos(bos_data)
    double_bottom = detect_double_bottom(data) #checkd
    inverse_hns = detect_inverse_head_and_shoulders(data) # checkd
    # hammer= detect_hammer(data)
    # bullish_engulfing = detect_bullish_engulfing(data)
    # evening_star = detect_evening_star(data) # تبديل من نمط بيع الى شراء # ملغي
    # morning_star = detect_morning_star(data)
    piercing_line= detect_piercing_line(data) # ملغي
    double_top = detect_double_top(data) # تبديل النمط من بيع الى شراء 
    triple_top =  detect_triple_top(data)  # تبديل النمط من بيع الى شراء 
    three_white_soldiers= detect_three_white_soldiers(data) # checkd
    large_base = detect_large_base(data)
    big_move_up = detect_big_move_up(data) # checkd
    bullish_breakout = detect_bullish_breakout(data) # checkd
    cup_and_handle = detect_cup_and_handle(data)  
    bullish_flag = detect_bullish_flag(data) # checkd
    # # if bos  and  (double_bottom or inverse_hns or hammer):
    
    if bos_buy and (
    # if (

                three_white_soldiers or  # 95% - نمط قوي جدًا وموثوق في الاتجاه الصاعد
                double_bottom or         # 90% - نمط قوي ويشير إلى انعكاس صعودي
                double_top or
                inverse_hns #or           # 85% - نمط قوي ومؤشر لانعكاس الاتجاه إلى صعود
                # triple_top 
                
                
                # bullish_engulfing  or     # 80% - نمط موثوق يشير إلى صعود
                # morning_star  #or          # 75% - نمط إيجابي يشير إلى بداية اتجاه صاعد
                # bullish_flag #or          # 70% - نمط يشير إلى استمرارية الاتجاه الصاعد
                # large_base  or            # 65% - يشير إلى تكوين قاعدة قوية لدعم الصعود
                # big_move_up #or           # 60% - يشير إلى حركة صاعدة كبيرة ولكنها أقل دقة
                ## piercing_line #or         # 55% - نمط متوسط القوة يشير إلى انعكاس محتمل
                ## hammer #or                # 50% - نمط انعكاسي صاعد ولكنه ضعيف نسبيًا
                
                # cup_and_handle           # 50% - نمط انعكاسي ولكنه يتطلب تأكيدًا إضافيًا
                # bullish_breakout
            ):
        is_buy = True  # إشارة شراء قوية
        side = "buy"
    
        # صفقات الشراء


        # stop_loss_price = close_price * (1 + stop_loss)
        # take_profit_price = close_price * (1 - profit_target)
        
        
    if is_buy and is_sell:
        print(f"⚠️ تم إيجاد تضارب في عملة {symbol}")
        return False, " "

    # تحديد الإشارة النهائية
    # if is_sell:
    #     print(f"📉 إشارة بيع على {symbol}")
    #     return True, "sell"

    if is_buy:
        print(f"📈 إشارة شراء على {symbol}")
        return True, "buy"


    # إذا لم تتحقق أي إشارة
    # print(f"❌ لا توجد إشارات صالحة على {symbol}")
    return False, " "

