"""
Tax calculation services for PAYE and AIDS Levy.
"""

from decimal import Decimal
from typing import List, Tuple

from modules.payroll.domain.value_objects import TaxBracket, Currency
from modules.payroll.domain.entities import TaxTable


class TaxCalculator:
    """
    Service for calculating PAYE (Pay As You Earn) tax.

    Uses Zimbabwe's progressive tax bracket system.
    Formula: PAYE = (income * rate) - deduction
    """

    @staticmethod
    def calculate_paye(income: Decimal, tax_table: TaxTable) -> Decimal:
        """
        Calculate PAYE tax using the tax table.

        Args:
            income: Gross taxable income
            tax_table: Tax table with brackets

        Returns:
            PAYE tax amount (never negative)
        """
        if income <= 0:
            return Decimal("0")

        return tax_table.calculate_tax(income)

    @staticmethod
    def calculate_paye_from_brackets(
        income: Decimal,
        brackets: List[Tuple[Decimal, Decimal, Decimal, Decimal]]
    ) -> Decimal:
        """
        Calculate PAYE from raw bracket tuples.

        Args:
            income: Gross taxable income
            brackets: List of (min_income, max_income, rate, deduction) tuples

        Returns:
            PAYE tax amount
        """
        if income <= 0 or not brackets:
            return Decimal("0")

        # Sort by min_income descending to find correct bracket
        sorted_brackets = sorted(brackets, key=lambda x: x[0], reverse=True)

        paye = Decimal("0")
        for min_inc, max_inc, rate, deduct in sorted_brackets:
            if income > min_inc:
                paye = (income * rate) - deduct
                break

        return max(Decimal("0"), paye).quantize(Decimal("0.01"))


class AIDSLevyCalculator:
    """
    Service for calculating AIDS Levy.

    AIDS Levy is 3% of PAYE in Zimbabwe.
    """

    AIDS_LEVY_RATE = Decimal("0.03")  # 3% of PAYE

    @classmethod
    def calculate(cls, paye: Decimal, pays_levy: bool = True) -> Decimal:
        """
        Calculate AIDS Levy.

        Args:
            paye: PAYE tax amount
            pays_levy: Whether employee is subject to AIDS levy

        Returns:
            AIDS Levy amount
        """
        if not pays_levy or paye <= 0:
            return Decimal("0")

        return (paye * cls.AIDS_LEVY_RATE).quantize(Decimal("0.01"))


class NSSACalculator:
    """
    Service for calculating NSSA (National Social Security Authority) contributions.

    NSSA rates:
    - Employee: 4.5% of gross salary
    - Employer: 4.5% of gross salary
    """

    EMPLOYEE_RATE = Decimal("0.045")  # 4.5%
    EMPLOYER_RATE = Decimal("0.045")  # 4.5%

    # NSSA has a ceiling for insurable earnings (needs to be updated periodically)
    # Currently not enforced but placeholder for future implementation
    CEILING_USD: Decimal = None  # No ceiling currently
    CEILING_ZIG: Decimal = None

    @classmethod
    def calculate(
        cls,
        gross_salary: Decimal,
        currency: Currency = Currency.USD
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate NSSA contributions.

        Args:
            gross_salary: Gross salary amount
            currency: Currency of the salary

        Returns:
            Tuple of (employee_contribution, employer_contribution)
        """
        if gross_salary <= 0:
            return Decimal("0"), Decimal("0")

        # Apply ceiling if set
        ceiling = cls.CEILING_USD if currency == Currency.USD else cls.CEILING_ZIG
        base = min(gross_salary, ceiling) if ceiling else gross_salary

        employee = (base * cls.EMPLOYEE_RATE).quantize(Decimal("0.01"))
        employer = (base * cls.EMPLOYER_RATE).quantize(Decimal("0.01"))

        return employee, employer

    @classmethod
    def calculate_employee(cls, gross_salary: Decimal) -> Decimal:
        """Calculate employee NSSA contribution only."""
        if gross_salary <= 0:
            return Decimal("0")
        return (gross_salary * cls.EMPLOYEE_RATE).quantize(Decimal("0.01"))

    @classmethod
    def calculate_employer(cls, gross_salary: Decimal) -> Decimal:
        """Calculate employer NSSA contribution only."""
        if gross_salary <= 0:
            return Decimal("0")
        return (gross_salary * cls.EMPLOYER_RATE).quantize(Decimal("0.01"))


class StatutoryCalculator:
    """
    Combines all statutory deduction calculations.
    """

    def __init__(
        self,
        tax_calculator: TaxCalculator = None,
        aids_calculator: AIDSLevyCalculator = None,
        nssa_calculator: NSSACalculator = None
    ):
        self.tax_calculator = tax_calculator or TaxCalculator()
        self.aids_calculator = aids_calculator or AIDSLevyCalculator()
        self.nssa_calculator = nssa_calculator or NSSACalculator()

    def calculate_all(
        self,
        gross_salary: Decimal,
        tax_table: TaxTable,
        pays_aids_levy: bool = True,
        currency: Currency = Currency.USD
    ) -> dict:
        """
        Calculate all statutory deductions.

        Args:
            gross_salary: Gross salary amount
            tax_table: Tax table for PAYE calculation
            pays_aids_levy: Whether employee pays AIDS levy
            currency: Currency of the salary

        Returns:
            Dictionary with all statutory deduction amounts
        """
        paye = self.tax_calculator.calculate_paye(gross_salary, tax_table)
        aids_levy = self.aids_calculator.calculate(paye, pays_aids_levy)
        nssa_employee, nssa_employer = self.nssa_calculator.calculate(
            gross_salary, currency
        )

        return {
            "paye": paye,
            "aids_levy": aids_levy,
            "nssa_employee": nssa_employee,
            "nssa_employer": nssa_employer,
            "total_statutory": paye + aids_levy + nssa_employee,
        }
