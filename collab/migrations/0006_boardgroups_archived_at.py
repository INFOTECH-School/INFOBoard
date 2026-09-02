from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collab', '0005_excalidrawroom_archived_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='boardgroups',
            name='archived_at',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='data archiwizacji'),
        ),
    ]
