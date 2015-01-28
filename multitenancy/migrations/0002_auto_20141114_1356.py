# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('multitenancy', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactlink',
            name='description',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contactlink',
            name='email',
            field=models.EmailField(max_length=75, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='contactlink',
            name='contact',
            field=models.OneToOneField(to='rapidsms.Contact'),
            preserve_default=True,
        ),
    ]
