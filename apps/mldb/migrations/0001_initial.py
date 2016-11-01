# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-01 17:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=128)),
                ('slug', models.CharField(max_length=128, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=128, unique=True)),
                ('title', models.CharField(max_length=128, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.SmallIntegerField()),
                ('text', models.TextField()),
                ('characters', models.ManyToManyField(to='mldb.Character')),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mldb.Episode')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([('episode', 'order')]),
        ),
    ]
