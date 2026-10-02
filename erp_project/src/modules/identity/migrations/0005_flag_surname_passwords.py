"""
Flag logins still holding the surname password (REM-07) - now a no-op.

Until REM-07, every login provisioned for a new employee received the
employee's surname as its password. This migration used to find those
accounts with check_password and mark them must_change_password. Each check
runs the full password hasher, so the work grew with the number of employees
and ran inside the migration transaction, before the API could start.

That work now lives in the management command

    python manage.py flag_surname_passwords

(modules.identity.management.commands.flag_surname_passwords), which applies
the same rule in short, resumable batches outside the deployment window. Run
it once on every database after this migration is applied - see
docs/DEPLOYMENT.md, "Flagging Surname-Password Accounts".

The migration keeps its name, dependencies and place in the graph so
databases that already applied it, and databases that have not, agree on
migration history. Where it already ran, its flags stay set and the command
finds nothing more to do.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0004_customuser_must_change_password"),
        ("hr", "0020_seed_employee_lifecycle_permissions"),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop, migrations.RunPython.noop, elidable=True
        ),
    ]
