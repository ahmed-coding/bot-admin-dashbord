# This file will contain the implementation of the best trading strategy.
# It will combine elements from existing strategies and incorporate best practices.


### Proposed Best Strategy: Combined Indicator and Risk Management
"""
This strategy combines the Bollinger Bands/RSI and EMA Crossover strategies, enhancing them with dynamic risk management techniques. It aims to capture significant price movements while managing risk effectively.
This strategy aims to leverage the strengths of both Bollinger Bands/RSI and EMA Crossover strategies, while incorporating crucial risk management principles.

**1. Entry Conditions (Long/Buy):**
*   **Bollinger Band Squeeze Breakout (Bullish):** Price breaks above the upper Bollinger Band after a period of low volatility (squeeze).
*   **EMA Crossover (Bullish):** Short-term EMA (e.g., 9-period) crosses above a longer-term EMA (e.g., 21-period).
*   **RSI Confirmation:** RSI is above 50 and trending upwards, indicating bullish momentum.
*   **Volume Confirmation:** Increased trading volume during the breakout/crossover.

**2. Entry Conditions (Short/Sell):**
*   **Bollinger Band Squeeze Breakout (Bearish):** Price breaks below the lower Bollinger Band after a period of low volatility (squeeze).
*   **EMA Crossover (Bearish):** Short-term EMA (e.g., 9-period) crosses below a longer-term EMA (e.g., 21-period).
*   **RSI Confirmation:** RSI is below 50 and trending downwards, indicating bearish momentum.
*   **Volume Confirmation:** Increased trading volume during the breakdown/crossover.

**3. Exit Conditions:**
*   **Take Profit (Dynamic):** A percentage-based take-profit target, adjusted by recent volatility (e.g., Average True Range - ATR). This allows for larger profits in volatile markets and smaller, more achievable targets in calmer markets.
*   **Stop Loss (Dynamic):** A percentage-based stop-loss, also adjusted by ATR. This helps in managing risk effectively based on market conditions.
*   **Trailing Stop Loss:** Once a trade moves into profit, a trailing stop loss can be implemented to lock in gains while allowing for further upside.
*   **Time-based Exit:** If a trade remains open for an extended period without reaching either profit or stop-loss, it might be closed to free up capital.

**4. Risk Management:**
*   **Position Sizing:** Implement a fixed percentage of capital per trade (e.g., 1-2% of total capital per trade) to control risk exposure.
*   **Maximum Open Positions:** Limit the number of concurrent open trades to avoid over-leveraging.
*   **Daily Loss Limit:** Implement a daily loss limit to prevent significant drawdowns.

**5. Market Regime Filter:**
*   **Trend Identification:** Use a longer-term EMA (e.g., 50-period or 200-period) to identify the prevailing market trend. Only take long trades in an uptrend and short trades in a downtrend.
"""
# Implementation of the Best Strategy

import pandas as pd
import ta
from binance.client import Client

def should_open_best_trade(client: Client, symbol: str, intervel: str, limit: int):
    klines = client.futures_klines(symbol=symbol, interval=intervel, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])

    # Bollinger Bands
    df['bb_bbm'] = ta.volatility.bollinger_mavg(df['close'])
    df['bb_bbh'] = ta.volatility.bollinger_hband(df['close'])
    df['bb_bbl'] = ta.volatility.bollinger_lband(df['close'])
    df['bb_width'] = ta.volatility.bollinger_wband(df['close'])

    # EMA Crossover
    df['ema_short'] = ta.trend.ema_indicator(df['close'], window=9)
    df['ema_long'] = ta.trend.ema_indicator(df['close'], window=21)

    # RSI
    df['rsi'] = ta.momentum.rsi(df['close'], window=8)

    # ATR for dynamic stop loss/take profit
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)

    # Market Trend (using 50-period EMA)
    df['ema_trend'] = ta.trend.ema_indicator(df['close'], window=50)

    last_row = df.iloc[-1]
    second_last_row = df.iloc[-2]

    # Bullish conditions
    bullish_bb_breakout = last_row['close'] > last_row['bb_bbh'] and second_last_row['close'] <= second_last_row['bb_bbh']
    bullish_ema_crossover = last_row['ema_short'] > last_row['ema_long'] and second_last_row['ema_short'] <= second_last_row['ema_long']
    bullish_rsi = last_row['rsi'] > 20 and last_row['rsi'] < 45 and last_row['rsi'] > second_last_row['rsi']
    uptrend = last_row['close'] > last_row['ema_trend']

    # Bearish conditions
    bearish_bb_breakout = last_row['close'] < last_row['bb_bbl'] and second_last_row['close'] >= second_last_row['bb_bbl']
    bearish_ema_crossover = last_row['ema_short'] < last_row['ema_long'] and second_last_row['ema_short'] >= second_last_row['ema_long']
    bearish_rsi = last_row['rsi'] > 70 and last_row['rsi'] < second_last_row['rsi']
    downtrend = last_row['close'] < last_row['ema_trend']
    
    recent_avg_volume = df['volume'][-20:-1].mean()
    volume_confirm = last_row['volume'] > 1.2 * recent_avg_volume
    # Determine trade signal and side
    confirm = False
    side = None
    # print(f"RSI Bearish: {bearish_rsi} and RSI Bullish: {bullish_rsi}")
    # print(f"Bullish conditions - BB Breakout: {bullish_bb_breakout}, EMA Crossover: {bullish_ema_crossover}, RSI: {bullish_rsi}, Uptrend: {uptrend}")
    # print(f"Bearish conditions - BB Breakout: {bearish_bb_breakout}, EMA Crossover: {bearish_ema_crossover}, RSI: {bearish_rsi}, Downtrend: {downtrend}")
    # print(f"Volume Confirm: {volume_confirm}")
    # print('*'*50)
    
    # if bullish_rsi and uptrend:
    #     confirm = True
    #     side = "buy"
    # elif bearish_rsi and downtrend:
    #     confirm = True
    #     side = "sell"
        
    if bullish_bb_breakout and bullish_ema_crossover and bullish_rsi :
        confirm = True
        side = "buy"
    elif bearish_bb_breakout and bearish_ema_crossover and bearish_rsi:
        confirm = True
        side = "sell"

        
    # if bullish_bb_breakout and bullish_ema_crossover and bullish_rsi and uptrend:
    #     confirm = True
    #     side = "buy"
    # elif bearish_bb_breakout and bearish_ema_crossover and bearish_rsi and downtrend:
    #     confirm = True
    #     side = "sell"

    # if bullish_bb_breakout and bullish_ema_crossover and bullish_rsi and uptrend and volume_confirm:
    #     confirm = True
    #     side = "buy"
    # elif bearish_bb_breakout and bearish_ema_crossover and bearish_rsi and downtrend and volume_confirm:
    #     confirm = True
    #     side = "sell"

    return confirm, side


