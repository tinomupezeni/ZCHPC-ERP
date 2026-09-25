"""
Advance the recruitment tables' ID sequences past existing rows (REM-04).

Until REM-04 the repositories minted IDs as max(id) + 1 and inserted them
explicitly. On PostgreSQL an explicit-ID insert does not advance the column's
sequence, so existing databases can have sequences well behind max(id). Now
that IDs are database-assigned, the next insert would draw an ID that is
already taken and fail. This moves each sequence forward to max(id) - never
backwards - and does nothing on other databases or on sequences already ahead.
"""

from django.db import migrations

TABLES = (
    "human_resources_job",
    "human_resources_candidate",
    "human_resources_jobapplication",
)


def advance_sequences(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table])
            (sequence,) = cursor.fetchone()
            if sequence is None:
                continue
            cursor.execute(f'SELECT MAX(id) FROM "{table}"')
            (max_id,) = cursor.fetchone()
            cursor.execute(f"SELECT last_value, is_called FROM {sequence}")
            last_value, is_called = cursor.fetchone()
            next_value = last_value + 1 if is_called else last_value
            if max_id is not None and next_value <= max_id:
                cursor.execute("SELECT setval(%s, %s, true)", [sequence, max_id])


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0002_application_submission_snapshot"),
    ]

    operations = [
        migrations.RunPython(advance_sequences, migrations.RunPython.noop),
    ]
