from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
# import  config 
from binance.exceptions import BinanceAPIException
from ict_bot import *
import ta
# استخدم دالة fetch_historical_data لتحميل البيانات
# أو قم بتحميل بيانات جاهزة في صيغة DataFrame

klines_interval=Client.KLINE_INTERVAL_15MINUTE
count_top_symbols=200
analize_period= 80
excluded_symbols = set()  # قائمة العملات المستثناة بسبب أخطاء متكررة
klines_limit=20
black_list=[
        'USDCUSDT',
        'USTCUSDT',

    ]


def get_top_symbols(limit=20, profit_target=0.007, rsi_threshold=70):
    tickers = client.futures_ticker()
    exchange_info = client.futures_exchange_info()  # جلب معلومات التداول
    valid_symbols = {info['symbol'] for info in exchange_info['symbols']}  # الرموز المسموح بها
    sorted_tickers = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
    top_symbols = []
    
    for ticker in sorted_tickers:
        if ticker['symbol'].endswith("USDT") and ticker['symbol'] in valid_symbols and ticker['symbol'] not in excluded_symbols and ticker['symbol'] not in black_list :  # تحقق من صلاحية الرمز
            try:
                klines = client.get_klines(symbol=ticker['symbol'], interval=klines_interval, limit=klines_limit)
                if klines is None or klines == []:
                    continue
                top_symbols.append(ticker['symbol'])
                if len(top_symbols) >= limit:
                    break
            except BinanceAPIException as e:
                print(f"خطأ في جلب بيانات {ticker['symbol']}: {e}")
                excluded_symbols.add(ticker['symbol'])
    return top_symbols



def detect_hammer(data):
    """
    دالة للكشف عن نمط المطرقة في البيانات.
    """
    # احصل على البيانات مباشرة من الكائن
    open_price = data['Open'][-1]
    high_price = data['High'][-1]
    low_price = data['Low'][-1]
    close_price = data['Close'][-1]

    # حساب جسم الشمعة والظلال
    body = abs(close_price - open_price)  # طول الجسم
    lower_shadow = abs(open_price - low_price) if close_price > open_price else abs(close_price - low_price)  # الظل السفلي
    upper_shadow = abs(high_price - close_price) if close_price > open_price else abs(high_price - open_price)  # الظل العلوي

    # التحقق من شروط نمط المطرقة
    is_hammer = (
        body < (high_price - low_price) * 0.3 and  # الجسم صغير مقارنة بالمدى
        lower_shadow > body * 2 and  # الظل السفلي أطول بمرتين من الجسم
        upper_shadow < body * 0.3  # الظل العلوي قصير جدًا
    )
    return is_hammer




def detect_bos(data):
    """
    اكتشاف كسر الهيكل (BOS) في بيانات Pandas.
    """
    # data['BOS'] = (data['Close'] > data['High'].shift(1)) | (data['Close'] < data['Low'].shift(1))
    data['BOS'] = ((data['Close'] > data['Close'].shift(1)) | (data['Close'] > data['High'].shift(1)))

    # data['BOS'] = ((data['Close'] > data['High'].shift(1)))
    # data['BOS'] = ((data['Close'] > data['High'].shift(1)))
    # data['BOS'] = ((data['Close'] > data['Close'].shift(1)))

    return data


def preprocess_data(data):
    """
    تجهيز البيانات التاريخية لإضافة مناطق السيولة.
    """
    data['Liquidity_Zone_High'] = data['High'].rolling(window=5).max().shift(1)
    data['Liquidity_Zone_Low'] = data['Low'].rolling(window=5).min().shift(1)
    data = detect_bos(data)  # إضافة عمود BOS

    return data


def load_data(symbol, intervel, period):
    """
    تحميل بيانات تاريخية بصيغة OHLCV.
    """
    data = fetch_historical_data(symbol, intervel, period)  # قم بتغيير الزوج والفاصل الزمني حسب الحاجة
    data.set_index('Open_Time', inplace=True)
    data = preprocess_data(data)  # تجهيز البيانات

    return data


def calculate_rsi(data, period=14):
    """حساب RSI متوافق مع مكتبة Backtesting"""
    deltas = pd.Series(data).diff()  # تحويل البيانات إلى pandas Series للتوافق
    gains = deltas.where(deltas > 0, 0.0)
    losses = -deltas.where(deltas < 0, 0.0)
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def bol_h(df):
    return ta.volatility.BollingerBands(pd.Series(df)).bollinger_hband() 

