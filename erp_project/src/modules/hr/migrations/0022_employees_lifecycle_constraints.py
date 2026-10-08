"""
Constrain Employees.lifecycle_status (AUD-02).

Separate from 0021 because PostgreSQL will not alter a table in the same
transaction that updated its rows.

- hr_employees_lifecycle_status_valid: only ACTIVE / DEACTIVATED / ARCHIVED
  can be stored.
- hr_employees_is_active_matches_lifecycle: is_active is true exactly when
  lifecycle_status is ACTIVE, so the compatibility flag cannot drift from
  the authoritative state.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0021_employees_lifecycle_status"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="employees",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("lifecycle_status__in", ["ACTIVE", "DEACTIVATED", "ARCHIVED"])
                ),
                name="hr_employees_lifecycle_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="employees",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("is_active", True), ("lifecycle_status", "ACTIVE")),
                    models.Q(
                        models.Q(("lifecycle_status", "ACTIVE"), _negated=True),
                        ("is_active", False),
                    ),
                    _connector="OR",
                ),
                name="hr_employees_is_active_matches_lifecycle",
            ),
        ),
    ]
