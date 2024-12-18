import time
import pandas as pd
from .models import CandlestickData
from django.db import transaction

def fetch_data(client, symbol, interval='1m', years=5, start_time=None):
    """
    Fetch historical candlestick data from Binance.
    """
    candles_per_day = 1440 // int(interval[:-1])  # Calculate number of candles per day
    days_in_year = 365
    total_candles = candles_per_day * days_in_year * years if not start_time else 1000

    limit = 1000
    all_data = []
    current_time = int(time.time() * 1000)
    if not start_time:
        start_time = current_time - (years * 365 * 24 * 60 * 60 * 1000)

    while total_candles > 0:
        candles = client.futures_klines(symbol=symbol, interval=interval, limit=limit, startTime=start_time)
        if not candles:
            break

        all_data.extend(candles)
        start_time = candles[-1][6]  # Update start_time for next iteration
        total_candles -= limit
        time.sleep(0.2)  # Sleep to avoid rate limit

    # Convert to DataFrame and clean up the data
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
    df['Quote_Asset_Volume'] = df['Quote_Asset_Volume'].astype(float)
    df['Taker_Buy_Base_Asset_Volume'] = df['Taker_Buy_Base_Asset_Volume'].astype(float)
    df['Taker_Buy_Quote_Asset_Volume'] = df['Taker_Buy_Quote_Asset_Volume'].astype(float)
    df['Number_Of_Trades'] = df['Number_Of_Trades'].astype(int)
    df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
    df['Change_Percentage'] = ((df['High'] - df['Open']) / df['Open']) * 100

    return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Quote_Asset_Volume', 'Taker_Buy_Base_Asset_Volume',
               'Taker_Buy_Quote_Asset_Volume', 'Number_Of_Trades', 'Change_Percentage']]

def save_candlestick_data(df, symbol, interval):
    """
    Save the fetched candlestick data to the database in chunks.
    """
    candlestick_objects = []
    for _, row in df.iterrows():
        candlestick_objects.append(
            CandlestickData(
                symbol=symbol,
                interval=interval,
                open_time=row['Open_Time'],
                open_price=row['Open'],
                high_price=row['High'],
                low_price=row['Low'],
                close_price=row['Close'],
                volume=row['Volume'],
                quote_asset_volume=row['Quote_Asset_Volume'],
                taker_buy_base_asset_volume=row['Taker_Buy_Base_Asset_Volume'],
                taker_buy_quote_asset_volume=row['Taker_Buy_Quote_Asset_Volume'],
                number_of_trades=row['Number_Of_Trades'],
                change_percentage=row['Change_Percentage']
            )
        )

    # Insert the candlestick data in chunks to avoid memory overload
    with transaction.atomic():  # Ensures that the insertion is atomic
        CandlestickData.objects.bulk_create(candlestick_objects, batch_size=1000)