def bol_l(df):
    return ta.volatility.BollingerBands(pd.Series(df)).bollinger_lband() 


# def detect_double_bottom(data):
#     """
#     اكتشاف نمط القاع المزدوج في البيانات.
    
#     Args:
#         data (DataFrame): بيانات الشموع (Pandas DataFrame).
    
#     Returns:
#         bool: True إذا تم اكتشاف القاع المزدوج، False إذا لم يتم.
#     """
#     if len(data) < 5:  # التأكد من وجود بيانات كافية
#         return False
    
#     lows = data['Low']
#     # التحقق من القاعين المتساويين نسبياً
#     if (
#         lows.iloc[-3] < lows.iloc[-4] and  # القاع الأول أقل من السابق
#         lows.iloc[-3] == lows.iloc[-1] and  # القاع الأول يساوي القاع الثاني
#         data['Close'].iloc[-1] > data['High'].iloc[-2]  # الإغلاق بعد القاع الثاني أعلى من القمة بين القاعين
#     ):
#         return True
    
#     return False

def detect_double_bottom(data):
    """
    دالة للكشف عن نمط القاع المزدوج.
    """
    lows = pd.Series(data['Low'])
    
    # التحقق من أن هناك عددًا كافيًا من القيم
    if len(lows) < 5:
        return False

    # شروط القاع المزدوج
    double_bottom_detected = (
        lows.iloc[-3] < lows.iloc[-4] and  # القاع الأول أقل من السابق
        lows.iloc[-3] < lows.iloc[-2] and  # القاع الأول أقل من القاع الثاني
        lows.iloc[-1] > lows.iloc[-3]      # السعر الحالي أعلى من القاع الأول
    )
    return double_bottom_detected



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
    
    lows = pd.Series(data['Low'])
    highs = pd.Series(data['High'])
    # تحقق من الرأس والكتفين
    if (
        lows.iloc[-5] > lows.iloc[-3] and  # الكتف الأيسر
        lows.iloc[-3] < lows.iloc[-1] and  # الرأس
        highs.iloc[-3] > highs.iloc[-5] and highs.iloc[-3] > highs.iloc[-1]  # الرأس أعلى
    ):
        return True
    
    return False






def detect_shooting_star(data):
    open_price = data['Open'][-1]
    close_price = data['Close'][-1]
    high_price = data['High'][-1]
    low_price = data['Low'][-1]
    
    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    is_shooting_star = (
        body < (high_price - low_price) * 0.3 and
        upper_shadow > body * 2 and
        lower_shadow < body * 0.2
    )
    return is_shooting_star


def detect_bearish_engulfing(data):
    open_price_1 = data['Open'][-2]
    close_price_1 = data['Close'][-2]
    open_price_2 = data['Open'][-1]
    close_price_2 = data['Close'][-1]

    is_bearish_engulfing = (
        close_price_1 > open_price_1 and
        open_price_2 > close_price_1 and
        close_price_2 < open_price_1
    )
    return is_bearish_engulfing


def detect_double_top(data):
    highs = data['High']
    is_double_top = (
        highs[-2] == max(highs[-5:]) and
        highs[-3] == max(highs[-5:]) and
        highs[-2] == highs[-3]  # القمتان متساويتان
    )
    return is_double_top


def detect_head_and_shoulders(data):
    highs = data['High']
    is_head_and_shoulders = (
        highs[-4] < highs[-3] and  # الكتف الأول
        highs[-3] > highs[-2] and  # الرأس أعلى من الكتف
        highs[-2] < highs[-3] and  # الكتف الثاني
        highs[-1] < highs[-2]      # تأكيد الكسر
    )
    return is_head_and_shoulders

def detect_inverted_hammer(data):
    open_price = data['Open'][-1]
    close_price = data['Close'][-1]
    high_price = data['High'][-1]
    low_price = data['Low'][-1]

    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    is_inverted_hammer = (
        body < (high_price - low_price) * 0.3 and
        upper_shadow > body * 2 and
        lower_shadow < body * 0.2
    )
    return is_inverted_hammer


