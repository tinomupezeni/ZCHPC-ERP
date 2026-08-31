"""
Give safe defaults to hr_employees columns that exist in the live database
but were never tracked as Django model fields (has_disability, is_blind,
pension_rate, skills) - their origin isn't in this repo's migration history,
but they're NOT NULL with no default, so every INSERT that doesn't mention
them (which is all of them, since the model doesn't know about these
columns) fails with a NotNullViolation.

Guarded to no-op on backends/databases where these columns don't exist
(e.g. a fresh SQLite test database built from this repo's migrations alone).
"""
from django.db import migrations

COLUMN_DEFAULTS = {
    "has_disability": "false",
    "is_blind": "false",
    "pension_rate": "0",
    "skills": "'[]'::jsonb",
}


def add_defaults(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'hr_employees' AND column_name = ANY(%s)",
            [list(COLUMN_DEFAULTS.keys())],
        )
        existing_columns = {row[0] for row in cursor.fetchall()}

        for column, default in COLUMN_DEFAULTS.items():
            if column in existing_columns:
                cursor.execute(
                    f"ALTER TABLE hr_employees ALTER COLUMN {column} SET DEFAULT {default}"
                )


def remove_defaults(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'hr_employees' AND column_name = ANY(%s)",
            [list(COLUMN_DEFAULTS.keys())],
        )
        existing_columns = {row[0] for row in cursor.fetchall()}

        for column in COLUMN_DEFAULTS:
            if column in existing_columns:
                cursor.execute(f"ALTER TABLE hr_employees ALTER COLUMN {column} DROP DEFAULT")


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0013_remove_employees_bank_account_and_more"),
    ]

    operations = [
        migrations.RunPython(add_defaults, remove_defaults),
    ]
