"""
Durable employee lifecycle audit (AUD-02).

Creates hr_employee_lifecycle_event, the append-only record of every
employee lifecycle transition (deactivate, reactivate, archive): which
employee (and their EC number), who, when, from and to which state, why,
through which API, and what accompanied it.

Schema only. Transitions made before this migration were never recorded and
cannot be reconstructed, so nothing is backfilled.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0023_employees_employee_id_immutable'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeLifecycleEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_number', models.CharField(max_length=20)),
                ('event_type', models.CharField(choices=[('DEACTIVATE', 'Deactivated'), ('REACTIVATE', 'Reactivated'), ('ARCHIVE', 'Archived')], max_length=20)),
                ('from_status', models.CharField(choices=[('ACTIVE', 'Active'), ('DEACTIVATED', 'Deactivated'), ('ARCHIVED', 'Archived')], max_length=20)),
                ('to_status', models.CharField(choices=[('ACTIVE', 'Active'), ('DEACTIVATED', 'Deactivated'), ('ARCHIVED', 'Archived')], max_length=20)),
                ('actor_email', models.CharField(blank=True, default='', max_length=254)),
                ('reason', models.TextField(blank=True, default='')),
                ('source', models.CharField(blank=True, default='', max_length=64)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('occurred_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employee_lifecycle_actions', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lifecycle_events', to='hr.employees')),
            ],
            options={
                'db_table': 'hr_employee_lifecycle_event',
                'ordering': ['occurred_at', 'id'],
                'indexes': [models.Index(fields=['employee', 'occurred_at'], name='hr_lifecycle_event_emp_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('event_type__in', ['DEACTIVATE', 'REACTIVATE', 'ARCHIVE'])), name='hr_lifecycle_event_type_valid'), models.CheckConstraint(condition=models.Q(('from_status', models.F('to_status')), _negated=True), name='hr_lifecycle_event_changes_state')],
            },
        ),
    ]
