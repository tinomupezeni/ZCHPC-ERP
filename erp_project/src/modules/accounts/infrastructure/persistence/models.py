"""
Django models for the Accounts module.
"""
from django.db import models


class Currency(models.Model):
    """Currency definition."""
    name = models.CharField(max_length=32)
    code = models.CharField(max_length=8, unique=True)
    symbol = models.CharField(max_length=8, blank=True, null=True)
    rate_to_base = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Partner(models.Model):
    """Partners (Customer/Supplier/Employee)."""
    PARTNER_TYPES = [
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('employee', 'Employee'),
    ]

    name = models.CharField(max_length=255)
    partner_type = models.CharField(max_length=50, choices=PARTNER_TYPES)
    vat_number = models.CharField(max_length=64, blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_partner'

    def __str__(self):
        return self.name


class AccountChart(models.Model):
    """Chart of Accounts."""
    ACCOUNT_TYPES = [
        ('view', 'View'),
        ('regular', 'Regular'),
        ('consolidation', 'Consolidation'),
    ]

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    reconcile = models.BooleanField(default=False)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_accountchart'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Journal(models.Model):
    """Accounting Journals."""
    JOURNAL_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, unique=True)
    journal_type = models.CharField(max_length=50, choices=JOURNAL_TYPES)
    default_debit_account = models.ForeignKey(
        AccountChart,
        on_delete=models.SET_NULL,
        null=True,
        related_name='default_debit_journals'
    )
    default_credit_account = models.ForeignKey(
        AccountChart,
        on_delete=models.SET_NULL,
        null=True,
        related_name='default_credit_journals'
    )
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_journal'

    def __str__(self):
        return self.name


class AnalyticAccount(models.Model):
    """Analytic Accounts (Projects/Cost Centers)."""
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_analyticaccount'

    def __str__(self):
        return self.name


class AccountTag(models.Model):
    """Tags for multi-dimensional reporting."""
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_accounttag'

    def __str__(self):
        return self.name


class AccountMove(models.Model):
    """Journal Entry (Move)."""
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    date = models.DateField()
    ref = models.CharField(max_length=255, blank=True, null=True)
    narration = models.TextField(blank=True, null=True)
    posted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_accountmove'

    def __str__(self):
        return f"{self.journal.name} - {self.date}"


class AccountMoveLine(models.Model):
    """Journal Entry Lines (Move Line)."""
    move = models.ForeignKey(
        AccountMove,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(AccountChart, on_delete=models.CASCADE)
    partner = models.ForeignKey(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    amount_currency = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True
    )
    analytic_account = models.ForeignKey(
        AnalyticAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(AccountTag, blank=True, related_name='move_lines')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_accountmoveline'

    def __str__(self):
        return f"{self.account.name} - Debit:{self.debit} Credit:{self.credit}"
