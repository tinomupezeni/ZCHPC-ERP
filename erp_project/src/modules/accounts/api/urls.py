"""
URL patterns for the accounts module API.
"""

from django.urls import path

from modules.accounts.api import views

app_name = "accounts_v2"

urlpatterns = [
    # Accounts
    path("accounts/", views.account_list, name="account-list"),
    path("accounts/<int:account_id>/", views.account_detail, name="account-detail"),
    path("accounts/<int:account_id>/activate/", views.account_activate, name="account-activate"),
    path("accounts/chart/", views.chart_of_accounts, name="chart-of-accounts"),

    # Currencies
    path("currencies/", views.currency_list, name="currency-list"),
    path("currencies/<int:currency_id>/", views.currency_detail, name="currency-detail"),

    # Journals
    path("journals/", views.journal_list, name="journal-list"),
    path("journals/<int:journal_id>/", views.journal_detail, name="journal-detail"),

    # Journal Entries
    path("entries/", views.journal_entry_list, name="entry-list"),
    path("entries/<int:entry_id>/", views.journal_entry_detail, name="entry-detail"),
    path("entries/<int:entry_id>/post/", views.journal_entry_post, name="entry-post"),
    path("entries/<int:entry_id>/unpost/", views.journal_entry_unpost, name="entry-unpost"),
    path("entries/<int:entry_id>/reverse/", views.journal_entry_reverse, name="entry-reverse"),
    path("entries/<int:entry_id>/lines/", views.journal_entry_add_line, name="entry-add-line"),
    path(
        "entries/<int:entry_id>/lines/<int:line_id>/",
        views.journal_entry_remove_line,
        name="entry-remove-line"
    ),

    # Partners
    path("partners/", views.partner_list, name="partner-list"),
    path("partners/<int:partner_id>/", views.partner_detail, name="partner-detail"),

    # Reports
    path("reports/trial-balance/", views.trial_balance, name="trial-balance"),
    path("reports/profit-loss/", views.profit_loss, name="profit-loss"),
    path("reports/balance-sheet/", views.balance_sheet, name="balance-sheet"),
    path("reports/general-ledger/", views.general_ledger, name="general-ledger"),
    path("reports/account-balances/", views.account_balances, name="account-balances"),
]
