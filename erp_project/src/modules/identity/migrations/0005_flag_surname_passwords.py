"""
Flag logins still holding the surname password (REM-07).

Until REM-07, every login provisioned for a new employee received the
employee's surname as its password. Those accounts are found by checking
the surname against the stored hash with Django's own check_password - no
hash is read into plaintext, rewritten or replaced - and marked
must_change_password, so RBACMiddleware confines them to the password change.

Only accounts whose password verifiably equals the linked employee's surname
are flagged; every other account, and every password hash, is untouched.
Running it again changes nothing (flagged accounts are skipped). The reverse
is a no-op: the flag cannot be told apart from one set later for another
reason.

Note: check_password runs the full password hasher once per linked employee
login, so this migration's duration grows with the number of employees.
"""

from django.contrib.auth.hashers import check_password
from django.db import migrations


def flag_surname_passwords(apps, schema_editor):
    Employees = apps.get_model("hr", "Employees")
    CustomUser = apps.get_model("identity", "CustomUser")

    candidates = (
        Employees.objects.filter(user__isnull=False, user__must_change_password=False)
        .exclude(surname="")
        .select_related("user")
    )
    flagged = [
        employee.user_id
        for employee in candidates
        if employee.user.password and check_password(employee.surname, employee.user.password)
    ]
    if flagged:
        CustomUser.objects.filter(pk__in=flagged).update(must_change_password=True)


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0004_customuser_must_change_password"),
        ("hr", "0020_seed_employee_lifecycle_permissions"),
    ]

    operations = [
        migrations.RunPython(flag_surname_passwords, migrations.RunPython.noop),
    ]
