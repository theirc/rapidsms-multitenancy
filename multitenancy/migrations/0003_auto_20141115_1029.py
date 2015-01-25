# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('multitenancy', '0002_auto_20141114_1356'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.PositiveSmallIntegerField(choices=[(1, 'Group Manager'), (2, 'Tenant Manager')])),
                ('group', models.ForeignKey(to='multitenancy.TenantGroup')),
                ('tenant', models.ForeignKey(blank=True, to='multitenancy.Tenant', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='tenantrole',
            index_together=set([('group', 'user')]),
        ),
    ]
