"""
Seed the core ERP modules as active by default.

Without this, every SystemModule row defaults to is_active=False (see 0002),
and the frontend sidebar hides any nav item with a moduleIdentifier until an
admin manually "installs" it from the App Store page - so even a superuser
sees only Dashboard/Settings/App Store on a fresh deployment. HR, Payroll,
Accounts, and Procurement are real, implemented modules and should be visible
out of the box; "sales" and "inventory" are frontend nav placeholders with no
backend module behind them yet, so they're intentionally left unseeded.

Uses get_or_create so this is a no-op for any module row an admin already
created/toggled via the App Store UI.
"""
from django.db import migrations


CORE_MODULES = [
    {
        "identifier": "hr",
        "name": "Human Resources",
        "description": "Employees, departments, positions, attendance, leave, recruitment.",
        "dependencies": [],
    },
    {
        "identifier": "payroll",
        "name": "Payroll",
        "description": "Salary processing, tax calculations, payslips.",
        "dependencies": ["hr"],
    },
    {
        "identifier": "accounts",
        "name": "Accounting",
        "description": "Chart of accounts, journal entries, financial reporting.",
        "dependencies": [],
    },
    {
        "identifier": "procurement",
        "name": "Procurement",
        "description": "Purchase requests, orders, supplier management.",
        "dependencies": [],
    },
]


def seed_core_modules(apps, schema_editor):
    SystemModule = apps.get_model("identity", "SystemModule")
    for module in CORE_MODULES:
        SystemModule.objects.get_or_create(
            identifier=module["identifier"],
            defaults={
                "name": module["name"],
                "description": module["description"],
                "dependencies": module["dependencies"],
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0002_systemmodule"),
    ]

    operations = [
        migrations.RunPython(seed_core_modules, migrations.RunPython.noop),
    ]
