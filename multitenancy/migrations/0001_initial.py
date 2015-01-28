# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rapidsms', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackendLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('backend', models.OneToOneField(related_name='tenantlink', to='rapidsms.Backend')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ContactLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contact', models.OneToOneField(related_name='tenantlink', to='rapidsms.Contact')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(max_length=64)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TenantGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('slug', models.SlugField(unique=True, max_length=64)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='tenant',
            name='group',
            field=models.ForeignKey(related_name='tenants', to='multitenancy.TenantGroup'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='tenant',
            unique_together=set([('group', 'slug'), ('group', 'name')]),
        ),
        migrations.AddField(
            model_name='contactlink',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, to='multitenancy.Tenant', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='backendlink',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, to='multitenancy.Tenant', null=True),
            preserve_default=True,
        ),
    ]
