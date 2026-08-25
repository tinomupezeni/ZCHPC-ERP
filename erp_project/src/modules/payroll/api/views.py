"""
Payroll API views.
"""

from datetime import date, datetime
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from modules.payroll.infrastructure.persistence.models import (
    TaxBracket as TaxBracketModel,
    DailyZiGRateToUSD,
    Payroll as PayrollModel,
)
from modules.hr.infrastructure.persistence.models import (
    AllowanceType as AllowanceTypeModel,
    DeductionType as DeductionTypeModel,
)

from modules.payroll.domain.value_objects import PayrollPeriod, Currency
from modules.payroll.application.services import (
    PayrollService,
    ProcessPayrollCommand,
    ExchangeRateService,
    CreateExchangeRateCommand,
)
from modules.payroll.infrastructure.persistence.django_tax_repository import DjangoTaxTableRepository
from modules.payroll.infrastructure.persistence.django_exchange_rate_repository import DjangoExchangeRateRepository
from modules.payroll.infrastructure.persistence.django_payslip_repository import DjangoPayslipRepository
from modules.payroll.infrastructure.persistence.django_allowance_repository import (
    DjangoEmployeeAllowanceRepository,
    DjangoEmployeeDeductionRepository,
)
from modules.payroll.api.serializers import (
    TaxBracketSerializer,
    CreateTaxBracketSerializer,
    ExchangeRateSerializer,
    CreateExchangeRateSerializer,
    PayslipSerializer,
    PayslipListSerializer,
    ProcessPayrollSerializer,
    PayrollSummarySerializer,
    AllowanceTypeSerializer,
    DeductionTypeSerializer,
)


# ============================================================
# Tax Bracket Views
# ============================================================

class TaxBracketListView(APIView):
    """List and create tax brackets."""

    def get(self, request):
        """List all tax brackets."""
        currency = request.query_params.get("currency")

        queryset = TaxBracketModel.objects.all().order_by(
            "currency", "min_income", "-active_from"
        )

        if currency:
            queryset = queryset.filter(currency=currency.upper())

        serializer = TaxBracketSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new tax bracket."""
        serializer = CreateTaxBracketSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        bracket = TaxBracketModel.objects.create(
            currency=data["currency"],
            min_income=data["min_income"],
            max_income=data.get("max_income"),
            rate=data["rate"],
            deduction=data["deduction"],
            active_from=data["active_from"],
            provider=data.get("provider", "")
        )

        return Response(
            TaxBracketSerializer(bracket).data,
            status=status.HTTP_201_CREATED
        )


class TaxBracketDetailView(APIView):
    """Retrieve, update, or delete a tax bracket."""

    def get(self, request, bracket_id):
        """Get a specific tax bracket."""
        try:
            bracket = TaxBracketModel.objects.get(id=bracket_id)
            return Response(TaxBracketSerializer(bracket).data)
        except TaxBracketModel.DoesNotExist:
            return Response(
                {"error": "Tax bracket not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, bracket_id):
        """Update a tax bracket."""
        try:
            bracket = TaxBracketModel.objects.get(id=bracket_id)
        except TaxBracketModel.DoesNotExist:
            return Response(
                {"error": "Tax bracket not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CreateTaxBracketSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        for key, value in serializer.validated_data.items():
            setattr(bracket, key, value)
        bracket.save()

        return Response(TaxBracketSerializer(bracket).data)

    def delete(self, request, bracket_id):
        """Delete a tax bracket."""
        try:
            TaxBracketModel.objects.filter(id=bracket_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================
# Exchange Rate Views
# ============================================================

class ExchangeRateListView(APIView):
    """List and create exchange rates."""

    def get(self, request):
        """List exchange rates (last 365 days by default)."""
        limit = int(request.query_params.get("limit", 365))
        rates = DailyZiGRateToUSD.objects.all().order_by("-date")[:limit]
        serializer = ExchangeRateSerializer(rates, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new exchange rate."""
        serializer = CreateExchangeRateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        rate_date = data["date"]
        zig_rate = data["zigRate"]

        # Check if rate exists for this date
        existing = DailyZiGRateToUSD.objects.filter(date=rate_date).first()
        if existing:
            existing.average = zig_rate
            existing.save()
            rate = existing
        else:
            rate = DailyZiGRateToUSD.objects.create(
                date=rate_date,
                average=zig_rate
            )

        return Response(
            ExchangeRateSerializer(rate).data,
            status=status.HTTP_201_CREATED
        )


