"""
Make an employee's EC number immutable at the database (AUD-02).

An EC number (Employees.employee_id) belongs to one employee for all time.
The UNIQUE constraint stops two rows holding a number at once, and the
application no longer deletes employee rows, so a held number stays held.
The remaining way to free a number for someone else was to change it on its
row; this trigger refuses any UPDATE that changes a non-blank employee_id.

A blank number was never issued, so numbering such a row is still allowed.
An UPDATE that writes the same value passes, so ordinary saves are unaffected.

Applied to PostgreSQL (production) and SQLite (development and tests). Note
that on SQLite a later migration that rebuilds hr_employees drops triggers,
so such a migration must recreate this one.
"""

from django.db import migrations

POSTGRESQL_FORWARD = """
CREATE FUNCTION hr_employees_employee_id_immutable() RETURNS trigger AS $$
BEGIN
    IF OLD.employee_id <> '' AND NEW.employee_id IS DISTINCT FROM OLD.employee_id THEN
        RAISE EXCEPTION 'An employee''s EC number cannot be changed (was %, requested %)',
            OLD.employee_id, NEW.employee_id
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hr_employees_employee_id_immutable
    BEFORE UPDATE OF employee_id ON hr_employees
    FOR EACH ROW EXECUTE FUNCTION hr_employees_employee_id_immutable();
"""

POSTGRESQL_REVERSE = """
DROP TRIGGER IF EXISTS hr_employees_employee_id_immutable ON hr_employees;
DROP FUNCTION IF EXISTS hr_employees_employee_id_immutable();
"""

SQLITE_FORWARD = """
CREATE TRIGGER hr_employees_employee_id_immutable
    BEFORE UPDATE OF employee_id ON hr_employees
    FOR EACH ROW
    WHEN OLD.employee_id <> '' AND NEW.employee_id IS NOT OLD.employee_id
BEGIN
    SELECT RAISE(ABORT, 'An employee''s EC number cannot be changed');
END;
"""

SQLITE_REVERSE = "DROP TRIGGER IF EXISTS hr_employees_employee_id_immutable;"


def _run(schema_editor, statements):
    sql = statements.get(schema_editor.connection.vendor)
    if sql is None:
        raise RuntimeError(
            f"No EC number immutability trigger for {schema_editor.connection.vendor}"
        )
    if schema_editor.connection.vendor == "sqlite":
        # The SQLite trigger body contains ';', so it is one statement.
        schema_editor.execute(sql)
    else:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql)


def create_trigger(apps, schema_editor):
    _run(schema_editor, {"postgresql": POSTGRESQL_FORWARD, "sqlite": SQLITE_FORWARD})


def drop_trigger(apps, schema_editor):
    _run(schema_editor, {"postgresql": POSTGRESQL_REVERSE, "sqlite": SQLITE_REVERSE})


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0022_employees_lifecycle_constraints"),
    ]

    operations = [
        migrations.RunPython(create_trigger, drop_trigger),
    ]
