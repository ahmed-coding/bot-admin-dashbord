# import utils.request_load as request_load
# from utils.config import API_KEY, API_SECRET, FUTUER_API_TEST_KEY, FUTUER_API_TEST_SECRET
# from binance.client import Client


# def update_futuer_active_trades(client):
#     """
#     استرجاع الصفقات المفتوحة على Binance Futures وتحديث الحالة في Django.
#     """
#     active_trade = request_load.get_futuer_open_trad()
#     positions = client.futures_position_information()  # جلب جميع المراكز المفتوحة
#     # print(positions)
#     for symbol, trade in list(active_trade.items()):
#         # print(f"{symbol}")
#         for position in positions:
#             acive_symbol = position['symbol']
#             position_amt = float(position['positionAmt'])  # الكمية المفتوحة
#             # print(position['symbol'])
#             # print(acive_symbol)
#             if  position['symbol'] in symbol:
#                 print(f"trad open for {acive_symbol} ")
#                 continue
#             else:
#                 update_status = request_load.close_trad(trade)
#                 print(f"trad colse for {symbol}")
#                 break


# client = Client(API_KEY,API_SECRET,requests_params={'timeout':90})


# update_futuer_active_trades(client)




is_buy=False
is_sell = False

print(((is_buy & is_sell)))
