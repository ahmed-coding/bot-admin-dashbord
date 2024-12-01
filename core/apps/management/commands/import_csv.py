import csv
from django.core.management.base import BaseCommand
from ...models import Symbol  # Replace 'myapp' with your app name

class Command(BaseCommand):
    help = 'Import trade data from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file to be imported')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        try:
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    Symbol.objects.get_or_create(
                        symbol=row['Symbol'],
                        return_value=float(row['Return']),
                        trades=int(row['Trades']),
                        win_rate=float(row['Win Rate'] or '0'),
                        best_trade=float(row['Best Trade']  or '0'),
                        worst_trade=float(row['Worst Trade']  or '0'),
                        max_duration=row['Max Duration'],
                        avg_duration=row['Avg Duration']
                    )
            self.stdout.write(self.style.SUCCESS(f"Data imported successfully from {csv_file}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing data: {e}"))
