import json
from binance.client import Client
from datetime import datetime
import math
import time
import csv
import os
import statistics
from binance.exceptions import BinanceAPIException
import threading
import requests
from utils.config import API_KEY, API_SECRET, FUTUER_API_TEST_KEY, FUTUER_API_TEST_SECRET
from utils.helper import *
import numpy as np
import pandas as pd
import decimal
import ta
import utils.request_load as request_load

import utils.helper as helper



client = Client(API_KEY,API_SECRET,requests_params={'timeout':90})
# client.API_URL = 'https://testnet.binance.vision/api'
# client = Client(FUTUER_API_TEST_KEY, FUTUER_API_TEST_SECRET, testnet=True, requests_params={'timeout':90})
# client.API_URL = "https://testnet.binancefuture.com"


# client.futures_account_balance()
current_prices = {}
# _active_trades = helper.get_futuer_active_trades(client)
active_trades = request_load.get_futuer_open_trad()

# إدارة المحفظة 0
balance = helper.get_futuer_usdt_balance(client) # الرصيد المبدئي للبوت
# balance = 3# الرصيد المبدئي للبوت

investment=0.5 # حجم كل صفقة
base_profit_target=0.008 # نسبة الربح
# base_profit_target=0.005 # نسبة الربح
base_stop_loss=0.02 # نسبة الخسارة
# base_stop_loss=0.000 # نسبة الخسارة
timeout=60 # وقت انتهاء وقت الصفقة
commission_rate = 0.002 # نسبة العمولة للمنصة
klines_interval=Client.KLINE_INTERVAL_5MINUTE
klines_limit=14
count_top_symbols=200
analize_period=80
rsi_analize_period=8
start_date= '3 hours ago UTC'
# test_list =[
#                     'CATIUSDT',
#                     'WIFUSDT',
#                     'CATIUSDT',
#                     'PNUTUSDT',
#                     'CRVUSDT',
#                     'BOMEUSDT',
#                 ]

leverage = 20   # ال80رافعة المالية


excluded_symbols =[]  # قائمة العملات المستثناة بسبب أخطاء متكررة
symbols_to_trade =request_load.get_futuer_top_symbols(count_top_symbols ,excluded_symbols)
last_trade_time = {}

top_symbols=request_load.get_futuer_top_symbols(count_top_symbols ,excluded_symbols)

__active_symbol = {}
_symbols = client.futures_exchange_info()['symbols']
valid_symbols = [s['symbol'] for s in _symbols]

MAX_POSITIONS = 10




csv_file = 'bollinger__futuers_trades_log.csv'
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['الرمز', 'الكمية', 'السعر الابتدائي', 'سعر الهدف', 'سعر الإيقاف', 'وقت الاغلاق', 'وقت الفتح','نسبة الربح','نسبة الخسارة','المهلة', 'الربح','النتيجة', 'الرصيد المتبقي'])


def can_trade(symbol):
    if symbol in last_trade_time and time.time() - last_trade_time[symbol] < 30:  # انتظار 5 دقائق
        # print(f"تخطى التداول على {symbol} - لم تمر 5 دقائق منذ آخر صفقة.")
        return False
    return True






