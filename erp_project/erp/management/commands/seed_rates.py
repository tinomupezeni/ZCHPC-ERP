import csv
from django.core.management.base import BaseCommand
from ...models import DailyZiGRateToUSD  # adjust if your app name is different
from django.utils.dateparse import parse_date
from decimal import Decimal


class Command(BaseCommand):
    help = "Seed DailyZiGRateToUSD data from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the CSV file containing Date and USD Mid Rate columns",
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        with open(csv_file, newline="", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            print("CSV Headers:", reader.fieldnames)  # 👈 Add this line
            count = 0
            for row in reader:
                date = parse_date(row["Date"])
                avg = Decimal(row["USD Mid Rate"])

                obj, created = DailyZiGRateToUSD.objects.update_or_create(
                    date=date,
                    defaults={"average": avg},
                )
                count += 1

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Inserted {obj}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Updated {obj}"))

            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully processed {count} records")
            )
