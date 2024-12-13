import pandas as pd
import time

def fetch_ict_data(client, symbol, interval='1m', years=5):
    """
    جلب بيانات الشموع التاريخية (1m) لمدة خمس سنوات من Binance.
    """
    # حساب عدد الشموع المطلوبة
    candles_per_day = 1440  # عدد الشموع اليومية
    days_in_year = 365
    total_candles = candles_per_day * days_in_year * years

    # حدود Binance: 1000 شمعة لكل طلب
    limit = 1000

    # قائمة لتخزين البيانات
    all_data = []

    # وقت البداية (قبل خمس سنوات من الآن)
    current_time = int(time.time() * 1000)  # الوقت الحالي بالمللي ثانية
    start_time = current_time - (years * 365 * 24 * 60 * 60 * 1000)

    while total_candles > 0:
        # جلب البيانات من Binance
        candles = client.futures_klines(
            symbol=symbol, interval=interval, limit=limit, startTime=start_time
        )
        
        if not candles:
            break  # إذا لم تكن هناك بيانات إضافية
        
        # إضافة البيانات إلى القائمة
        all_data.extend(candles)

        # تحديث وقت البداية للنطاق التالي
        start_time = candles[-1][6]  # وقت إغلاق آخر شمعة

        # تقليل عدد الشموع المتبقية
        total_candles -= limit

        # التأخير لتجنب حظر Binance
        time.sleep(0.2)  # تأخير بين الطلبات

    # إنشاء DataFrame
    df = pd.DataFrame(all_data, columns=[
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

# مثال للاستخدام:
# client = BinanceClient(api_key, api_secret)
# df = fetch_ict_data(client, symbol='BTCUSDT', interval='1m', years=5)
# print(df)