def open_futures_trade(symbol, investment, leverage):
    global base_profit_target, base_stop_loss, active_trades, balance
    if get_open_positions_count(client) >= MAX_POSITIONS:
        return
    
    
    if symbol in active_trades:
        print(f"هناك صفقة مفتوحة من قبل لعملة {symbol}")
        return
    if balance < investment:
        # print(f"{datetime.now()} - {symbol} -الرصيد الحالي غير كافٍ لفتح صفقة جديدة.")
        return
    
    # if not helper.should_open_futuer_rsi_trade(client=client, symbol=symbol, intervel=klines_interval,limit=analize_period,rsi_limit=rsi_analize_period):
    # # print(f"لا يجب شراء {symbol} في الوقت الحالي ")
    #     return
    
    if not helper.rsi_ict_should_open_futuer_trade(client=client, symbol=symbol, interval=klines_interval,limit=analize_period,rsi_period=rsi_analize_period):
    # print(f"لا يجب شراء {symbol} في الوقت الحالي ")
        return
    
    time.sleep(3)
    try:
        # ضبط الرافعة المالية
        client.futures_change_leverage(symbol=symbol, leverage=leverage)

        # الحصول على سعر السوق الحالي
        ticker = client.futures_symbol_ticker(symbol=symbol)
        
        if not ticker:
            excluded_symbols.append(symbol)
            return
        
        current_price = float(ticker['price'])
        # price = float(ticker['price'])
        # qty_precision = get_qty_precision(symbol)
        price_precision = get_price_precision(client,symbol)
        # qty = round(leverage/price, qty_precision)
        
        # حساب الكمية بالدقة المناسبة
        _quantity = (investment / current_price) * leverage
        # quantity_precision = helper.get_qty_precision(client, symbol,)
        # quantity = round(_quantity, quantity_precision)
        # quantity = helper.adjust_futuer_quantity(client, symbol,((investment * leverage )/ current_price))
        quantity = helper.QUN_Precision(client,((investment * leverage )/ current_price),symbol,)
        
        _target_price = current_price * (1 + base_profit_target)
        _stop_loss_price = current_price * (1 - base_stop_loss)
        # price_precision = helper.adjust_futuser_price_precision(client, symbol, current_price * (1 + base_profit_target))
        # target_price = round(_target_price, price_precision)
        stop_loss_price = round(_stop_loss_price, price_precision)
        target_price = float(helper.Pric_Precision(client, _target_price, symbol))
        # _target_price = current_price * (1 + base_profit_target)
        # _stop_loss_price = current_price * (1 - base_stop_loss)
        # price_precision = helper.adjust_futuser_price_precision(client, symbol, current_price * (1 + base_profit_target))
        # target_price = helper.adjust_futuser_price_precision(client, symbol, current_price * (1 + base_profit_target))
        # stop_loss_price = helper.adjust_futuser_price_precision(client, symbol, current_price * (1 - base_profit_target))
        
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "initial_price": current_price,
            "target_price": target_price,
            'stop_price': stop_loss_price,
            'start_time':str(datetime.fromtimestamp(time.time())),
            "timeout": timeout * 60,
            "investment": investment,
            "is_futuer": True
        }
        __active_symbol[symbol] = payload

        
        #         # تنفيذ أمر شراء بالسوق
        order = client.futures_create_order(
            symbol=symbol,
            side='BUY',
            type='MARKET',
            quantity=quantity
        )
                # تنفيذ أمر شراء بالسوق
        # order = client.futures_create_order(
        #     symbol=symbol,
        #     side='SELL',
        #     type='MARKET',
        #     quantity=quantity
        # )
        helper.update_futuer_active_trades(client)

        order_response= request_load.create_trad(payload)
        active_trades = request_load.get_futuer_open_trad()

        # حساب سعر جني الأرباح
        # target_price = adjust_futuser_price_precision(client, symbol, current_price * (1 + base_profit_target))
        # stop_loss_price = adjust_futuser_price_precision(client, symbol, current_price * (1 - base_stop_loss))

        # target_price = current_price * (1 + base_profit_target)
        # stop_loss_price = current_price * (1 - base_stop_loss)

        # إعداد أمر جني الأرباح
        # client.futures_create_order(
        #     symbol=symbol,
        #     side='BUY',
        #     type='TAKE_PROFIT_MARKET',
        #     stopPrice=target_price,
        #     closePosition=True
        # )
        client.futures_create_order(
            symbol=symbol,
            side='SELL',
            type='TAKE_PROFIT_MARKET',
            stopPrice=target_price,
            closePosition=True
        )
        # client.futures_create_order(
        #     symbol=symbol,
        #     side='BUY',
        #     type='TAKE_PROFIT_MARKET',
        #     stopPrice=target_price,
        #     closePosition=True
        # )


        print(f"تم فتح صفقة شراء {symbol} بنجاح!")
        print(f"تم تحديد مستوى جني الأرباح عند {target_price}")
        # print(f"تم تحديد مستوى جني الأرباح عند {target_price}")
        print(f"تم تعيين وقف الخسارة عند {stop_loss_price}.")

        # client.futures_create_order(
        #     symbol=symbol,
        #     side="SELL",
        #     type="STOP_MARKET",
        #     stopPrice=stop_loss_price,
        #     closePosition=True
        # )
        # client.futures_create_order(
        #     symbol=symbol,
        #     side="BUY",
        #     type="STOP_MARKET",
        #     stopPrice=stop_loss_price,
        #     closePosition=True
        # )
        print(f"تم تعيين وقف الخسارة عند {stop_loss_price}.")
        # تسجيل البيانات في حال أردت المتابعة لاحقًا
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "initial_price": current_price,
            "target_price": target_price,
            'stop_price': stop_loss_price,
            'start_time':str(datetime.fromtimestamp(time.time())),
            "timeout": timeout * 60,
            "investment": investment,
            "is_futuer": True
        }
        # order_response= request_load.create_trad(payload)
        _active_trades = helper.get_futuer_active_trades(client)
        active_trades = request_load.get_futuer_open_trad()
        balance = helper.get_futuer_usdt_balance(client)
        helper.update_futuer_active_trades(client)
        # __active_symbol[symbol] = payload
        print(f"عدد الصفقات المفتوحة حاليًا: {helper.get_open_positions_count(client)}")

        return payload

    except BinanceAPIException as e:
        print(f"خطأ أثناء فتح الصفقة لعملة {symbol}: {e}")
        return None


