from django.db import migrations


def drop_room_number_unique_index(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return

    table_name = 'rooms'
    column_name = 'room_number'

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT INDEX_NAME
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
              AND NON_UNIQUE = 0
              AND INDEX_NAME <> 'PRIMARY'
            """,
            [table_name, column_name],
        )
        index_names = [row[0] for row in cursor.fetchall()]

        for index_name in index_names:
            schema_editor.execute(
                f"ALTER TABLE `{table_name}` DROP INDEX `{index_name}`"
            )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('booking', '0016_alter_booking_status_alter_room_availability_status'),
    ]

    operations = [
        migrations.RunPython(drop_room_number_unique_index, reverse_code=migrations.RunPython.noop),
    ]
