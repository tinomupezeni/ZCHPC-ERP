"""
Add Employees.lifecycle_status and classify existing employees (AUD-02).

lifecycle_status (ACTIVE / DEACTIVATED / ARCHIVED) becomes the authoritative
statement of employment state; Employees.is_active stays as a mirror of it
(constraints added in 0022).

How existing rows are classified
--------------------------------
Only Employees.is_active is read - it is the employment flag; the login's
CustomUser.is_active is a separate concern and is left exactly as it is:

- is_active = True  -> ACTIVE
- is_active = False -> DEACTIVATED

No row becomes ARCHIVED. Until now "inactive" was the only non-active state
the system had, so an inactive row may be a suspension or a departure and
the data cannot tell which. DEACTIVATED carries exactly what is_active=False
already meant (not in normal employment, role kept, reversible) and adds no
claim; ARCHIVED would assert a permanent closure nobody decided. Archiving a
departed employee is a deliberate later action.

The column also carries a database default of ACTIVE, so inserts that do not
name it (older code during a deploy, historical migration states) keep
working.

Nothing is deleted or rewritten besides the new column. The reverse drops
the column; is_active is untouched in both directions.
"""

from django.db import migrations, models

# Snapshot of the lifecycle values at the time of this migration, copied
# rather than imported so later edits cannot change history.
ACTIVE = "ACTIVE"
DEACTIVATED = "DEACTIVATED"
ARCHIVED = "ARCHIVED"


def classify_existing_employees(apps, schema_editor):
    Employees = apps.get_model("hr", "Employees")
    Employees.objects.filter(is_active=True).update(lifecycle_status=ACTIVE)
    Employees.objects.filter(is_active=False).update(lifecycle_status=DEACTIVATED)


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0020_seed_employee_lifecycle_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="employees",
            name="lifecycle_status",
            field=models.CharField(
                choices=[
                    (ACTIVE, "Active"),
                    (DEACTIVATED, "Deactivated"),
                    (ARCHIVED, "Archived"),
                ],
                db_default=ACTIVE,
                default=ACTIVE,
                max_length=20,
            ),
        ),
        migrations.RunPython(classify_existing_employees, migrations.RunPython.noop),
    ]
