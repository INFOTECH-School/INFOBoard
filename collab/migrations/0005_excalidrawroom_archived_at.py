from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collab', '0004_alter_excalidrawroom_user_room_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='excalidrawroom',
            name='archived_at',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='data archiwizacji'),
        ),
    ]
