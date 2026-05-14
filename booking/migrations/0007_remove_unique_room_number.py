from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0006_alter_room_room_number"),
    ]

    operations = [
        # The unique constraint was already removed in migration 0006.
        # Keep this migration empty to preserve the historical chain
        # without running backend-specific raw SQL that breaks on MySQL.
    ]
