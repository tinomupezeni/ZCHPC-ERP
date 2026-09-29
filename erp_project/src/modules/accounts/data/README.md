# Accounts reference data

## zchpc_chart_of_accounts.csv

The official Zimbabwe Centre for High Performance Computing Chart of Accounts,
exported from Sage 200 Evolution on 20/07/2026 15:45:02. 103 accounts.

Load it with:

```
python manage.py import_chart_of_accounts            # add --dry-run to preview
```

### Format

UTF-8 CSV (no BOM), standard CSV quoting, header row required:

| Column | Meaning |
|---|---|
| `code` | Account code, exactly as in Sage (e.g. `20000/01/101/022/300`) |
| `name` | Account name, exactly as in Sage |
| `external_account_type` | Sage account type, exactly as exported (e.g. `Other Expense`) |
| `parent_code` | Code of the parent account, or blank |

Sage exports each account as `code (name)`; that column is split into `code`
and `name` at the first ` (` with the final `)` removed, so names containing
brackets (`RAM (Gb)`) are kept whole. No value is corrected, including spelling
(`Dilligenc`, `Equipoment`) and Sage's truncation of
`Property, Plant and Equipm`.

`parent_code` is filled only where the chart itself states the relationship:
the parent account appears in the chart and the child's code extends it. That
applies to the four `10000/04/056/000n` accounts under `10000/04/056` Hosting
Services. Other slash-separated codes have no parent account in the chart, so
none is invented.

### Open accounting questions (for Finance)

- `account_type` is not part of the Sage export. Imported accounts get
  `regular`, the existing application default for accounts that are neither
  view nor consolidation accounts. Whether `10000/04/056` Hosting Services is a
  heading (`view`) or a posting account has not been confirmed.
- The Sage account types are stored verbatim in `external_account_type` and are
  not mapped onto the accounts domain's Asset/Liability/Equity/Revenue/Expense.
