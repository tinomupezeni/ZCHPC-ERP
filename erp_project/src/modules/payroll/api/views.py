"""
Payroll API views.

Views only translate HTTP into application inputs. Object-level authorization
(the payroll policy) is enforced inside the application services; their
AuthorizationError becomes 401/403 here via ``error_response``.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from modules.payroll.domain.value_objects import PayrollPeriod
from modules.payroll.application.services import (
    PayrollService,
    ProcessPayrollCommand,
)
from modules.payroll.application.services.employee_payroll_data_service import (
    EmployeePayrollDataService,
)
from modules.payroll.application.services.payroll_configuration_service import (
    PayrollConfigurationService,
)
from modules.payroll.application.services.payslip_access_service import PayslipAccessService
from modules.payroll.api.actors import payroll_actor_from_request
from modules.payroll.api.errors import error_response
from modules.payroll.infrastructure.persistence.django_tax_repository import DjangoTaxTableRepository
from modules.payroll.infrastructure.persistence.django_exchange_rate_repository import DjangoExchangeRateRepository
from modules.payroll.infrastructure.persistence.django_payslip_repository import DjangoPayslipRepository
from modules.payroll.infrastructure.persistence.django_allowance_repository import (
    DjangoEmployeeAllowanceRepository,
    DjangoEmployeeDeductionRepository,
)
from modules.payroll.infrastructure.persistence.django_payroll_repository import DjangoPayrollRepository
from modules.payroll.infrastructure.persistence.django_employee_payroll_provider import (
    DjangoEmployeePayrollInfoProvider,
)
from modules.payroll.api.serializers import (
    TaxBracketSerializer,
    CreateTaxBracketSerializer,
    ExchangeRateSerializer,
    CreateExchangeRateSerializer,
    PayslipListSerializer,
    AllowanceTypeSerializer,
    DeductionTypeSerializer,
    PayrollProfileSerializer,
    StatutoryProfileSerializer,
    EmployeeBankAccountSerializer,
)
from shared.domain.exceptions import AuthorizationError, DomainException

_configuration = PayrollConfigurationService()
_payslips = PayslipAccessService()
_employee_data = EmployeePayrollDataService()


# ============================================================
# Tax Bracket Views
# ============================================================

class TaxBracketListView(APIView):
    """List and create tax brackets."""

    def get(self, request):
        """List all tax brackets."""
        try:
            brackets = _configuration.list_tax_brackets(
                payroll_actor_from_request(request), request.query_params.get("currency")
            )
        except DomainException as e:
            return error_response(e)
        return Response(TaxBracketSerializer(brackets, many=True).data)

    def post(self, request):
        """Create a new tax bracket."""
        serializer = CreateTaxBracketSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            bracket = _configuration.create_tax_bracket(
                payroll_actor_from_request(request), serializer.validated_data
            )
        except DomainException as e:
            return error_response(e)

        return Response(TaxBracketSerializer(bracket).data, status=status.HTTP_201_CREATED)


class TaxBracketDetailView(APIView):
    """Retrieve, update, or delete a tax bracket."""

    def get(self, request, bracket_id):
        """Get a specific tax bracket."""
        try:
            bracket = _configuration.get_tax_bracket(payroll_actor_from_request(request), bracket_id)
        except DomainException as e:
            return error_response(e)
        return Response(TaxBracketSerializer(bracket).data)

    def put(self, request, bracket_id):
        """Update a tax bracket."""
        serializer = CreateTaxBracketSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            bracket = _configuration.update_tax_bracket(
                payroll_actor_from_request(request), bracket_id, serializer.validated_data
            )
        except DomainException as e:
            return error_response(e)
        return Response(TaxBracketSerializer(bracket).data)

    def delete(self, request, bracket_id):
        """Delete a tax bracket."""
        try:
            _configuration.delete_tax_bracket(payroll_actor_from_request(request), bracket_id)
        except AuthorizationError as e:
            return error_response(e)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# Exchange Rate Views
# ============================================================

class ExchangeRateListView(APIView):
    """List and create exchange rates."""

    def get(self, request):
        """List exchange rates (last 365 days by default)."""
        limit = int(request.query_params.get("limit", 365))
        try:
            rates = _configuration.list_exchange_rates(payroll_actor_from_request(request), limit)
        except DomainException as e:
            return error_response(e)
        return Response(ExchangeRateSerializer(rates, many=True).data)

    def post(self, request):
        """Create a new exchange rate."""
        serializer = CreateExchangeRateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            rate = _configuration.save_exchange_rate(
                payroll_actor_from_request(request), data["date"], data["zigRate"]
            )
        except DomainException as e:
            return error_response(e)

        return Response(ExchangeRateSerializer(rate).data, status=status.HTTP_201_CREATED)


class ExchangeRateDetailView(APIView):
    """Retrieve or delete a specific exchange rate."""

    def get(self, request, rate_id):
        """Get a specific exchange rate."""
        try:
            rate = _configuration.get_exchange_rate(payroll_actor_from_request(request), rate_id)
        except DomainException as e:
            return error_response(e)
        return Response(ExchangeRateSerializer(rate).data)

    def delete(self, request, rate_id):
        """Delete an exchange rate."""
        try:
            _configuration.delete_exchange_rate(payroll_actor_from_request(request), rate_id)
        except AuthorizationError as e:
            return error_response(e)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LatestExchangeRateView(APIView):
    """Get the latest exchange rate."""

    def get(self, request):
        """Get the most recent exchange rate."""
        try:
            rate = _configuration.get_latest_exchange_rate(payroll_actor_from_request(request))
        except DomainException as e:
            return error_response(e)
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

        try:
            payslips = _payslips.list_payslips(
                payroll_actor_from_request(request), period.year, period.month
            )
        except DomainException as e:
            return error_response(e)

        return Response(PayslipListSerializer(payslips, many=True).data)

    def post(self, request):
        """Process payroll for a period - generates a payslip for every active employee who doesn't already have one."""
        period_str = request.data.get("month") or request.data.get("period")
        if not period_str:
            return Response(
                {"error": "month parameter required (YYYY-MM format)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            period = PayrollPeriod.from_string(period_str)
        except ValueError:
            return Response(
                {"error": "Invalid period format. Use YYYY-MM"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = PayrollService(
            payroll_repository=DjangoPayrollRepository(),
            payslip_repository=DjangoPayslipRepository(),
            tax_repository=DjangoTaxTableRepository(),
            exchange_rate_repository=DjangoExchangeRateRepository(),
            allowance_repository=DjangoEmployeeAllowanceRepository(),
            deduction_repository=DjangoEmployeeDeductionRepository(),
            employee_provider=DjangoEmployeePayrollInfoProvider(),
        )

        try:
            command = ProcessPayrollCommand(period=period, processed_by=request.user.id)
            result = service.process_payroll(command, payroll_actor_from_request(request))
        except AuthorizationError as e:
            return error_response(e)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "payroll_id": result.payroll_id,
                "total_processed": len(result.processed),
                "total_skipped": len(result.skipped),
                "total_errors": len(result.errors),
                "errors": result.errors,
            },
            status=status.HTTP_201_CREATED,
        )


class PayslipDetailView(APIView):
    """Retrieve a specific payslip."""

    def get(self, request, payslip_id):
        """Get detailed payslip information."""
        try:
            payslip = _payslips.get_payslip(payroll_actor_from_request(request), payslip_id)
        except DomainException as e:
            return error_response(e)

        # Build detailed response
        data = {
            "id": payslip.id,
            "employee_id": payslip.employee.employee_id,
            "employee_name": f"{payslip.employee.first_name} {payslip.employee.surname}",
            "department": getattr(payslip.employee.department, "name", "N/A"),
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
            payslip = _payslips.approve_payslip(payroll_actor_from_request(request), payslip_id)
        except DomainException as e:
            return error_response(e)

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

        try:
            summary = _payslips.get_period_summary(
                payroll_actor_from_request(request), period.year, period.month
            )
        except DomainException as e:
            return error_response(e)

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
        try:
            types = _configuration.list_allowance_types(payroll_actor_from_request(request))
        except DomainException as e:
            return error_response(e)
        return Response(AllowanceTypeSerializer(types, many=True).data)

    def post(self, request):
        """Create a new allowance type."""
        serializer = AllowanceTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            allowance_type = _configuration.create_allowance_type(
                payroll_actor_from_request(request),
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description", ""),
                amount=serializer.validated_data.get("default_amount", 0),
            )
        except DomainException as e:
            return error_response(e)

        return Response(
            AllowanceTypeSerializer(allowance_type).data,
            status=status.HTTP_201_CREATED
        )


class DeductionTypeListView(APIView):
    """List and create deduction types."""

    def get(self, request):
        """List all deduction types."""
        try:
            types = _configuration.list_deduction_types(payroll_actor_from_request(request))
        except DomainException as e:
            return error_response(e)
        return Response(DeductionTypeSerializer(types, many=True).data)

    def post(self, request):
        """Create a new deduction type."""
        serializer = DeductionTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            deduction_type = _configuration.create_deduction_type(
                payroll_actor_from_request(request),
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description", ""),
                amount=serializer.validated_data.get("default_amount", 0),
            )
        except DomainException as e:
            return error_response(e)

        return Response(
            DeductionTypeSerializer(deduction_type).data,
            status=status.HTTP_201_CREATED
        )


# ============================================================
# Per-employee payroll data (profile, statutory, bank accounts)
# ============================================================

class PayrollProfileDetailView(APIView):
    def get(self, request, employee_id):
        try:
            profile = _employee_data.get_payroll_profile(payroll_actor_from_request(request), employee_id)
        except DomainException as e:
            return error_response(e)
        return Response(PayrollProfileSerializer(profile).data)

    def put(self, request, employee_id):
        serializer = PayrollProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        try:
            profile = _employee_data.update_payroll_profile(
                payroll_actor_from_request(request), employee_id, serializer.validated_data
            )
        except DomainException as e:
            return error_response(e)
        return Response(PayrollProfileSerializer(profile).data)


class StatutoryProfileDetailView(APIView):
    def get(self, request, employee_id):
        try:
            profile = _employee_data.get_statutory_profile(payroll_actor_from_request(request), employee_id)
        except DomainException as e:
            return error_response(e)
        return Response(StatutoryProfileSerializer(profile).data)

    def put(self, request, employee_id):
        serializer = StatutoryProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        try:
            profile = _employee_data.update_statutory_profile(
                payroll_actor_from_request(request), employee_id, serializer.validated_data
            )
        except DomainException as e:
            return error_response(e)
        return Response(StatutoryProfileSerializer(profile).data)


class EmployeeBankAccountListView(APIView):
    def get(self, request, employee_id):
        try:
            accounts = _employee_data.list_bank_accounts(payroll_actor_from_request(request), employee_id)
        except DomainException as e:
            return error_response(e)
        return Response(EmployeeBankAccountSerializer(accounts, many=True).data)

    def post(self, request, employee_id):
        serializer = EmployeeBankAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        try:
            account = _employee_data.add_bank_account(
                payroll_actor_from_request(request), employee_id, serializer.validated_data
            )
        except DomainException as e:
            return error_response(e)
        return Response(EmployeeBankAccountSerializer(account).data, status=201)
