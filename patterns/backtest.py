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

klines_interval=Client.KLINE_INTERVAL_5MINUTE
count_top_symbols=200
analize_period= 50
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




def detect_bos(data,is_sell=False):
    """
    اكتشاف كسر الهيكل (BOS) في بيانات Pandas.
    """
    # data['BOS'] = (data['Close'] > data['High'].shift(1)) | (data['Close'] < data['Low'].shift(1))
    # data['BOS'] = ((data['Close'] > data['Close'].shift(1)) | (data['Close'] > data['High'].shift(1)))
    # if is_sell:
        # data['BOS'] = ((data['Close'] < data['Close'].shift(1)) & (data['Close'] < data['Low'].shift(1)))
    #     return data
    
    # data['BOS'] = ((data['Close'] < data['Close'].shift(1)) & (data['Close'] < data['Low'].shift(1)))

    
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



# -------------------- الانماط الصاعدة----------


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
        lows[-3] < lows[-4] and  # القاع الأول أقل من السابق
        abs(lows[-3] - lows[-1]) < (min(lows[-5:]) * 0.01) and  # القاع الأول يساوي القاع الثاني
        data['Close'][-1] > data['High'][-2]  # الإغلاق بعد القاع الثاني أعلى من القمة بين القاعين
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
        lows[-5] > lows[-3] and  # الكتف الأيسر
        lows[-3] < lows[-1] and  # الرأس
        highs[-3] > highs[-5] and highs[-3] > highs[-1]  # الرأس أعلى
    ):
        return True
    
    return False




def detect_hammer(data):
    """
    كشف نمط المطرقة (Hammer)
    """
    open_price = data['Open'][-1]
    close_price = data['Close'][-1]
    high_price = data['High'][-1]
    low_price = data['Low'][-1]

    body = abs(close_price - open_price)
    lower_shadow = min(open_price, close_price) - low_price
    upper_shadow = high_price - max(open_price, close_price)

    return (
        body < (high_price - low_price) * 0.3 and
        lower_shadow > body * 2 and
        upper_shadow < body * 0.3
    )


def detect_bullish_engulfing(data):
    """
    كشف نمط الابتلاع الشرائي (Bullish Engulfing)
    """
    open_price_1 = data['Open'][-2]
    close_price_1 = data['Close'][-2]
    open_price_2 = data['Open'][-1]
    close_price_2 = data['Close'][-1]

    return (
        close_price_1 < open_price_1 and  # الشمعة الأولى هابطة
        open_price_2 < close_price_1 and  # افتتاح الشمعة الثانية أقل من إغلاق الأولى
        close_price_2 > open_price_1      # إغلاق الشمعة الثانية أعلى من افتتاح الأولى
    )


def detect_morning_star(data):
    """
    كشف نمط نجمة الصباح (Morning Star)
    """
    open_price_1 = data['Open'][-3]
    close_price_1 = data['Close'][-3]
    open_price_2 = data['Open'][-2]
    close_price_2 = data['Close'][-2]
    open_price_3 = data['Open'][-1]
    close_price_3 = data['Close'][-1]

    return (
        close_price_1 < open_price_1 and  # الشمعة الأولى هابطة
        abs(close_price_2 - open_price_2) < (close_price_1 - open_price_1) * 0.5 and  # الشمعة الثانية صغيرة
        close_price_3 > open_price_1      # الشمعة الثالثة تغلق فوق افتتاح الأولى
    )


def detect_piercing_line(data):
    """
    كشف نمط اختراق الخط (Piercing Line)
    """
    open_price_1 = data['Open'][-2]
    close_price_1 = data['Close'][-2]
    open_price_2 = data['Open'][-1]
    close_price_2 = data['Close'][-1]

    return (
        close_price_1 < open_price_1 and  # الشمعة الأولى هابطة
        open_price_2 < close_price_1 and  # الشمعة الثانية تفتح أدنى من إغلاق الأولى
        close_price_2 > (open_price_1 + close_price_1) / 2  # إغلاق الشمعة الثانية أعلى منتصف الأولى
    )


def detect_three_white_soldiers(data):
    """
    كشف نمط الجنود الثلاثة البيض (Three White Soldiers)
    """
    close_1 = data['Close'][-3]
    open_1 = data['Open'][-3]
    close_2 = data['Close'][-2]
    open_2 = data['Open'][-2]
    close_3 = data['Close'][-1]
    open_3 = data['Open'][-1]

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
        lows[-5:].min() > lows[-6] and  # قاعدة قوية
        highs[-1] > highs[-2] and      # اختراق القمة السابقة
        highs[-1] > highs[-3]
    )



