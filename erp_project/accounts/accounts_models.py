from django.db import models
from django.contrib.postgres.fields import ArrayField


# -------------------------------
# Currency
# -------------------------------
class Currency(models.Model):
    name = models.CharField(max_length=32)
    code = models.CharField(max_length=8, unique=True)
    symbol = models.CharField(max_length=8, blank=True, null=True)
    rate_to_base = models.DecimalField(max_digits=18, decimal_places=6, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# -------------------------------
# Partners (Customer/Supplier/Employee)
# -------------------------------
class Partner(models.Model):
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

    def __str__(self):
        return self.name


# -------------------------------
# Chart of Accounts
# -------------------------------
class AccountChart(models.Model):
    ACCOUNT_TYPES = [
        ('view', 'View'),
        ('regular', 'Regular'),
        ('consolidation', 'Consolidation'),
    ]
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    reconcile = models.BooleanField(default=False)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# -------------------------------
# Journals
# -------------------------------
class Journal(models.Model):
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
    default_debit_account = models.ForeignKey(AccountChart, on_delete=models.SET_NULL, null=True, related_name='default_debit_journals')
    default_credit_account = models.ForeignKey(AccountChart, on_delete=models.SET_NULL, null=True, related_name='default_credit_journals')
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# -------------------------------
# Analytic Accounts (Projects/Cost Centers)
# -------------------------------
class AnalyticAccount(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# -------------------------------
# Tags for multi-dimensional reporting
# -------------------------------
class AccountTag(models.Model):
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, blank=True, null=True)  # hex color

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# -------------------------------
# Journal Entry (Move)
# -------------------------------
class AccountMove(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    date = models.DateField()
    ref = models.CharField(max_length=255, blank=True, null=True)
    narration = models.TextField(blank=True, null=True)
    posted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.journal.name} - {self.date}"


# -------------------------------
# Journal Entry Lines (Move Line)
# -------------------------------
class AccountMoveLine(models.Model):
    move = models.ForeignKey(AccountMove, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(AccountChart, on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)
    amount_currency = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    analytic_account = models.ForeignKey(AnalyticAccount, on_delete=models.SET_NULL, null=True, blank=True)
    tag_ids = ArrayField(models.IntegerField(), blank=True, default=list)  # store tag IDs for multi-dimensional analysis
    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account.name} - Debit:{self.debit} Credit:{self.credit}"