def detect_evening_star(data):
    open_price_1 = data['Open'][-3]
    close_price_1 = data['Close'][-3]
    open_price_2 = data['Open'][-2]
    close_price_2 = data['Close'][-2]
    open_price_3 = data['Open'][-1]
    close_price_3 = data['Close'][-1]

    is_evening_star = (
        close_price_1 > open_price_1 and  # الشمعة الأولى صاعدة
        close_price_2 > close_price_1 and  # الشمعة الثانية صاعدة أكثر
        close_price_3 < (open_price_1 + close_price_1) / 2 and  # الشمعة الثالثة تغلق تحت منتصف الأولى
        close_price_3 < open_price_3  # الشمعة الثالثة هابطة
    )
    return is_evening_star





class ICTStrategy(Strategy):
    profit_target = 0.01  # الربح المستهدف كنسبة مئوية
    stop_loss = 0.01  # إيقاف الخسارة كنسبة مئوية
    rsi_period = 8
    def init(self):
        """
        تهيئة المؤشرات أو المتغيرات.
        """
        # يمكن استخدام متغيرات لحفظ الإشارات المكتشفة
        # self.data['Liquidity_Zone_High'] = self.data['High'].rolling(window=5).max().shift(1)
        # self.data['Liquidity_Zone_Low'] = self.data['Low'].rolling(window=5).min().shift(1)
        self.rsi = self.I(calculate_rsi, self.data.Close, self.rsi_period)
        self.bol_h=self.I(bol_h, self.data.Close)
        self.bol_l=self.I(bol_l, self.data.Close)
    
    
    
    
    def next(self):
        
        
        
        shooting_star = detect_shooting_star(self.data)
        bearish_engulfing = detect_bearish_engulfing(self.data)
        evening_star = detect_evening_star(self.data)
        double_top = detect_double_top(self.data)
        head_and_shoulders = detect_head_and_shoulders(self.data)
        inverted_hammer = detect_inverted_hammer(self.data)
        bos_detected = self.data.BOS[-1]


        if  shooting_star or bearish_engulfing or evening_star or double_top or head_and_shoulders or inverted_hammer :
            close_price = self.data.Close[-1]
            stop_loss_price = close_price * (1 + self.stop_loss)
            take_profit_price = close_price * (1 - self.profit_target)
            self.sell(sl=stop_loss_price, tp=take_profit_price)
            
            # bos_detected = self.data.BOS[-1]
            # double_bottom = detect_double_bottom(self.data)
            # inverse_hns = detect_inverse_head_and_shoulders(self.data)
            # hammer= detect_hammer(self.data)
            
        
        # # print(f"BOS Detected: {bos_detected}")
        close_price = self.data.Close[-1]
        # fvg_zones = detect_fvg(self.data)

        # # if bos_detected and self.data.Close[-3] > self.bol_l[-3] and self.data.Close[-2] < self.bol_l[-2] :
        # # if bos_detected and self.data.Close[-3] > self.bol_l[-3] and self.data.Close[-2] < self.bol_l[-2] and self.rsi[-1] > 25 and self.rsi[-1] < 45:
        # # if bos_detected and self.data.Close[-3] > self.bol_l[-3] and self.data.Close[-2] < self.bol_l[-2]:
        # if bos_detected and (double_bottom or inverse_hns):
        # if inverse_hns :
        # if (double_bottom and inverse_hns )or hammer:
        # if (double_bottom and hammer  )or inverse_hns:

        # if (hammer  and inverse_hns ) or double_bottom:
        # if (hammer and double_bottom   )or inverse_hns:

        
        # if (inverse_hns and hammer  ) or double_bottom:
        # if (inverse_hns and double_bottom ) or hammer :
        # if inverse_hns and double_bottom  and hammer :

        # if self.rsi[-1] < 40 and (double_bottom or inverse_hns or hammer):

        # if bos_detected and (double_bottom or inverse_hns or hammer):
        # if bos_detected  and (self.rsi[-1] > 25 and self.rsi[-1] < 45) and (inverse_hns or hammer):
        # if bos_detected  and (double_bottom or inverse_hns or hammer):

        # if bos_detected  and (inverse_hns or hammer):
        
        # if bos_detected and self.rsi[-2] > 25 and self.rsi[-2] < 45:

        #     # print("BOS Signal Detected!")
        #     # اختبر بشكل مستقل من دون FVG
            # stop_loss_price = close_price * (1 - self.stop_loss)
            # take_profit_price = close_price * (1 + self.profit_target)
            # self.buy(sl=stop_loss_price, tp=take_profit_price)
            
            # stop_loss_price = close_price * (1 + self.stop_loss)
            # take_profit_price = close_price * (1 - self.profit_target)
            # self.sell(sl=stop_loss_price, tp=take_profit_price)
            
        # fvg_zones = detect_fvg(self.data)
        # bos_detected = self.data.BOS[-1]
        
        # # سجل تحقق الإشارات
        # # print(f"FVG Zones: {fvg_zones}, BOS Detected: {bos_detected}")
        
        # if bos_detected and fvg_zones:
        #     # print("Signal Detected! Checking conditions...")
        #     zone = fvg_zones[-1]
        #     close_price = self.data.Close[-1]

        #     risk_percentage = 0.01
        #     reward_percentage = 0.02

        #     if close_price < zone['low'] and not self.position:
        #         print("Opening Sell Position...")
        #         stop_loss_price = close_price * (1 + risk_percentage)
        #         take_profit_price = close_price * (1 - reward_percentage)
        #         self.sell(sl=stop_loss_price, tp=take_profit_price)
            
        #     elif close_price > zone['high'] and not self.position:
        #     # if close_price > zone['high'] and not self.position:
            
        #         print("Opening Buy Position...")
        #         stop_loss_price = close_price * (1 - risk_percentage)
        #         take_profit_price = close_price * (1 + reward_percentage)
        #         self.buy(sl=stop_loss_price, tp=take_profit_price)

