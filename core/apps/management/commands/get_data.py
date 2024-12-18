import time
import pandas as pd
from django.core.management.base import BaseCommand
from apps.models import CandlestickData
from apps.utils import fetch_data, save_candlestick_data  # Assuming fetch_data and save_candlestick_data are in utils.py
from binance.client import Client
class Command(BaseCommand):
    help = 'Fetch historical candlestick data and save it to the database'

    def add_arguments(self, parser):
        # Allow the user to specify symbol, interval, years, and optional start_time
        parser.add_argument('symbol', type=str, help='The trading pair symbol (e.g., BTCUSDT)')
        parser.add_argument('--interval', type=str, default='1m', help='Time interval (default is 1m)')
        parser.add_argument('--years', type=int, default=5, help='Number of years of data to fetch')
        parser.add_argument('--start_time', type=int, help='Start time for fetching data (optional)')

    def handle(self, *args, **kwargs):
        # Retrieve command line arguments
        symbol = kwargs['symbol']
        interval = kwargs['interval']
        years = kwargs['years']
        start_time = kwargs.get('start_time')

        # Print start message
        self.stdout.write(f"Fetching data for {symbol} with interval {interval} for {years} years...")
        api_key = ''
        api_secret = ''

        # Fetch the data
        client = Client(api_key=api_key, api_secret=api_secret)
        df = fetch_data(client, symbol, interval, years, start_time)

        # Save the fetched data to the database
        save_candlestick_data(df, symbol, interval)

        # Print success message
        self.stdout.write(self.style.SUCCESS(f"Successfully fetched and saved data for {symbol}"))
