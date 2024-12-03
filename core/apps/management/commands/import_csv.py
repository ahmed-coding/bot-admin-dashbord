import csv
from django.core.management.base import BaseCommand
from ...models import Symbol, FSymbol  # Replace with your app name

class Command(BaseCommand):
    help = 'Import trade data from two CSV files for Symbol and FSymbol models'

    def add_arguments(self, parser):
        parser.add_argument('symbol_csv', type=str, help='Path to the CSV file for Symbol model')
        parser.add_argument('fsymbol_csv', type=str, help='Path to the CSV file for FSymbol model')

    def handle(self, *args, **options):
        symbol_csv = options['symbol_csv']
        fsymbol_csv = options['fsymbol_csv']

        try:
            # Import data for Symbol model
            self.import_csv_to_model(symbol_csv, Symbol, 'Symbol')

            # Import data for FSymbol model
            self.import_csv_to_model(fsymbol_csv, FSymbol, 'FSymbol')

            self.stdout.write(self.style.SUCCESS("Data imported successfully for both models"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing data: {e}"))

    def import_csv_to_model(self, csv_file, model_class, model_name):
        try:
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)

                # Clear existing data for the model
                model_class.objects.all().delete()

                data_list = []
                for row in reader:
                    instance = model_class(
                        symbol=row['Symbol'],
                        return_value=self.parse_float(row.get('Return', '0')),
                        trades=self.parse_int(row.get('Trades', '0')),
                        win_rate=self.parse_float(row.get('Win Rate', '0')),
                        best_trade=self.parse_float(row.get('Best Trade', '0')),
                        worst_trade=self.parse_float(row.get('Worst Trade', '0')),
                        max_duration=row.get('Max Duration', ''),
                        avg_duration=row.get('Avg Duration', '')
                    )
                    data_list.append(instance)

                # Bulk create the data
                model_class.objects.bulk_create(data_list)
                self.stdout.write(self.style.SUCCESS(f"Data imported successfully for {model_name} model from {csv_file}"))

        except Exception as e:
            raise Exception(f"Failed to import data for {model_name}: {e}")

    def parse_float(self, value):
        """Convert a value to float, return 0.0 if it's invalid or empty."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def parse_int(self, value):
        """Convert a value to int, return 0 if it's invalid or empty."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

