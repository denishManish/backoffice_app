# Generated by Django 5.0.3 on 2024-03-26 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('opening_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=25)),
                ('note', models.TextField(blank=True, null=True)),
                ('country', models.CharField(max_length=50)),
                ('region', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=50)),
                ('street', models.CharField(max_length=50)),
                ('house', models.PositiveSmallIntegerField()),
                ('address_note', models.CharField(blank=True, max_length=150, null=True)),
            ],
        ),
    ]
