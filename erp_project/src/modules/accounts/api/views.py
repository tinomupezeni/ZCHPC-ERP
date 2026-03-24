"""
API views for the accounts module.
"""

from datetime import date
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.accounts.application.services import (
    AccountService,
    CreateAccountDTO,
    UpdateAccountDTO,
    JournalEntryService,
    CreateJournalEntryDTO,
    UpdateJournalEntryDTO,
    JournalEntryLineDTO,
    ReportingService,
)
from modules.accounts.infrastructure.persistence.django_account_repository import DjangoAccountRepository
from modules.accounts.infrastructure.persistence.django_currency_repository import DjangoCurrencyRepository
from modules.accounts.infrastructure.persistence.django_journal_repository import DjangoJournalRepository
from modules.accounts.infrastructure.persistence.django_journal_entry_repository import DjangoJournalEntryRepository
from modules.accounts.infrastructure.persistence.django_partner_repository import DjangoPartnerRepository
from modules.accounts.api.serializers import (
    AccountSerializer,
    CreateAccountSerializer,
    UpdateAccountSerializer,
    ChartOfAccountsSerializer,
    CurrencySerializer,
    CreateCurrencySerializer,
    UpdateCurrencyRateSerializer,
    JournalSerializer,
    CreateJournalSerializer,
    JournalEntrySerializer,
    CreateJournalEntrySerializer,
    UpdateJournalEntrySerializer,
    AddEntryLineSerializer,
    CreateReversingEntrySerializer,
    PartnerSerializer,
    CreatePartnerSerializer,
    AccountBalanceSerializer,
    TrialBalanceSerializer,
    ProfitLossSerializer,
    BalanceSheetSerializer,
    GeneralLedgerSerializer,
)


# Initialize repositories
_account_repo = DjangoAccountRepository()
_currency_repo = DjangoCurrencyRepository()
_journal_repo = DjangoJournalRepository()
_entry_repo = DjangoJournalEntryRepository()
_partner_repo = DjangoPartnerRepository()

# Initialize services
_account_service = AccountService(_account_repo, _entry_repo)
_entry_service = JournalEntryService(_entry_repo, _journal_repo, _account_repo)
_reporting_service = ReportingService(_account_repo, _entry_repo)


def _handle_error(e: Exception) -> Response:
    """Handle domain exceptions."""
    if isinstance(e, ValidationError):
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    elif isinstance(e, NotFoundError):
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================
# Account Views
# ============================