def detect_big_move_up(data):
    """
    كشف نمط الاندفاع الكبير.
    """
    close_1 = data['Close'][-2]
    close_2 = data['Close'][-1]
    return (
        close_2 > close_1 * 1.05  # ارتفاع كبير بنسبة 5% أو أكثر
    )


def detect_bullish_breakout(data):
    """
    كشف نمط الاختراق الصاعد.
    """
    close_1 = data['Close'][-2]
    close_2 = data['Close'][-1]
    high_1 = data['High'][-2]
    return (
        close_2 > high_1 * 1.01 and  # اختراق القمة السابقة بنسبة 1% أو أكثر
        close_2 > close_1
    )





# -------------------- الانماط الهابطة----------

def detect_shooting_star(data):
    """
    كشف نمط الشهاب (Shooting Star)
    """
    open_price = data['Open'][-1]
    close_price = data['Close'][-1]
    high_price = data['High'][-1]
    low_price = data['Low'][-1]
    
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
    open_price_1 = data['Open'][-2]
    close_price_1 = data['Close'][-2]
    open_price_2 = data['Open'][-1]
    close_price_2 = data['Close'][-1]

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
        highs[-2] == max(highs[-5:]) and
        highs[-3] == max(highs[-5:]) and
        highs[-2] == highs[-3]
    )


def detect_head_and_shoulders(data):
    """
    كشف نمط الرأس والكتفين (Head and Shoulders)
    """
    highs = data['High']
    return (
        highs[-4] < highs[-3] and  # الكتف الأول
        highs[-3] > highs[-2] and  # الرأس
        highs[-2] < highs[-3] and  # الكتف الثاني
        highs[-1] < highs[-2]      # تأكيد الكسر
    )


def detect_inverted_hammer(data):
    """
    كشف نمط المطرقة المقلوبة (Inverted Hammer)
    """
    open_price = data['Open'][-1]
    close_price = data['Close'][-1]
    high_price = data['High'][-1]
    low_price = data['Low'][-1]

    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    return (
        body < (high_price - low_price) * 0.3 and
        upper_shadow > body * 2 and
        lower_shadow < body * 0.2
    )


def detect_evening_star(data):
    """
    كشف نمط نجمة المساء (Evening Star)
    """
    open_price_1 = data['Open'][-3]
    close_price_1 = data['Close'][-3]
    open_price_2 = data['Open'][-2]
    close_price_2 = data['Close'][-2]
    open_price_3 = data['Open'][-1]
    close_price_3 = data['Close'][-1]

    return (
        close_price_1 > open_price_1 and  # الشمعة الأولى صاعدة
        close_price_2 > close_price_1 and  # الشمعة الثانية صاعدة أكثر
        close_price_3 < (open_price_1 + close_price_1) / 2 and  # الشمعة الثالثة تغلق تحت منتصف الأولى
        close_price_3 < open_price_3  # الشمعة الثالثة هابطة
    )

def detect_large_top(data):
    """
    كشف نمط القاعدة الكبيرة الهابطة.
    """
    highs = data['High']
    lows = data['Low']
    return (
        highs[-5:].max() < highs[-6] and  # قاعدة هابطة
        lows[-1] < lows[-2] and           # انخفاض كبير تحت القاع السابق
        lows[-1] < lows[-3]
    )


def detect_big_move_down(data):
    """
    كشف نمط الاندفاع الكبير الهابط.
    """
    close_1 = data['Close'][-2]
    close_2 = data['Close'][-1]
    return (
        close_2 < close_1 * 0.95  # انخفاض كبير بنسبة 5% أو أكثر
    )

def detect_bearish_breakout(data):
    """
    كشف نمط الاختراق الهابط.
    """
    close_1 = data['Close'][-2]
    close_2 = data['Close'][-1]
    low_1 = data['Low'][-2]
    return (
        close_2 < low_1 * 0.99 and  # اختراق القاع السابق بنسبة 1% أو أكثر
        close_2 < close_1
    )

def detect_bearish_trend(data):
    """
    كشف نمط المتاجرة الهابطة في الاتجاه.
    """
    close_1 = data['Close'][-5]
    close_2 = data['Close'][-1]
    return (
        close_2 < close_1 and  # إغلاق الشمعة الأخيرة أقل من الشمعة قبلها
        close_2 < data['Open'][-1]  # سعر الإغلاق أقل من سعر الافتتاح
    )