def open_trade_with_dynamic_target(symbol, investment=2.5, base_profit_target=0.002, base_stop_loss=0.0005, timeout=30):
    global balance, commission_rate, active_trades
    
    # trading_status= bot_settings.trading_status()
    # if trading_status =="0":
    #     # print("the trading is of can't open more trad")
    #     return
    # Ensure sufficient balance before opening the trade
    if balance < investment:
        # print(f"{datetime.now()} - {symbol} -الرصيد الحالي غير كافٍ لفتح صفقة جديدة.")
        return

    if not check_bnb_balance(client=client):
        print(f"{datetime.now()} - الرصيد غير كافٍ من BNB لتغطية الرسوم. {symbol} يرجى إيداع BNB.")
        return
    
    # if not can_trade(symbol=symbol):
    #     # print(f"{datetime.now()} -لقدم تم فتح صفقة حديثاً لعملة {symbol} سيتم الانتظار .")

    #     return
        
    price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    # klines = client.get_klines(symbol=symbol, interval=klines_interval, limit=analize_period)
    # closing_prices = [float(kline[4]) for kline in klines]
    # avg_volatility = statistics.stdev(closing_prices)

    # Ensure both strategies' conditions are met before opening a trade
    if not should_open_trade(client=client, symbol=symbol):
        # print(f"لا يجب شراء {symbol} في الوقت الحالي ")
        return

    # Calculate dynamic profit target and stop loss based on volatility
    profit_target = base_profit_target 
    stop_loss = base_stop_loss
    target_price = price * (1 + profit_target)
    stop_price = price * (1 - stop_loss)
    quantity = adjust_quantity(client,symbol, (investment) / price)


    try:
        # Execute the buy order
        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        commission = investment * commission_rate
        payload= {
            "symbol": symbol,
            'quantity': quantity,
            'initial_price': price,
            'target_price': target_price,
            'stop_price': stop_price,
            'start_time':str(datetime.fromtimestamp(time.time())),
            'timeout': timeout * 60,
            'investment': investment - commission
        }
        # active_trades[symbol] = {
        #     'quantity': quantity,
        #     'initial_price': price,
        #     'target_price': target_price,
        #     'stop_price': stop_price,
        #     'start_time': str(datetime.fromtimestamp(time.time())),
        #     'timeout': timeout * 60,
        #     'investment': investment - commission
        # }
        # order_response= request_load.create_trad(payload)
        # active_trades = request_load.get_futuer_open_trad()
        # if order_response:
        #     print(f"تم حفظ الصفقة بنجاح لعملة {symbol}")
        # _active_trades = helper.get_futuer_active_trades(client)
        
        balance = helper.get_usdt_balance(client)
        last_trade_time[symbol] = time.time()  # Record the trade timestamp
        print(f"{datetime.now()} - تم فتح صفقة شراء لـ {symbol} بسعر {price}, بهدف {target_price} وإيقاف خسارة عند {stop_price}")
        print(f"الرصيد المتبقي {balance}")
    except BinanceAPIException as e:
        if 'NOTIONAL' in str(e) or 'Invalid symbol' in str(e)  or 'Market is closed' in str(e):
            excluded_symbols.append(symbol)
        print(f"خطأ في فتح الصفقة لـ {symbol}: {e}")


