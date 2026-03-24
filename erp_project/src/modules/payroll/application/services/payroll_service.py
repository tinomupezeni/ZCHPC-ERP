"""
Payroll application service for payroll processing.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from shared.domain.exceptions import ValidationError, NotFoundError

from modules.payroll.domain.entities import (
    Payroll,
    Payslip,
    PayrollSummary,
    EmployeeAllowance,
    EmployeeDeduction,
)
from modules.payroll.domain.value_objects import (
    PayrollPeriod,
    PayrollStatus,
    PayslipStatus,
    Currency,
)
from modules.payroll.domain.services import (
    PayslipGenerator,
    EmployeeSalaryInfo,
)
from modules.payroll.application.interfaces import (
    IPayrollRepository,
    IPayslipRepository,
    ITaxTableRepository,
    IExchangeRateRepository,
    IEmployeeAllowanceRepository,
    IEmployeeDeductionRepository,
    IEmployeePayrollInfoProvider,
)


@dataclass
class ProcessPayrollCommand:
    """Command to process payroll for a period."""

    period: PayrollPeriod
    processed_by: int  # User ID


@dataclass
class ProcessPayrollResult:
    """Result of payroll processing."""

    payroll_id: int
    processed: List[int]  # Employee IDs
    skipped: List[int]  # Employee IDs (already have payslip)
    errors: List[dict]  # {employee_id, error}


class PayrollService:
    """
    Application service for payroll processing.

    Orchestrates the generation of payslips for all active employees.
    """

    def __init__(
        self,
        payroll_repository: IPayrollRepository,
        payslip_repository: IPayslipRepository,
        tax_repository: ITaxTableRepository,
        exchange_rate_repository: IExchangeRateRepository,
        allowance_repository: IEmployeeAllowanceRepository,
        deduction_repository: IEmployeeDeductionRepository,
        employee_provider: IEmployeePayrollInfoProvider,
        payslip_generator: PayslipGenerator = None
    ):
        self.payroll_repo = payroll_repository
        self.payslip_repo = payslip_repository
        self.tax_repo = tax_repository
        self.rate_repo = exchange_rate_repository
        self.allowance_repo = allowance_repository
        self.deduction_repo = deduction_repository
        self.employee_provider = employee_provider
        self.generator = payslip_generator or PayslipGenerator()

    def get_or_create_payroll(self, period: PayrollPeriod) -> Payroll:
        """Get existing payroll or create new one."""
        existing = self.payroll_repo.get_by_period(period)
        if existing:
            return existing

        payroll = Payroll.create(period)
        return self.payroll_repo.save(payroll)

    def process_payroll(self, command: ProcessPayrollCommand) -> ProcessPayrollResult:
        """
        Process payroll for all active employees.

        Args:
            command: ProcessPayrollCommand with period and user info

        Returns:
            ProcessPayrollResult with processing details
        """
        # Get or create payroll
        payroll = self.get_or_create_payroll(command.period)

        if not payroll.can_process:
            raise ValidationError(
                f"Cannot process payroll in {payroll.status.value} status"
            )

        # Start processing
        payroll.start_processing(command.processed_by)
        self.payroll_repo.save(payroll)

        # Get required data
        exchange_rate = self.rate_repo.get_latest()
        if not exchange_rate:
            raise ValidationError("No exchange rate available for payroll processing")

        usd_tax_table = self.tax_repo.get_active_for_currency(
            Currency.USD, date.today()
        )
        zig_tax_table = self.tax_repo.get_active_for_currency(
            Currency.ZIG, date.today()
        )

        if not usd_tax_table:
            raise ValidationError("No USD tax table available")

        # Get active employees
        employee_ids = self.employee_provider.get_active_employee_ids()

        processed = []
        skipped = []
        errors = []
        payslips = []

        for emp_id in employee_ids:
            # Check if payslip already exists
            existing = self.payslip_repo.get_by_employee_and_period(
                emp_id, command.period
            )
            if existing:
                skipped.append(emp_id)
                continue

            try:
                payslip = self._generate_employee_payslip(
                    employee_id=emp_id,
                    period=command.period,
                    payroll_id=payroll.id,
                    usd_tax_table=usd_tax_table,
                    zig_tax_table=zig_tax_table or usd_tax_table,
                    exchange_rate=exchange_rate
                )
                payslips.append(payslip)
                processed.append(emp_id)
            except Exception as e:
                errors.append({"employee_id": emp_id, "error": str(e)})

        # Save all payslips
        if payslips:
            self.payslip_repo.save_batch(payslips)

        # Calculate summary
        summary = self._calculate_summary(payslips)
        payroll.complete_processing(summary)
        self.payroll_repo.save(payroll)

        return ProcessPayrollResult(
            payroll_id=payroll.id,
            processed=processed,
            skipped=skipped,
            errors=errors
        )

    def _generate_employee_payslip(
        self,
        employee_id: int,
        period: PayrollPeriod,
        payroll_id: int,
        usd_tax_table,
        zig_tax_table,
        exchange_rate
    ) -> Payslip:
        """Generate a payslip for a single employee."""
        # Get employee info
        emp_info = self.employee_provider.get_employee_salary_info(employee_id)

        # Get allowances and deductions
        allowances = self.allowance_repo.get_by_employee(employee_id)
        deductions = self.deduction_repo.get_by_employee(employee_id)

        salary_info = EmployeeSalaryInfo(
            employee_id=employee_id,
            employee_name=emp_info.get("employee_name", ""),
            usd_salary=Decimal(str(emp_info.get("usd_salary", 0) or 0)),
            zig_salary=Decimal(str(emp_info.get("zig_salary", 0) or 0)),
            pays_aids_levy=emp_info.get("pays_aids_levy", True),
            allowances=allowances,
            deductions=deductions
        )

        return self.generator.generate(
            employee_info=salary_info,
            period=period,
            usd_tax_table=usd_tax_table,
            zig_tax_table=zig_tax_table,
            exchange_rate=exchange_rate,
            payroll_id=payroll_id
        )

    def _calculate_summary(self, payslips: List[Payslip]) -> PayrollSummary:
        """Calculate summary from payslips."""
        summary = PayrollSummary(total_employees=len(payslips))

        for ps in payslips:
            summary.total_gross_usd += ps.gross_usd
            summary.total_gross_zig += ps.gross_zig
            summary.total_net_usd += ps.net_salary_usd
            summary.total_net_zig += ps.net_salary_zig
            summary.total_paye_usd += ps.paye_usd
            summary.total_paye_zig += ps.paye_zig
            summary.total_nssa_employee_usd += ps.nssa_employee_usd
            summary.total_nssa_employee_zig += ps.nssa_employee_zig
            summary.total_nssa_employer_usd += ps.nssa_employer_usd
            summary.total_nssa_employer_zig += ps.nssa_employer_zig
            summary.total_aids_levy_usd += ps.aids_levy_usd
            summary.total_aids_levy_zig += ps.aids_levy_zig
            summary.total_deductions_usd += ps.total_deductions_usd
            summary.total_deductions_zig += ps.total_deductions_zig
            summary.total_allowances_usd += ps.total_allowances_usd
            summary.total_allowances_zig += ps.total_allowances_zig

        return summary

    def close_payroll(self, payroll_id: int, user_id: int) -> Payroll:
        """Close a payroll period."""
        payroll = self.payroll_repo.get_by_id(payroll_id)
        if not payroll:
            raise NotFoundError(f"Payroll {payroll_id} not found")

        payroll.close(user_id)
        return self.payroll_repo.save(payroll)

    def reopen_payroll(self, payroll_id: int) -> Payroll:
        """Reopen a closed payroll."""
        payroll = self.payroll_repo.get_by_id(payroll_id)
        if not payroll:
            raise NotFoundError(f"Payroll {payroll_id} not found")

        payroll.reopen()
        return self.payroll_repo.save(payroll)

    def get_payroll(self, payroll_id: int) -> Optional[Payroll]:
        """Get payroll by ID."""
        return self.payroll_repo.get_by_id(payroll_id)

    def get_payroll_by_period(self, period: PayrollPeriod) -> Optional[Payroll]:
        """Get payroll for a specific period."""
        return self.payroll_repo.get_by_period(period)

    def get_payslips_for_period(self, period: PayrollPeriod) -> List[Payslip]:
        """Get all payslips for a period."""
        return self.payslip_repo.get_by_period(period)

    def get_payslip(self, payslip_id: int) -> Optional[Payslip]:
        """Get payslip by ID."""
        return self.payslip_repo.get_by_id(payslip_id)

    def approve_payslip(self, payslip_id: int) -> Payslip:
        """Approve a payslip."""
        payslip = self.payslip_repo.get_by_id(payslip_id)
        if not payslip:
            raise NotFoundError(f"Payslip {payslip_id} not found")

        payslip.approve()
        return self.payslip_repo.save(payslip)

    def mark_payslip_paid(self, payslip_id: int) -> Payslip:
        """Mark a payslip as paid."""
        payslip = self.payslip_repo.get_by_id(payslip_id)
        if not payslip:
            raise NotFoundError(f"Payslip {payslip_id} not found")

        payslip.mark_paid()
        return self.payslip_repo.save(payslip)