class ICTStrategy(Strategy):
    profit_target = 0.01  # الربح المستهدف كنسبة مئوية
    stop_loss = 0.02  # إيقاف الخسارة كنسبة مئوية
    rsi_period = 14
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
        
        
        
        
        
        
        
        
        
        
        bos_detected = self.data.BOS[-1]
        double_bottom = detect_double_bottom(self.data)
        inverse_hns = detect_inverse_head_and_shoulders(self.data)
        hammer= detect_hammer(self.data)
        bullish_engulfing = detect_bullish_engulfing(self.data)
        morning_star = detect_morning_star(self.data)
        piercing_line= detect_piercing_line(self.data)
        three_white_soldiers= detect_three_white_soldiers(self.data)
        
        large_base = detect_large_base(self.data)
        big_move_up = detect_big_move_up(self.data)
        bullish_breakout = detect_bullish_breakout(self.data)
        # # if bos  and  (double_bottom or inverse_hns or hammer):
        
        if bos_detected and (

        # if (
                inverse_hns or 
                double_bottom or 
                three_white_soldiers or 
                bullish_engulfing or 
                morning_star  or 
                large_base  or 
                bullish_breakout or 
                big_move_up  or 
                piercing_line  or 
                hammer
            ):
        # if bos  and  (double_bottom or inverse_hns or hammer):
        # if self.rsi < 40 and (double_bottom or inverse_hns or hammer or bullish_engulfing or morning_star or piercing_line or three_white_soldiers):
            if not self.position:
                close_price = self.data.Close[-1]

                stop_loss_price = close_price * (1 - self.stop_loss)
                take_profit_price = close_price * (1 + self.profit_target)
                self.buy(sl=stop_loss_price, tp=take_profit_price)     
                
                
                # close_price = self.data.Close[-1]
                # stop_loss_price = close_price * (1 + self.stop_loss)
                # take_profit_price = close_price * (1 - self.profit_target)
                # self.sell(sl=stop_loss_price, tp=take_profit_price)
            
        
        
        # shooting_star = detect_shooting_star(self.data)
        # bearish_engulfing = detect_bearish_engulfing(self.data)
        # evening_star = detect_evening_star(self.data)
        # double_top = detect_double_top(self.data)
        # head_and_shoulders = detect_head_and_shoulders(self.data)
        # inverted_hammer = detect_inverted_hammer(self.data)
        # bos_detected = self.data.BOS[-1]

        # large_top = detect_large_top(self.data)
        # big_move_down = detect_big_move_down(self.data)
        # bearish_breakout = detect_bearish_breakout(self.data)
        # bearish_trend = detect_bearish_trend(self.data)
        # # if bos and (shooting_star or bearish_engulfing or evening_star or double_top or head_and_shoulders or inverted_hammer or large_top or big_move_down or bearish_breakout or bearish_trend):
        # if bos_detected and (
        # # if  (
        #         head_and_shoulders or 
        #         double_top or 
        #         bearish_engulfing or 
        #         shooting_star or 
        #         evening_star or 
        #         inverted_hammer or 
        #         large_top or 
        #         big_move_down  or 
        #         bearish_breakout or 
        #         bearish_trend
        #         ):
            
        #     if not self.position:
        #         close_price = self.data.Close[-1]
        #         stop_loss_price = close_price * (1 + self.stop_loss)
        #         take_profit_price = close_price * (1 - self.profit_target)
        #         self.sell(sl=stop_loss_price, tp=take_profit_price)
                
        #         close_price = self.data.Close[-1]
        #         stop_loss_price = close_price * (1 - self.stop_loss)
        #         take_profit_price = close_price * (1 + self.profit_target)
        #         self.buy(sl=stop_loss_price, tp=take_profit_price)   
                
            # bos_detected = self.data.BOS[-1]
            # double_bottom = detect_double_bottom(self.data)
            # inverse_hns = detect_inverse_head_and_shoulders(self.data)
            # hammer= detect_hammer(self.data)
            
        
        # # print(f"BOS Detected: {bos_detected}")
        # close_price = self.data.Close[-1]
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
        # data = data[:-2]
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
excel.columns = ['Symbol', 'Return', 'Trades', 'Win Rate', 'Best Trade', 'Worst Trade','Max Duration','Avg Duration',]
excel.loc[len(excel.index)] = ['Total', excel['Return'].sum(), excel['Trades'].sum(), excel['Win Rate'].sum() / count_top_symbols, '', '','', '']

# excel.to_excel('result.xlsx')

excel.to_csv('pattern_result.csv')
