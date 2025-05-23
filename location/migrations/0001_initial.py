# Generated by Django 5.1.4 on 2025-05-16 16:59

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('location', models.CharField(max_length=64)),
                ('type', models.CharField(default='', max_length=18)),
                ('tags', models.TextField(default='')),
                ('rating', models.FloatField(default=5)),
                ('open_time', models.TimeField(default=datetime.time(0, 0))),
                ('close_time', models.TimeField(default=datetime.time(23, 59))),
                ('ticket_info', models.CharField(default='', max_length=100)),
                ('address', models.CharField(default='', max_length=100)),
                ('image_path', models.CharField(default='', max_length=255)),
                ('description', models.TextField(default='')),
                ('long_description', models.TextField(default='')),
                ('coordinate', models.CharField(default='', max_length=40)),
                ('favourited_by', models.ManyToManyField(blank=True, related_name='favourite_locations', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('rating', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_edited', models.BooleanField(default=False)),
                ('is_flagged', models.BooleanField(default=False)),
                ('bot_reply', models.TextField(blank=True, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='location.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='location.location')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Location_List',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location_list', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TripList',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False)),
                ('name', models.CharField(default='My trip list', max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trip_lists', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TripPath',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path_name', models.CharField(default='', max_length=255)),
                ('locations_ordered', models.CharField(max_length=255)),
                ('total_distance', models.FloatField(blank=True, null=True)),
                ('total_duration', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('trip_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trip_paths', to='location.triplist')),
            ],
        ),
    ]
