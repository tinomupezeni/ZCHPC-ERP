import time
from datetime import datetime
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from erp_project.authentication.models import DailyZiGRateToUSD  # adjust import to your app

class Command(BaseCommand):
    help = "Fetch today's (or latest) ZiG/USD exchange rate from RBZ and save to DB"

    def handle(self, *args, **options):
        """
        Handles the command to fetch and save the exchange rate.
        """
        self.stdout.write("\n--- Starting ZiG/USD rate fetch ---")

        # Configure Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)

        try:
            # Navigate to the Daily Exchange Rates page
            url = "https://www.rbz.co.zw/index.php/13-daily-exchange-rates/16-rates"
            self.stdout.write(f"🌐 Navigating to {url}")
            driver.get(url)

            # Wait for the page to load completely
            self.stdout.write("⏳ Waiting for page to load...")
            time.sleep(5)

            # Use direct XPath to find the USD/ZWG rate without storing element references
            # This avoids stale element issues
            usd_rate_xpath = "//table[contains(., 'USD/ZWG')]//tr[contains(., 'USD/ZWG')]/td[4]"
            
            # Wait for the rate element to be present
            rate_element = wait.until(EC.presence_of_element_located((By.XPATH, usd_rate_xpath)))
            usd_rate = rate_element.text.strip()
            
            self.stdout.write(f"💰 Found USD/ZWG rate: {usd_rate}")
            
            # Convert to float and save
            rate = float(usd_rate)
            self.stdout.write(f"✅ Extracted rate: {rate}")
            
            # Save or update the rate in the database
            today = datetime.today().date()
            obj, created = DailyZiGRateToUSD.objects.update_or_create(
                date=today,
                defaults={"rate": rate},
            )

            if created:
                self.stdout.write(f"✅ Successfully saved new rate {rate} for {today}")
            else:
                self.stdout.write(f"🔄 Successfully updated rate {rate} for {today}")

        except TimeoutException:
            self.stdout.write("❌ Timeout: Could not find exchange rate element")
            
        except Exception as e:
            self.stdout.write(f"❌ An error occurred: {str(e)}")
            
        finally:
            driver.quit()
            self.stdout.write("--- Script finished ---")