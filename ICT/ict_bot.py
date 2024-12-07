import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client  # للتعامل مع Binance API
# from config import API_KEY, API_SECRET, FUTUER_API_TEST_KEY, FUTUER_API_TEST_SECRET


# تهيئة عميل Binance API
api_key = 'of6qt1T1MpGvlgma1qxwFTLdrGNNVsMj0fKf8LZy1sMf3OqTrwHC7BCRIkgsSsda'
api_secret = 'MZuALJiqyWMoQ0WkPE6tqWdToGLTHLsap5m95qhPIDtizy1FPD0TQBXNvyQBhgFf'


# api_key = 'tweOjH1Keln44QaxLCr3naevRPgF3j3sYuOpaAg9B7nUT74MyURemvivEUcihfkt'
# api_secret = 'XLlku378D8aZzYg9JjOTtUngA8Q73xBCyy7jGVbqRYSoEICsGBfWC0cIsRptLHxb'

# تهيئة الاتصال ببايننس واستخدام Testnet
client = Client(api_key, api_secret,requests_params={'timeout':90})
# client = Client(API_KEY, API_SECRET)

# تحميل بيانات الشموع (1m أو 5m)
def fetch_historical_data(symbol, interval, limit=500):
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



def identify_liquidity_zones(data):
    """
    تحديد مناطق السيولة بناءً على القمم والقيعان.
    """
    data['Liquidity_Zone_High'] = data['High'].rolling(window=5).max().shift(1)
    data['Liquidity_Zone_Low'] = data['Low'].rolling(window=5).min().shift(1)
    return data


def detect_bos(data):
    """
    اكتشاف كسر الهيكل (BOS) في البيانات.
    """
    data['BOS'] = (data['Close'] > data['High'].shift(1)) | (data['Close'] < data['Low'].shift(1))
    return data


# def detect_fvg(data):
#     """
#     تحديد فجوات القيمة العادلة (FVG).
#     """
#     fvg_zones = []
#     for i in range(1, len(data)-2):
#         if data['Low'][i] > data['High'][i-1] and data['High'][i] < data['Low'][i+1]:
#             fvg_zones.append({
#                 "start": data.index[i],
#                 "low": data['Low'][i],
#                 "high": data['High'][i]
#             })
#     return fvg_zones

def detect_fvg(data):
    """
    اكتشاف فجوات القيمة العادلة (Fair Value Gap).
    """
    # الوصول إلى الأعمدة بشكل فردي
    highs = data['High']
    lows = data['Low']
    closes = data['Close']

    print(f"Highs: {highs[-5:]}, Lows: {lows[-5:]}, Closes: {closes[-5:]}")

    fvg_zones = []
    # اكتشاف الفجوات في البيانات
    for i in range(1, len(data)):
        if lows[i] > highs[i - 1]:  # فجوة صعودية
            fvg_zones.append({'high': highs[i - 1], 'low': lows[i]})
        elif highs[i] < lows[i - 1]:  # فجوة هبوطية
            fvg_zones.append({'high': highs[i], 'low': lows[i - 1]})

    print(f"Detected FVG Zones: {fvg_zones}")
    return fvg_zones




def enter_trade(data):
    """
    التحقق من إشارات الدخول وتنفيذ الصفقة.
    """
    fvg_zones = detect_fvg(data)
    bos_detected = data['BOS'].iloc[-1]

    if bos_detected and fvg_zones:
        # إذا كان هناك كسر هيكل وفجوة FVG
        zone = fvg_zones[-1]  # أحدث منطقة FVG
        if data['Close'].iloc[-1] < zone['low']:
            return "Sell", zone['start']
        elif data['Close'].iloc[-1] > zone['high']:
            return "Buy", zone['start']
    return None, None



def is_trading_session():
    """
    تحقق من وجود الوقت الحالي ضمن جلسة تداول فعالة.
    """
    current_time = datetime.utcnow()
    london_start = current_time.replace(hour=8, minute=0, second=0)
    london_end = current_time.replace(hour=16, minute=0, second=0)
    newyork_start = current_time.replace(hour=13, minute=0, second=0)
    newyork_end = current_time.replace(hour=21, minute=0, second=0)

    return london_start <= current_time <= london_end or newyork_start <= current_time <= newyork_end



def manage_trade(signal, data, leverage=10):
    """
    تنفيذ الصفقة وإدارتها.
    """
    if signal == "Buy":
        print("شراء عند السعر:", data['Close'].iloc[-1])
        # هنا يمكن إضافة كود لفتح صفقة شراء عبر Binance API
    elif signal == "Sell":
        print("بيع عند السعر:", data['Close'].iloc[-1])
        # هنا يمكن إضافة كود لفتح صفقة بيع عبر Binance API




def ict_trading_system(symbol, interval):
    """
    نظام التداول بناءً على إستراتيجية ICT.
    """
    data = fetch_historical_data(symbol, interval)
    data = identify_liquidity_zones(data)
    data = detect_bos(data)

    # تحقق من الإشارات والجلسات
    if is_trading_session():
        signal, zone = enter_trade(data)
        if signal:
            manage_trade(signal, data)


