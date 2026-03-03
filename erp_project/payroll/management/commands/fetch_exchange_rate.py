"""
Django management command to fetch the daily ZiG to USD exchange rate.

Usage:
    python manage.py fetch_exchange_rate

To run as a cron job (every day at 10 AM):
    Add to crontab: 0 10 * * * /path/to/venv/bin/python /path/to/manage.py fetch_exchange_rate

For Windows Task Scheduler:
    Create a task that runs: python manage.py fetch_exchange_rate
    Schedule: Daily at 10:00 AM
"""

import re
import requests
from decimal import Decimal
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from payroll.payroll_models import DailyZiGRateToUSD


class Command(BaseCommand):
    help = 'Fetches the daily ZiG to USD exchange rate from RBZ and stores it in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rate',
            type=float,
            help='Manually specify the rate instead of fetching from RBZ',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Specify date in YYYY-MM-DD format (default: today)',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Allow specifying a different date
        if options['date']:
            try:
                from datetime import datetime
                today = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return

        # If rate is manually specified, use that
        if options['rate']:
            rate_value = Decimal(str(options['rate']))
            self._save_rate(today, rate_value, "Manual")
            return

        # Try to fetch from RBZ first, then fallback to other sources
        self.stdout.write("Fetching exchange rate from RBZ...")
        rate, source = self._fetch_rate()

        if rate:
            self._save_rate(today, rate, source)
        else:
            self.stderr.write(
                self.style.WARNING(
                    f'Could not fetch rate for {today}. '
                    'Please add manually using: python manage.py fetch_exchange_rate --rate <value>'
                )
            )

    def _fetch_rate(self):
        """
        Try to fetch the exchange rate from multiple sources.
        Primary: Zimpricecheck (most reliable)
        Fallback: RBZ, then alternative APIs
        """
        # 1. Try Zimpricecheck (primary, most reliable)
        rate = self._scrape_zimpricecheck()
        if rate:
            return rate, "Zimpricecheck"

        # 2. Try RBZ website (may have bot protection)
        rate = self._scrape_rbz()
        if rate:
            return rate, "RBZ"

        # 3. Fallback to alternative API
        rate = self._try_alternative_api()
        if rate:
            return rate, "Alternative API"

        return None, None

    def _scrape_zimpricecheck(self):
        """
        Scrape Zimpricecheck for the official ZiG to USD exchange rate.
        This site aggregates official rates and is regularly updated.
        """
        try:
            url = "https://zimpricecheck.com/price-updates/official-and-black-market-exchange-rates/"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            self.stdout.write(f"Fetching from: {url}")
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                self.stderr.write(f"Zimpricecheck returned status code: {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()

            # Look for patterns like "1 USD = 26.1103 ZiG"
            patterns = [
                r'1\s*USD\s*=\s*(\d+\.?\d*)\s*ZiG',
                r'USD\s*1\s*=\s*ZiG\s*(\d+\.?\d*)',
                r'USD\s*=\s*(\d+\.?\d*)\s*ZiG',
                r'(\d+\.?\d*)\s*ZiG\s*per\s*USD',
                r'Official.*?(\d{2}\.\d{4})',
            ]

            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    rate = float(match.group(1))
                    if 10 < rate < 100:
                        self.stdout.write(self.style.SUCCESS(f"Found rate via Zimpricecheck: {rate}"))
                        return Decimal(str(rate))

            # Also try finding in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                    if 'USD' in row_text.upper() or 'OFFICIAL' in row_text.upper():
                        matches = re.findall(r'(\d{2}\.\d{2,4})', row_text)
                        for match in matches:
                            rate = float(match)
                            if 10 < rate < 100:
                                self.stdout.write(self.style.SUCCESS(f"Found rate in Zimpricecheck table: {rate}"))
                                return Decimal(str(rate))

            self.stderr.write("Could not find rate in Zimpricecheck")
            return None

        except requests.exceptions.Timeout:
            self.stderr.write("Zimpricecheck request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Zimpricecheck request failed: {e}")
            return None
        except Exception as e:
            self.stderr.write(f"Zimpricecheck scraping error: {e}")
            return None

    def _scrape_rbz(self):
        """
        Scrape the RBZ website for the ZiG to USD exchange rate.
        Note: RBZ has bot protection that may block automated requests.
        """
        try:
            url = "https://www.rbz.co.zw/index.php/research/markets/exchange-rates"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }

            self.stdout.write(f"Fetching from: {url}")
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                self.stderr.write(f"RBZ returned status code: {response.status_code}")
                return None

            # Check for bot protection
            if 'validate.perfdrive.com' in response.text or 'captcha' in response.text.lower():
                self.stderr.write("RBZ has bot protection active, skipping...")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for tables with exchange rate data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text(strip=True).upper() for cell in cells])

                    if 'USD' in row_text or 'DOLLAR' in row_text:
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            match = re.search(r'(\d+\.?\d*)', text.replace(',', ''))
                            if match:
                                rate = float(match.group(1))
                                if 10 < rate < 100:
                                    self.stdout.write(f"Found rate in RBZ table: {rate}")
                                    return Decimal(str(rate))

            # Look for specific text patterns
            page_text = soup.get_text()
            patterns = [
                r'USD.*?=.*?ZiG.*?(\d+\.?\d*)',
                r'ZiG.*?(\d+\.?\d*).*?USD',
                r'(\d+\.?\d*)\s*ZiG.*?per.*?USD',
            ]

            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    rate = float(match.group(1))
                    if 10 < rate < 100:
                        self.stdout.write(f"Found rate via RBZ pattern: {rate}")
                        return Decimal(str(rate))

            self.stderr.write("Could not find USD rate in RBZ page")
            return None

        except requests.exceptions.Timeout:
            self.stderr.write("RBZ request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"RBZ request failed: {e}")
            return None
        except Exception as e:
            self.stderr.write(f"RBZ scraping error: {e}")
            return None

    def _try_alternative_api(self):
        """Fallback to alternative exchange rate APIs"""
        try:
            self.stdout.write("Trying alternative API...")
            response = requests.get(
                "https://api.exchangerate.host/latest",
                params={"base": "USD", "symbols": "ZWL,ZWG"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                if "ZWG" in rates:
                    return Decimal(str(rates["ZWG"]))
                if "ZWL" in rates:
                    return Decimal(str(rates["ZWL"]))

            return None
        except Exception as e:
            self.stderr.write(f"Alternative API failed: {e}")
            return None

    def _save_rate(self, date, rate_value, source):
        """Save the rate to the database"""
        rate, created = DailyZiGRateToUSD.objects.update_or_create(
            date=date,
            defaults={"average": rate_value}
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} rate for {date}: 1 USD = {rate_value} ZiG (Source: {source})'
            )
        )
