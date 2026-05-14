"""Schema guard for Room.room_number.

This migration originally attempted to add `room_number` unconditionally, but
the column already exists since the initial Room model migration.
On MySQL (and most DBs) that causes `Duplicate column name`.

We keep this migration in the graph (other migrations depend on it) but make
the operation idempotent: add the column only if it is missing.
"""

from django.db import migrations


def ensure_room_number_column(apps, schema_editor):
    table_name = "rooms"  # Room model uses Meta.db_table = 'rooms'
    column_name = "room_number"

    with schema_editor.connection.cursor() as cursor:
        existing_tables = set(schema_editor.connection.introspection.table_names(cursor))
        if table_name not in existing_tables:
            return

        columns = schema_editor.connection.introspection.get_table_description(cursor, table_name)
        existing_column_names = {c.name for c in columns}
        if column_name in existing_column_names:
            return

        qn = schema_editor.quote_name
        vendor = schema_editor.connection.vendor

        if vendor in {"mysql", "sqlite", "postgresql"}:
            schema_editor.execute(
                f"ALTER TABLE {qn(table_name)} ADD COLUMN {qn(column_name)} varchar(50) NOT NULL DEFAULT 'TBD'"
            )
        else:
            # Best-effort fallback
            schema_editor.execute(
                f"ALTER TABLE {qn(table_name)} ADD COLUMN {qn(column_name)} varchar(50)"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0012_rename_announcement_active_show_until_idx_announcemen_is_acti_13e55a_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(ensure_room_number_column, reverse_code=migrations.RunPython.noop),
    ]