def sell_trade(symbol, trade_quantity):
    
    try:
        # الحصول على الكمية المتاحة في المحفظة
        balance_info = client.get_asset_balance(asset=symbol.replace("USDT", ""))
        # available_quantity = float(balance_info['free'])
        available_quantity = trade_quantity
        current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])

        # التأكد من أن الكمية تلبي الحد الأدنى لـ LOT_SIZE وتعديل الدقة المناسبة
        step_size = get_lot_size(client,symbol)
        if available_quantity < step_size:
            print(f"{symbol} - الكمية المتاحة للبيع ({available_quantity}) أقل من الحد الأدنى المطلوب لـ LOT_SIZE ({step_size}).")
            return 0

        # ضبط الدقة للكمية حسب LOT_SIZE
        precision = int(round(-math.log(step_size, 10), 0))
        adjusted_quantity = round(math.floor(available_quantity / step_size) * step_size, precision)

        if adjusted_quantity < step_size:
            print(f"{symbol} - الكمية بعد التقريب ({adjusted_quantity}) لا تزال أقل من الحد الأدنى المطلوب لـ LOT_SIZE ({step_size}).")
            return 0
        # تنفيذ أمر البيع
        client.order_market_sell(symbol=symbol, quantity=adjusted_quantity)
        # sale_amount = adjusted_quantity * price
        last_trade_time[symbol] = time.time()  # Record the trade timestamp
        balance = helper.get_usdt_balance(client)
        earnings = adjusted_quantity * current_price
        print(f"تم تنفيذ عملية البيع لـ {symbol} بكمية {adjusted_quantity} وربح {earnings}")
        print(f"الرصيد المتبقي {balance}")

        return adjusted_quantity
    except BinanceAPIException as e:
        print(f"خطأ في بيع {symbol}: {e}")
        return 0

def check_trade_conditions():
    global balance,active_trades
    
    for symbol, trade in list(active_trades.items()):
        try:
            
            ticker = client.futures_symbol_ticker(symbol=symbol)
            if not ticker:
                continue
            # print(ticker)
            current_price = float(ticker['price'])
            current_prices[symbol] = current_price
        except BinanceAPIException as e:
            print(f"خطأ في تحديث السعر لـ {symbol}: {e}")
            continue
        # trade = active_trades[symbol]
        # Check for target, stop loss, or timeout conditions
        result = None
        sold_quantity = 0
        total_sale = 0
        # close_all= bot_settings.colose_all_status()
        # if close_all =="0":
        #     # print("the trading is of can't open more trad")
        #     return
        try:
            if current_price >= trade['target_price']:
                # sold_quantity = sell_trade(symbol, trade['quantity'])
                result = 'ربح' if sold_quantity > 0 else None
            elif current_price <= trade['stop_price']:
                # sold_quantity = sell_trade(symbol, trade['quantity'])
                result = 'خسارة' if sold_quantity > 0 else None
            # elif time.time() - trade['start_time'] >= trade['timeout']:
            #     sold_quantity = sell_trade(symbol, trade['quantity'])
            #     result = 'انتهاء المهلة' if sold_quantity > 0 else None
            # elif helper.should_close_trade(client,symbol):
            #     sold_quantity = sell_trade(symbol, trade['quantity'])
            #     result = 'إيقاف اجباري' if sold_quantity > 0 else None
                
            # Handle trade results and balance update
            if result and sold_quantity > 0:
                total_sale = sold_quantity * current_price
                commission = total_sale * commission_rate
                net_sale = total_sale - commission
                update_status = request_load.close_trad(trade)

                earnings = trade['quantity'] * current_price - trade['initial_price'] * trade['quantity']
                balance = helper.get_futuer_usdt_balance(client)

                
                print(f"{datetime.now()} - تم {result} الصفقة لـ {symbol} عند السعر {current_price} وربح {earnings}")
                with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    start_time=trade['start_time']
                    
                    writer.writerow([symbol, sold_quantity, trade['initial_price'], trade['target_price'], trade['stop_price'], datetime.now(), str(trade['start_time']), base_profit_target, base_stop_loss, str(timeout) + 'm', earnings, result, balance])
                del active_trades[symbol]
                
        except BinanceAPIException as e:
            if 'NOTIONAL' in str(e) or 'Invalid symbol' in str(e) or 'Market is closed' in str(e):
                excluded_symbols.append(symbol)
            print(f"خطأ في بيع {symbol}: {e}")
            continue



