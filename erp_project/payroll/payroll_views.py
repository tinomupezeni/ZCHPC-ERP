from datetime import datetime
from decimal import Decimal
import requests
import re
from bs4 import BeautifulSoup
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Sum
from django.utils import timezone

# Adjust imports to match your project structure
from .payroll_models import Payroll, DailyZiGRateToUSD, TaxBracket, PayrollPeriod
from .serializers.payroll_serializers import PayrollSerializer
from .services.payroll_services import PayrollService 

class PayrollViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Payroll records.
    """
    queryset = Payroll.objects.all().select_related('employee').order_by('employee__surname')
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """
        GET /api/payrolls/?period=YYYY-MM
        Lists payroll records for a specific month.
        """
        period_str = request.query_params.get("period")
        if not period_str:
            return Response(
                {"error": "Period parameter (YYYY-MM) is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate format YYYY-MM
            year, month = period_str.split('-')
            
            # Filter by the specific month
            payrolls = self.get_queryset().filter(
                period__year=year, 
                period__month=month
            )
            
            serializer = self.get_serializer(payrolls, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {"error": "Invalid period format. Use YYYY-MM"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def process(self, request):
        """
        POST /api/payrolls/process/
        Triggers the payroll engine for a specific month.
        Payload: { "month": "2025-11" }
        """
        period = request.data.get("month")
        
        if not period:
            return Response(
                {"error": "Month is required (YYYY-MM)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Call the service to calculate payrolls
            result = PayrollService.process_payroll_for_period(period)
            
            # Check if service returned a specific error dict
            if isinstance(result, dict) and "error" in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": f"Payroll processing complete for {period}",
                "details": result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Internal Error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        POST /api/payrolls/{id}/approve/
        Approves a specific payslip by ID.
        """
        try:
            payroll = self.get_object()
            
            if payroll.status == "Processed":
                return Response(
                    {"message": "Payslip is already processed"}, 
                    status=status.HTTP_200_OK
                )

            # Logic to finalize the slip
            payroll.status = "Processed"
            payroll.save()
            
            return Response(
                {"status": "Processed", "id": payroll.id}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/payrolls/summary/?period=YYYY-MM
        Returns totals for the dashboard cards.
        """
        period_str = request.query_params.get('period')
        if not period_str:
            return Response({"error": "Period required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            year, month = period_str.split('-')
            payrolls = self.get_queryset().filter(period__year=year, period__month=month)
            
            # Calculate totals
            totals = payrolls.aggregate(
                total_usd=Sum('base_salary_usd'),
                total_zig=Sum('base_salary_zig'),
                total_net_usd=Sum('net_salary_usd'),
                total_net_zig=Sum('net_salary_zig')
            )
            
            processed_count = payrolls.filter(status='Processed').count()
            
            return Response({
                "total_gross_usd": totals['total_usd'] or 0,
                "total_gross_zig": totals['total_zig'] or 0,
                "total_net_usd": totals['total_net_usd'] or 0,
                "total_net_zig": totals['total_net_zig'] or 0,
                "total_employees": payrolls.count(),
                "processed_count": processed_count
            })
        except ValueError:
             return Response({"error": "Invalid period"}, status=status.HTTP_400_BAD_REQUEST)


class CurrencyRateViewSet(viewsets.ViewSet):
    """
    ViewSet for managing daily ZiG to USD exchange rates.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        GET /api/payroll/rates/
        List all currency rates, ordered by most recent.
        """
        rates = DailyZiGRateToUSD.objects.all().order_by('-date')[:365]  # Last year
        data = [
            {
                "id": rate.id,
                "date": rate.date.isoformat(),
                "average": float(rate.average),
            }
            for rate in rates
        ]
        return Response(data)

    def create(self, request):
        """
        POST /api/payroll/rates/
        Manually add a currency rate.
        Payload: { "date": "2025-03-01", "zigRate": 25.5 }
        """
        date_str = request.data.get("date")
        zig_rate = request.data.get("zigRate")

        if not date_str or not zig_rate:
            return Response(
                {"error": "Both 'date' and 'zigRate' are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rate_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            rate_value = Decimal(str(zig_rate))

            rate, created = DailyZiGRateToUSD.objects.update_or_create(
                date=rate_date,
                defaults={"average": rate_value}
            )

            return Response({
                "id": rate.id,
                "date": rate.date.isoformat(),
                "average": float(rate.average),
                "created": created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except (ValueError, Exception) as e:
            return Response(
                {"error": f"Invalid data: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def fetch_latest(self, request):
        """
        POST /api/payroll/rates/fetch_latest/
        Fetches the latest ZiG/USD rate from RBZ API and stores it.
        """
        try:
            result = self._fetch_and_store_rate()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch rate: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def _fetch_and_store_rate():
        """
        Fetches the latest ZiG to USD rate from multiple sources.
        Primary: Zimpricecheck (reliable)
        Fallback: RBZ, then alternative APIs
        """
        today = timezone.now().date()

        # Try primary sources (Zimpricecheck, RBZ)
        fetched_rate, source = CurrencyRateViewSet._try_rbz_api()

        if fetched_rate and source:
            rate, created = DailyZiGRateToUSD.objects.update_or_create(
                date=today,
                defaults={"average": Decimal(str(fetched_rate))}
            )
            return {
                "success": True,
                "date": today.isoformat(),
                "rate": float(rate.average),
                "source": source,
                "created": created
            }

        # Try alternative API as last resort
        alt_rate = CurrencyRateViewSet._try_alternative_api()

        if alt_rate:
            rate, created = DailyZiGRateToUSD.objects.update_or_create(
                date=today,
                defaults={"average": Decimal(str(alt_rate))}
            )
            return {
                "success": True,
                "date": today.isoformat(),
                "rate": float(rate.average),
                "source": "Alternative API",
                "created": created
            }

        # Return error if no rate could be fetched
        return {
            "success": False,
            "error": "Could not fetch rate from any source. Please add manually."
        }

    @staticmethod
    def _try_rbz_api():
        """
        Try multiple sources to get the ZiG to USD exchange rate.
        Primary: Zimpricecheck (reliable, regularly updated)
        Fallback: RBZ website (has bot protection, may fail)
        """
        # Try Zimpricecheck first (most reliable)
        rate = CurrencyRateViewSet._try_zimpricecheck()
        if rate:
            return rate, "Zimpricecheck"

        # Try RBZ as fallback
        rate = CurrencyRateViewSet._try_rbz_direct()
        if rate:
            return rate, "RBZ"

        return None, None

    @staticmethod
    def _try_zimpricecheck():
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

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"Zimpricecheck returned status {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()

            # Look for patterns like "1 USD = 26.1103 ZiG" or "USD 1 = ZiG 26.1103"
            patterns = [
                r'1\s*USD\s*=\s*(\d+\.?\d*)\s*ZiG',
                r'USD\s*1\s*=\s*ZiG\s*(\d+\.?\d*)',
                r'USD\s*=\s*(\d+\.?\d*)\s*ZiG',
                r'(\d+\.?\d*)\s*ZiG\s*per\s*USD',
                r'Official.*?(\d{2}\.\d{4})',  # Matches rates like 26.1103
            ]

            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    rate = float(match.group(1))
                    # ZiG rates are typically between 20-50 per USD currently
                    if 10 < rate < 100:
                        print(f"Zimpricecheck rate found: {rate}")
                        return rate

            # Also try finding in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                    if 'USD' in row_text.upper() or 'OFFICIAL' in row_text.upper():
                        # Extract decimal numbers that look like exchange rates
                        matches = re.findall(r'(\d{2}\.\d{2,4})', row_text)
                        for match in matches:
                            rate = float(match)
                            if 10 < rate < 100:
                                print(f"Zimpricecheck table rate found: {rate}")
                                return rate

            return None

        except Exception as e:
            print(f"Zimpricecheck scraping error: {e}")
            return None

    @staticmethod
    def _try_rbz_direct():
        """
        Try scraping RBZ website directly (may fail due to bot protection).
        """
        try:
            url = "https://www.rbz.co.zw/index.php/research/markets/exchange-rates"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Check if we got a bot protection page
            if 'validate.perfdrive.com' in response.text or 'captcha' in response.text.lower():
                print("RBZ has bot protection active")
                return None

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
                                    return rate

            return None

        except Exception as e:
            print(f"RBZ scraping error: {e}")
            return None

    @staticmethod
    def _try_alternative_api():
        """
        Try fetching from alternative exchange rate APIs as fallback.
        """
        try:
            # Try exchangerate.host (free, no key required)
            response = requests.get(
                "https://api.exchangerate.host/latest",
                params={"base": "USD", "symbols": "ZWL,ZWG"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                # Try ZWG (Zimbabwe Gold) first, then ZWL
                if "ZWG" in rates:
                    return rates["ZWG"]
                if "ZWL" in rates:
                    return rates["ZWL"]

            return None
        except Exception:
            return None

    def destroy(self, request, pk=None):
        """
        DELETE /api/payroll/rates/{id}/
        Delete a specific rate record.
        """
        try:
            rate = DailyZiGRateToUSD.objects.get(pk=pk)
            rate.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DailyZiGRateToUSD.DoesNotExist:
            return Response(
                {"error": "Rate not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class TaxBracketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Tax Brackets.
    GET /api/tax-brackets/ - List all tax brackets
    POST /api/tax-brackets/ - Create a new tax bracket
    GET /api/tax-brackets/{id}/ - Retrieve a tax bracket
    PUT /api/tax-brackets/{id}/ - Update a tax bracket
    DELETE /api/tax-brackets/{id}/ - Delete a tax bracket
    """
    queryset = TaxBracket.objects.all().order_by('currency', 'min_income')
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """List all tax brackets, optionally filtered by currency."""
        currency = request.query_params.get('currency')
        queryset = self.get_queryset()

        if currency:
            queryset = queryset.filter(currency=currency.upper())

        data = [
            {
                "id": bracket.id,
                "currency": bracket.currency,
                "min_income": float(bracket.min_income),
                "max_income": float(bracket.max_income) if bracket.max_income else None,
                "rate": float(bracket.rate),
                "deduction": float(bracket.deduction),
                "active_from": bracket.active_from.isoformat() if bracket.active_from else None,
            }
            for bracket in queryset
        ]
        return Response(data)

    def create(self, request):
        """Create a new tax bracket."""
        try:
            bracket = TaxBracket.objects.create(
                currency=request.data.get('currency', 'USD'),
                min_income=request.data.get('min_income', 0),
                max_income=request.data.get('max_income'),
                rate=request.data.get('rate', 0),
                deduction=request.data.get('deduction', 0),
                active_from=request.data.get('active_from'),
            )
            return Response({
                "id": bracket.id,
                "currency": bracket.currency,
                "min_income": float(bracket.min_income),
                "max_income": float(bracket.max_income) if bracket.max_income else None,
                "rate": float(bracket.rate),
                "deduction": float(bracket.deduction),
                "active_from": bracket.active_from.isoformat() if bracket.active_from else None,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a tax bracket."""
        try:
            bracket = TaxBracket.objects.get(pk=pk)
            bracket.currency = request.data.get('currency', bracket.currency)
            bracket.min_income = request.data.get('min_income', bracket.min_income)
            bracket.max_income = request.data.get('max_income', bracket.max_income)
            bracket.rate = request.data.get('rate', bracket.rate)
            bracket.deduction = request.data.get('deduction', bracket.deduction)
            if 'active_from' in request.data:
                bracket.active_from = request.data.get('active_from')
            bracket.save()
            return Response({
                "id": bracket.id,
                "currency": bracket.currency,
                "min_income": float(bracket.min_income),
                "max_income": float(bracket.max_income) if bracket.max_income else None,
                "rate": float(bracket.rate),
                "deduction": float(bracket.deduction),
                "active_from": bracket.active_from.isoformat() if bracket.active_from else None,
            })
        except TaxBracket.DoesNotExist:
            return Response({"error": "Tax bracket not found"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Delete a tax bracket."""
        try:
            bracket = TaxBracket.objects.get(pk=pk)
            bracket.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TaxBracket.DoesNotExist:
            return Response({"error": "Tax bracket not found"}, status=status.HTTP_404_NOT_FOUND)


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Payroll Periods.
    GET /api/payroll-periods/ - List all payroll periods
    POST /api/payroll-periods/ - Create a new payroll period
    PUT /api/payroll-periods/{id}/ - Update a payroll period
    DELETE /api/payroll-periods/{id}/ - Delete a payroll period
    """
    queryset = PayrollPeriod.objects.all().order_by('name')
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """List all payroll periods."""
        periods = self.get_queryset()
        data = [
            {
                "id": period.id,
                "name": period.name,
                "frequency_in_days": period.frequency_in_days,
                "start_date": period.start_date.isoformat() if period.start_date else None,
                "end_date": period.end_date.isoformat() if period.end_date else None,
                "status": period.status,
            }
            for period in periods
        ]
        return Response(data)

    def create(self, request):
        """Create a new payroll period."""
        try:
            period = PayrollPeriod.objects.create(
                name=request.data.get('name'),
                frequency_in_days=request.data.get('frequency_in_days', 30),
                start_date=request.data.get('start_date'),
                end_date=request.data.get('end_date'),
                status=request.data.get('status', 'Open'),
            )
            return Response({
                "id": period.id,
                "name": period.name,
                "frequency_in_days": period.frequency_in_days,
                "start_date": period.start_date.isoformat() if period.start_date else None,
                "end_date": period.end_date.isoformat() if period.end_date else None,
                "status": period.status,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a payroll period."""
        try:
            period = PayrollPeriod.objects.get(pk=pk)
            period.name = request.data.get('name', period.name)
            period.frequency_in_days = request.data.get('frequency_in_days', period.frequency_in_days)
            period.start_date = request.data.get('start_date', period.start_date)
            period.end_date = request.data.get('end_date', period.end_date)
            period.status = request.data.get('status', period.status)
            period.save()
            return Response({
                "id": period.id,
                "name": period.name,
                "frequency_in_days": period.frequency_in_days,
                "start_date": period.start_date.isoformat() if period.start_date else None,
                "end_date": period.end_date.isoformat() if period.end_date else None,
                "status": period.status,
            })
        except PayrollPeriod.DoesNotExist:
            return Response({"error": "Payroll period not found"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Delete a payroll period."""
        try:
            period = PayrollPeriod.objects.get(pk=pk)
            period.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PayrollPeriod.DoesNotExist:
            return Response({"error": "Payroll period not found"}, status=status.HTTP_404_NOT_FOUND)