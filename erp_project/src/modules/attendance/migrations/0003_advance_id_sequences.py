"""
Advance the attendance tables' ID sequences past existing rows (REM-06).

Until REM-06 the attendance repository computed IDs as max(id) + 1 (inserting
through the sequence, but a database may also hold rows written with
explicit IDs by other tooling). On PostgreSQL an explicit-ID insert does not
advance the column's sequence, so existing databases can have sequences
behind max(id). Now that IDs are database-assigned, the next insert would
draw an ID that is already taken and fail. This moves each sequence forward
to max(id) - never backwards - and does nothing on other databases or on
sequences already ahead. Same approach as recruitment 0003 (REM-04).
"""

from django.db import migrations

TABLES = (
    "human_resources_attendancerecord",
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
        ("attendance", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(advance_sequences, migrations.RunPython.noop),
    ]
