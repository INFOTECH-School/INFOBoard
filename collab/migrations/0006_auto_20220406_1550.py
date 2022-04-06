# Generated by Django 3.2.12 on 2022-04-06 13:50

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('collab', '0005_excalidrawfile_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='excalidrawlogrecord',
            name='user_pseudonym',
            field=models.CharField(help_text='this is generated from draw.utils.user_id_for_room', max_length=64, null=True, validators=[django.core.validators.MinLengthValidator(64)]),
        ),
        migrations.CreateModel(
            name='Pseudonym',
            fields=[
                ('user_pseudonym', models.CharField(help_text='this is generated from draw.utils.user_id_for_room', max_length=64, primary_key=True, serialize=False, validators=[django.core.validators.MinLengthValidator(64)])),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='collab.excalidrawroom', verbose_name='room name')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'unique_together': {('room', 'user')},
            },
        ),
    ]