@api_view(["GET", "POST"])
def account_list(request: Request) -> Response:
    """List accounts or create a new account."""
    if request.method == "GET":
        account_type = request.query_params.get("type")
        include_inactive = request.query_params.get("include_inactive", "false").lower() == "true"

        try:
            accounts = _account_service.list_accounts(
                account_type=account_type,
                include_inactive=include_inactive
            )
            serializer = AccountSerializer(accounts, many=True)
            return Response(serializer.data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "POST":
        serializer = CreateAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            dto = CreateAccountDTO(**serializer.validated_data)
            account = _account_service.create_account(dto)
            return Response(
                AccountSerializer(account).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return _handle_error(e)


@api_view(["GET", "PUT", "DELETE"])
def account_detail(request: Request, account_id: int) -> Response:
    """Get, update, or delete an account."""
    if request.method == "GET":
        try:
            account = _account_service.get_account(account_id)
            return Response(AccountSerializer(account).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "PUT":
        serializer = UpdateAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            dto = UpdateAccountDTO(**serializer.validated_data)
            account = _account_service.update_account(account_id, dto)
            return Response(AccountSerializer(account).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "DELETE":
        try:
            _account_service.deactivate_account(account_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return _handle_error(e)


@api_view(["GET"])
def chart_of_accounts(request: Request) -> Response:
    """Get hierarchical chart of accounts."""
    try:
        chart = _account_service.get_chart_of_accounts()
        return Response(chart)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def account_activate(request: Request, account_id: int) -> Response:
    """Activate a deactivated account."""
    try:
        account = _account_service.activate_account(account_id)
        return Response(AccountSerializer(account).data)
    except Exception as e:
        return _handle_error(e)


# ============================
# Currency Views
# ============================

@api_view(["GET", "POST"])
def currency_list(request: Request) -> Response:
    """List currencies or create a new currency."""
    if request.method == "GET":
        currencies = _currency_repo.get_all()
        serializer = CurrencySerializer(currencies, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = CreateCurrencySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from modules.accounts.domain.entities import Currency
        currency = Currency.create(**serializer.validated_data)
        saved = _currency_repo.save(currency)
        return Response(
            CurrencySerializer(saved).data,
            status=status.HTTP_201_CREATED
        )


@api_view(["GET", "PUT"])
def currency_detail(request: Request, currency_id: int) -> Response:
    """Get or update a currency."""
    currency = _currency_repo.get_by_id(currency_id)
    if currency is None:
        return Response(
            {"error": "Currency not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        return Response(CurrencySerializer(currency).data)

    elif request.method == "PUT":
        serializer = UpdateCurrencyRateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            currency.update_rate(serializer.validated_data["rate_to_base"])
            saved = _currency_repo.save(currency)
            return Response(CurrencySerializer(saved).data)
        except Exception as e:
            return _handle_error(e)


# ============================
# Journal Views
# ============================

@api_view(["GET", "POST"])
def journal_list(request: Request) -> Response:
    """List journals or create a new journal."""
    if request.method == "GET":
        journal_type = request.query_params.get("type")
        if journal_type:
            from modules.accounts.domain.value_objects import JournalType
            try:
                jtype = JournalType(journal_type)
                journals = _journal_repo.get_by_type(jtype)
            except ValueError:
                return Response(
                    {"error": f"Invalid journal type: {journal_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            journals = _journal_repo.get_all()
        return Response(JournalSerializer(journals, many=True).data)

    elif request.method == "POST":
        serializer = CreateJournalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from modules.accounts.domain.entities import Journal
        from modules.accounts.domain.value_objects import JournalType

        data = serializer.validated_data
        journal = Journal.create(
            code=data["code"],
            name=data["name"],
            journal_type=JournalType(data["journal_type"]),
            default_debit_account_id=data.get("default_debit_account_id"),
            default_credit_account_id=data.get("default_credit_account_id"),
            currency_id=data.get("currency_id")
        )
        saved = _journal_repo.save(journal)
        return Response(
            JournalSerializer(saved).data,
            status=status.HTTP_201_CREATED
        )


@api_view(["GET"])
def journal_detail(request: Request, journal_id: int) -> Response:
    """Get a journal."""
    journal = _journal_repo.get_by_id(journal_id)
    if journal is None:
        return Response(
            {"error": "Journal not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    return Response(JournalSerializer(journal).data)


# ============================
# Journal Entry Views
# ============================

@api_view(["GET", "POST"])
def journal_entry_list(request: Request) -> Response:
    """List journal entries or create a new entry."""
    if request.method == "GET":
        journal_id = request.query_params.get("journal_id")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        posted_only = request.query_params.get("posted_only", "false").lower() == "true"

        try:
            if journal_id:
                entries = _entry_service.list_entries(
                    journal_id=int(journal_id),
                    posted_only=posted_only
                )
            elif from_date and to_date:
                entries = _entry_service.list_entries(
                    from_date=date.fromisoformat(from_date),
                    to_date=date.fromisoformat(to_date),
                    posted_only=posted_only
                )
            else:
                return Response(
                    {"error": "Either journal_id or date range is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(JournalEntrySerializer(entries, many=True).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "POST":
        serializer = CreateJournalEntrySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            lines = [
                JournalEntryLineDTO(**line)
                for line in data.get("lines", [])
            ]
            dto = CreateJournalEntryDTO(
                journal_id=data["journal_id"],
                entry_date=data["entry_date"],
                lines=lines,
                reference=data.get("reference"),
                narration=data.get("narration"),
                auto_post=data.get("auto_post", False)
            )
            entry = _entry_service.create_entry(dto)
            return Response(
                JournalEntrySerializer(entry).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return _handle_error(e)


@api_view(["GET", "PUT", "DELETE"])
def journal_entry_detail(request: Request, entry_id: int) -> Response:
    """Get, update, or delete a journal entry."""
    if request.method == "GET":
        try:
            entry = _entry_service.get_entry(entry_id)
            return Response(JournalEntrySerializer(entry).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "PUT":
        serializer = UpdateJournalEntrySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            dto = UpdateJournalEntryDTO(**serializer.validated_data)
            entry = _entry_service.update_entry(entry_id, dto)
            return Response(JournalEntrySerializer(entry).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "DELETE":
        try:
            _entry_service.delete_entry(entry_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return _handle_error(e)


@api_view(["POST"])
def journal_entry_post(request: Request, entry_id: int) -> Response:
    """Post a journal entry."""
    try:
        entry = _entry_service.post_entry(entry_id)
        return Response(JournalEntrySerializer(entry).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def journal_entry_unpost(request: Request, entry_id: int) -> Response:
    """Unpost a journal entry."""
    try:
        entry = _entry_service.unpost_entry(entry_id)
        return Response(JournalEntrySerializer(entry).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def journal_entry_reverse(request: Request, entry_id: int) -> Response:
    """Create a reversing entry for a posted entry."""
    serializer = CreateReversingEntrySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        entry = _entry_service.create_reversing_entry(
            entry_id=entry_id,
            reversal_date=serializer.validated_data["reversal_date"],
            reference=serializer.validated_data.get("reference")
        )
        return Response(
            JournalEntrySerializer(entry).data,
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def journal_entry_add_line(request: Request, entry_id: int) -> Response:
    """Add a line to an unposted entry."""
    serializer = AddEntryLineSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        line_dto = JournalEntryLineDTO(**serializer.validated_data)
        entry = _entry_service.add_line_to_entry(entry_id, line_dto)
        return Response(JournalEntrySerializer(entry).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["DELETE"])
def journal_entry_remove_line(request: Request, entry_id: int, line_id: int) -> Response:
    """Remove a line from an unposted entry."""
    try:
        entry = _entry_service.remove_line_from_entry(entry_id, line_id)
        return Response(JournalEntrySerializer(entry).data)
    except Exception as e:
        return _handle_error(e)


# ============================
# Partner Views
# ============================

@api_view(["GET", "POST"])
def partner_list(request: Request) -> Response:
    """List partners or create a new partner."""
    if request.method == "GET":
        partner_type = request.query_params.get("type")
        search = request.query_params.get("search")

        if search:
            partners = _partner_repo.search(search)
        elif partner_type:
            from modules.accounts.domain.value_objects import PartnerType
            try:
                ptype = PartnerType(partner_type)
                partners = _partner_repo.get_by_type(ptype)
            except ValueError:
                return Response(
                    {"error": f"Invalid partner type: {partner_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            partners = _partner_repo.get_all()

        return Response(PartnerSerializer(partners, many=True).data)

    elif request.method == "POST":
        serializer = CreatePartnerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from modules.accounts.domain.entities import Partner
        from modules.accounts.domain.value_objects import PartnerType

        data = serializer.validated_data
        partner = Partner.create(
            name=data["name"],
            partner_type=PartnerType(data["partner_type"]),
            vat_number=data.get("vat_number"),
            currency_id=data.get("currency_id"),
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address")
        )
        saved = _partner_repo.save(partner)
        return Response(
            PartnerSerializer(saved).data,
            status=status.HTTP_201_CREATED
        )


@api_view(["GET"])
def partner_detail(request: Request, partner_id: int) -> Response:
    """Get a partner."""
    partner = _partner_repo.get_by_id(partner_id)
    if partner is None:
        return Response(
            {"error": "Partner not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    return Response(PartnerSerializer(partner).data)


# ============================
# Report Views
# ============================

@api_view(["GET"])
def trial_balance(request: Request) -> Response:
    """Get trial balance report."""
    as_of_date = request.query_params.get("as_of_date")
    from_date = request.query_params.get("from_date")

    if not as_of_date:
        return Response(
            {"error": "as_of_date is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        report = _reporting_service.get_trial_balance(
            as_of_date=date.fromisoformat(as_of_date),
            from_date=date.fromisoformat(from_date) if from_date else None
        )
        return Response(TrialBalanceSerializer(report).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["GET"])
def profit_loss(request: Request) -> Response:
    """Get Profit & Loss report."""
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if not from_date or not to_date:
        return Response(
            {"error": "from_date and to_date are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        report = _reporting_service.get_profit_loss(
            from_date=date.fromisoformat(from_date),
            to_date=date.fromisoformat(to_date)
        )
        return Response(ProfitLossSerializer(report).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["GET"])
def balance_sheet(request: Request) -> Response:
    """Get Balance Sheet report."""
    as_of_date = request.query_params.get("as_of_date")
    fiscal_year_start = request.query_params.get("fiscal_year_start")

    if not as_of_date:
        return Response(
            {"error": "as_of_date is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        report = _reporting_service.get_balance_sheet(
            as_of_date=date.fromisoformat(as_of_date),
            fiscal_year_start=date.fromisoformat(fiscal_year_start) if fiscal_year_start else None
        )
        return Response(BalanceSheetSerializer(report).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["GET"])
def general_ledger(request: Request) -> Response:
    """Get general ledger for an account."""
    account_id = request.query_params.get("account_id")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if not account_id or not from_date or not to_date:
        return Response(
            {"error": "account_id, from_date, and to_date are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        report = _reporting_service.get_general_ledger(
            account_id=int(account_id),
            from_date=date.fromisoformat(from_date),
            to_date=date.fromisoformat(to_date)
        )
        return Response(GeneralLedgerSerializer(report).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["GET"])
def account_balances(request: Request) -> Response:
    """Get balances for accounts."""
    account_type = request.query_params.get("type")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    try:
        balances = _reporting_service.get_account_balances(
            account_type=account_type,
            from_date=date.fromisoformat(from_date) if from_date else None,
            to_date=date.fromisoformat(to_date) if to_date else None
        )
        return Response(AccountBalanceSerializer(balances, many=True).data)
    except Exception as e:
        return _handle_error(e)