# تحميل البيانات

# data = load_data()

# # إعداد Backtest مع البيانات والإستراتيجية
# bt = Backtest(data, ICTStrategy, cash=10000000, commission=0.002)

# # تشغيل الاختبار
# results = bt.run()

# # عرض النتائج
# print(results)

# رسم النتائج
# bt.plot()

def extract_stats(stats):
    trades = stats['# Trades']  # عدد الصفقات
    win_rate = stats['Win Rate [%]']  # نسبة الربح
    best_trade = stats['Best Trade [%]']  # أفضل صفقة
    worst_trade = stats['Worst Trade [%]']  # أسوأ صفقة
    max_duration = stats['Max. Trade Duration']  
    avg_duration = stats['Max. Trade Duration']  

    return trades, win_rate, best_trade, worst_trade, max_duration, avg_duration



result=[]
# تنفيذ الباكتيست
if __name__ == "__main__":
    # استخدم بيانات Binance أو بيانات جاهزة
    for symbol in get_top_symbols(count_top_symbols):
        # data = fetch_binance_data(symbol, Client.KLINE_INTERVAL_3MINUTE, "12 hours ago UTC", "6 hours ago UTC")
        data = load_data(symbol, klines_interval, analize_period)

        # data = fetch_binance_data(symbol, Client.KLINE_INTERVAL_3MINUTE, "168 hours ago UTC", "30 Nov 2024")

        # data = fetch_binance_data(symbol, Client.KLINE_INTERVAL_3MINUTE, "17 Nov 2024", "23 Nov 2024")

        # if data is None or data == []:
        #     # print(f"the data in symbol {symbol} is empty") 
        #     continue
        # تشغيل الباكتيست باستخدام Backtesting.py
        print(symbol)
        
        bt = Backtest(data, ICTStrategy, cash=10000000, commission=0.002)
        stats = bt.run() 
        trades, win_rate, best_trade, worst_trade, max_duration, avg_duration= extract_stats(stats)

        # print(stats.iloc[6])
        result.append([symbol, stats.iloc[6], trades, win_rate, best_trade, worst_trade, max_duration, avg_duration])
        # stats.plot()
        # print(stats)
        # bt.plot()
        # print(len(data))
        # طباعة النتائج
        # print(stats)





excel = pd.DataFrame(result)
excel.columns = ['Symbol', 'Return', 'Trades', 'Win Rate', 'Best Trade', 'Worst Trade','Max Duration','Avg Duration']
excel.loc[len(excel.index)] = ['Total', excel['Return'].sum(), excel['Trades'].sum(), '', '', '','', '']

# excel.to_excel('result.xlsx')

excel.to_csv('ict_result.csv')
