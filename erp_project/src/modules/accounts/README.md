# Accounts Module

Financial accounting and reporting.

## Domain

### Aggregates

**Account** (root):
- id, code, name
- parent_id (hierarchical)
- account_type (Asset, Liability, Equity, Revenue, Expense)
- currency_id
- is_reconcilable

**Journal** (root):
- id, code, name
- journal_type (Sales, Purchase, Cash, Bank, General)
- default_debit_account_id
- default_credit_account_id

**JournalEntry** (root):
- id, journal_id
- date, reference, narration
- is_posted
- lines (list of JournalEntryLine)

**JournalEntryLine**:
- id, entry_id, account_id
- partner_id (optional)
- debit, credit
- currency_id, amount_currency

**Partner** (root):
- id, name
- partner_type (Customer, Supplier, Employee)
- vat_number

**Currency** (root):
- id, code, name, symbol
- rate_to_base

### Value Objects

- `AccountCode`: Validated account code
- `AccountType`: Asset, Liability, Equity, Revenue, Expense
- `JournalType`: Sales, Purchase, Cash, Bank, General
- `DebitCredit`: Debit or credit indicator

### Domain Services

- `BalanceCalculator`: Account balances
- `TrialBalanceGenerator`: Trial balance report
- `ProfitLossGenerator`: P&L statement
- `BalanceSheetGenerator`: Balance sheet

### Events

- `JournalEntryPosted`
- `AccountCreated`

### Event Handlers

Listens to:
- `PayrollProcessed` -> Create salary expense journal entries

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts/chart/` | Chart of accounts |
| GET | `/api/accounts/journals/` | List journals |
| GET | `/api/accounts/entries/` | Journal entries |
| POST | `/api/accounts/entries/` | Create entry |
| POST | `/api/accounts/entries/{id}/post/` | Post entry |
| GET | `/api/accounts/reports/trial-balance/` | Trial balance |
| GET | `/api/accounts/reports/profit-loss/` | P&L |
| GET | `/api/accounts/reports/balance-sheet/` | Balance sheet |

## Dependencies

- Identity Module (ICurrentUserProvider)
- Receives events from Payroll Module