# تحديث قائمة الرموز بشكل دوري
def update_symbols_periodically(interval=600):
    global symbols_to_trade,balance
    balance = helper.get_futuer_usdt_balance(client)
    print(f"الرصيد المتبقي {balance}")

    print()
    while True:
        symbols_to_trade = request_load.get_futuer_top_symbols(count_top_symbols,excluded_symbols)
        print(f"{datetime.now()} - تم تحديث قائمة العملات للتداول: {symbols_to_trade}")
        time.sleep(interval)

# مراقبة تحديث الأسعار وفتح الصفقات
def update_prices():
    global symbols_to_trade, excluded_symbols,active_trades
    active_trades = request_load.get_futuer_open_trad()

    while True:
        # check_btc= check_btc_price()
        # active_trades = request_load.get_futuer_open_trad()
    #     if balance < investment:
    # # print(f"{datetime.now()} - {symbol} -الرصيد الحالي غير كافٍ لفتح صفقة جديدة.")
    #         return
        check_btc=True
        for symbol in symbols_to_trade:
        # for symbol in test_list:
            if symbol in excluded_symbols or symbol not in valid_symbols :
                continue
            try:
                # current_prices[symbol] = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                ticker = client.futures_symbol_ticker(symbol=symbol)
                if not ticker:
                    excluded_symbols.append(symbol)  # Exclude symbols causing frequent errors
                    continue
                # print(ticker)
                current_price = float(ticker['price'])
                current_prices[symbol] = current_price

                # # print(f"تم تحديث السعر لعملة {symbol}: {current_prices[symbol]}")
                if symbol not in active_trades and check_btc:
                    helper.update_futuer_active_trades(client)
                    active_trades = request_load.get_futuer_open_trad()
                    open_futures_trade(symbol,investment=investment,leverage=leverage)
                    time.sleep(0.1)
            except BinanceAPIException as e:
                print(f"خطأ في تحديث السعر لـ {symbol}: {e}")
                if 'NOTIONAL' in str(e) or 'Invalid symbol' in str(e):
                    excluded_symbols.append(symbol)  # Exclude symbols causing frequent errors
                    time.sleep(0.1)
        time.sleep(0.1)

# مراقبة حالة الصفقات المغلقة
def monitor_trades():
    while True:
        check_trade_conditions()
        time.sleep(0.1)


# load_open_trades_from_portfolio()


# load_open_trades_from_portfolio()
# بدء التحديث الدوري لقائمة العملات
def run_bot():
    global symbols_to_trade
    print(f"عدد الصفقات المفتوحة حاليًا: {helper.get_open_positions_count(client)}")
    helper.update_futuer_active_trades(client)
    symbols_to_trade = request_load.get_futuer_top_symbols(count_top_symbols,excluded_symbols)
    print(symbols_to_trade)
    symbol_update_thread = threading.Thread(target=update_symbols_periodically, args=(600,))
    symbol_update_thread.start()
    # print(active_trades)

    # تشغيل خيوط تحديث الأسعار ومراقبة الصفقات
    price_thread = threading.Thread(target=update_prices)
    trade_thread = threading.Thread(target=monitor_trades)
    price_thread.start()
    trade_thread.start()

    print(f"تم بدء تشغيل البوت في {datetime.now()}")
    
if __name__ == "__main__":
    run_bot()
    update_futuer_active_trades(client)
    # print(get_open_positions_count(client))
            
            
    print("Bot is turn of")