class ExchangeRateDetailView(APIView):
    """Retrieve or delete a specific exchange rate."""

    def get(self, request, rate_id):
        """Get a specific exchange rate."""
        try:
            rate = DailyZiGRateToUSD.objects.get(id=rate_id)
            return Response(ExchangeRateSerializer(rate).data)
        except DailyZiGRateToUSD.DoesNotExist:
            return Response(
                {"error": "Exchange rate not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, rate_id):
        """Delete an exchange rate."""
        try:
            DailyZiGRateToUSD.objects.filter(id=rate_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LatestExchangeRateView(APIView):
    """Get the latest exchange rate."""

    def get(self, request):
        """Get the most recent exchange rate."""
        rate = DailyZiGRateToUSD.objects.order_by("-date").first()
        if not rate:
            return Response(
                {"error": "No exchange rates available"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(ExchangeRateSerializer(rate).data)


# ============================================================
# Payslip Views
# ============================================================

class PayslipListView(APIView):
    """List payslips for a period."""

    def get(self, request):
        """List payslips, filtered by period."""
        period_str = request.query_params.get("period")
        if not period_str:
            return Response(
                {"error": "period parameter required (YYYY-MM format)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            period = PayrollPeriod.from_string(period_str)
        except ValueError:
            return Response(
                {"error": "Invalid period format. Use YYYY-MM"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payslips = PayrollModel.objects.filter(
            period__year=period.year,
            period__month=period.month
        ).select_related("employee", "employee__employment_details__department").order_by(
            "employee__employee_id"
        )

        serializer = PayslipListSerializer(payslips, many=True)
        return Response(serializer.data)


class PayslipDetailView(APIView):
    """Retrieve a specific payslip."""

    def get(self, request, payslip_id):
        """Get detailed payslip information."""
        try:
            payslip = PayrollModel.objects.select_related(
                "employee", "employee__employment_details__department"
            ).get(id=payslip_id)
        except PayrollModel.DoesNotExist:
            return Response(
                {"error": "Payslip not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Reverse OneToOne raises RelatedObjectDoesNotExist (an AttributeError
        # subclass) when absent, so getattr(..., None) is the safe accessor.
        employment_details = getattr(payslip.employee, "employment_details", None)

        # Build detailed response
        data = {
            "id": payslip.id,
            "employee_id": payslip.employee.employee_id,
            "employee_name": f"{payslip.employee.first_name} {payslip.employee.surname}",
            "department": getattr(getattr(employment_details, "department", None), "name", "N/A"),
            "period": f"{payslip.period.year}-{payslip.period.month:02d}",
            "base_salary_usd": str(payslip.base_salary_usd or 0),
            "base_salary_zig": str(payslip.base_salary_zig or 0),
            "total_allowances_usd": str(payslip.total_allowances_usd or 0),
            "total_allowances_zig": str(payslip.total_allowances_zig or 0),
            "gross_usd": str(
                (payslip.base_salary_usd or 0) + (payslip.total_allowances_usd or 0)
            ),
            "gross_zig": str(
                (payslip.base_salary_zig or 0) + (payslip.total_allowances_zig or 0)
            ),
            "paye_usd": str(payslip.paye_usd or 0),
            "paye_zig": str(payslip.paye_zig or 0),
            "aids_levy_usd": str(payslip.aids_levy_usd or 0),
            "aids_levy_zig": str(payslip.aids_levy_zig or 0),
            "nssa_employee_usd": str(payslip.nssa_employee_usd or 0),
            "nssa_employee_zig": str(payslip.nssa_employee_zig or 0),
            "nssa_employer_usd": str(payslip.nssa_employer_usd or 0),
            "nssa_employer_zig": str(payslip.nssa_employer_zig or 0),
            "other_deductions_usd": str(payslip.total_deductions_usd or 0),
            "other_deductions_zig": str(payslip.total_deductions_zig or 0),
            "net_salary_usd": str(payslip.net_salary_usd or 0),
            "net_salary_zig": str(payslip.net_salary_zig or 0),
            "exchange_rate": str(payslip.exchange_rate or 0),
            "status": payslip.status,
        }
        return Response(data)


class PayslipApproveView(APIView):
    """Approve a payslip."""

    def post(self, request, payslip_id):
        """Approve (mark as processed) a payslip."""
        try:
            payslip = PayrollModel.objects.get(id=payslip_id)
        except PayrollModel.DoesNotExist:
            return Response(
                {"error": "Payslip not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if payslip.status != "Draft":
            return Response(
                {"error": f"Cannot approve payslip in {payslip.status} status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payslip.status = "Processed"
        payslip.save()

        return Response({"id": payslip.id, "status": payslip.status})


# ============================================================
# Payroll Processing Views
# ============================================================

class PayrollSummaryView(APIView):
    """Get payroll summary for a period."""

    def get(self, request):
        """Get summary statistics for a payroll period."""
        period_str = request.query_params.get("period")
        if not period_str:
            return Response(
                {"error": "period parameter required (YYYY-MM format)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            period = PayrollPeriod.from_string(period_str)
        except ValueError:
            return Response(
                {"error": "Invalid period format. Use YYYY-MM"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Aggregate payslip data
        payslips = PayrollModel.objects.filter(
            period__year=period.year,
            period__month=period.month
        )

        if not payslips.exists():
            return Response(
                {"error": "No payroll data for this period"},
                status=status.HTTP_404_NOT_FOUND
            )

        from django.db.models import Sum, Count

        summary = payslips.aggregate(
            total_employees=Count("id"),
            total_base_usd=Sum("base_salary_usd"),
            total_base_zig=Sum("base_salary_zig"),
            total_allowances_usd=Sum("total_allowances_usd"),
            total_allowances_zig=Sum("total_allowances_zig"),
            total_net_usd=Sum("net_salary_usd"),
            total_net_zig=Sum("net_salary_zig"),
            total_paye_usd=Sum("paye_usd"),
            total_paye_zig=Sum("paye_zig"),
            total_nssa_emp_usd=Sum("nssa_employee_usd"),
            total_nssa_emp_zig=Sum("nssa_employee_zig"),
            total_nssa_employer_usd=Sum("nssa_employer_usd"),
            total_nssa_employer_zig=Sum("nssa_employer_zig"),
        )

        data = {
            "period": period.code,
            "total_employees": summary["total_employees"],
            "total_gross_usd": str(
                (summary["total_base_usd"] or 0) +
                (summary["total_allowances_usd"] or 0)
            ),
            "total_gross_zig": str(
                (summary["total_base_zig"] or 0) +
                (summary["total_allowances_zig"] or 0)
            ),
            "total_net_usd": str(summary["total_net_usd"] or 0),
            "total_net_zig": str(summary["total_net_zig"] or 0),
            "total_paye_usd": str(summary["total_paye_usd"] or 0),
            "total_paye_zig": str(summary["total_paye_zig"] or 0),
            "total_nssa_usd": str(
                (summary["total_nssa_emp_usd"] or 0) +
                (summary["total_nssa_employer_usd"] or 0)
            ),
            "total_nssa_zig": str(
                (summary["total_nssa_emp_zig"] or 0) +
                (summary["total_nssa_employer_zig"] or 0)
            ),
            "status": "Processed",
        }

        return Response(data)


# ============================================================
# Allowance & Deduction Type Views
# ============================================================

class AllowanceTypeListView(APIView):
    """List and create allowance types."""

    def get(self, request):
        """List all allowance types."""
        types = AllowanceTypeModel.objects.all().order_by("name")
        serializer = AllowanceTypeSerializer(types, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new allowance type."""
        serializer = AllowanceTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        allowance_type = AllowanceTypeModel.objects.create(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
            amount=serializer.validated_data.get("default_amount", 0)
        )

        return Response(
            AllowanceTypeSerializer(allowance_type).data,
            status=status.HTTP_201_CREATED
        )


class DeductionTypeListView(APIView):
    """List and create deduction types."""

    def get(self, request):
        """List all deduction types."""
        types = DeductionTypeModel.objects.all().order_by("name")
        serializer = DeductionTypeSerializer(types, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new deduction type."""
        serializer = DeductionTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        deduction_type = DeductionTypeModel.objects.create(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
            amount=serializer.validated_data.get("default_amount", 0)
        )

        return Response(
            DeductionTypeSerializer(deduction_type).data,
            status=status.HTTP_201_CREATED
        )

from django.shortcuts import get_object_or_404
from modules.payroll.infrastructure.persistence.models import PayrollProfile, StatutoryProfile, EmployeeBankAccount
from modules.hr.infrastructure.persistence.models import Employees
from .serializers import PayrollProfileSerializer, StatutoryProfileSerializer, EmployeeBankAccountSerializer

class PayrollProfileDetailView(APIView):
    def get(self, request, employee_id):
        profile, _ = PayrollProfile.objects.get_or_create(employee__uuid=employee_id)
        serializer = PayrollProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, employee_id):
        profile = get_object_or_404(PayrollProfile, employee__uuid=employee_id)
        serializer = PayrollProfileSerializer(data=request.data)
        if serializer.is_valid():
            for k, v in serializer.validated_data.items():
                setattr(profile, k, v)
            profile.save()
            return Response(PayrollProfileSerializer(profile).data)
        return Response(serializer.errors, status=400)

class StatutoryProfileDetailView(APIView):
    def get(self, request, employee_id):
        profile, _ = StatutoryProfile.objects.get_or_create(employee__uuid=employee_id)
        serializer = StatutoryProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, employee_id):
        profile = get_object_or_404(StatutoryProfile, employee__uuid=employee_id)
        serializer = StatutoryProfileSerializer(data=request.data)
        if serializer.is_valid():
            for k, v in serializer.validated_data.items():
                setattr(profile, k, v)
            profile.save()
            return Response(StatutoryProfileSerializer(profile).data)
        return Response(serializer.errors, status=400)

class EmployeeBankAccountListView(APIView):
    def get(self, request, employee_id):
        accounts = EmployeeBankAccount.objects.filter(employee__uuid=employee_id)
        serializer = EmployeeBankAccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request, employee_id):
        employee = get_object_or_404(Employees, uuid=employee_id)
        serializer = EmployeeBankAccountSerializer(data=request.data)
        if serializer.is_valid():
            account = EmployeeBankAccount.objects.create(employee=employee, **serializer.validated_data)
            return Response(EmployeeBankAccountSerializer(account).data, status=201)
        return Response(serializer.errors, status=400)
