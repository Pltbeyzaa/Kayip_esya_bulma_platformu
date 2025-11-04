from django.db import migrations, models
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageVector',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('image_path', models.CharField(max_length=500)),
                ('vector_id', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('location', models.CharField(max_length=200, blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_found', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='image_vectors', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'image_vectors',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ImageProcessingJob',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('image_path', models.CharField(max_length=500)),
                ('status', models.CharField(choices=[('pending', 'Bekliyor'), ('processing', 'İşleniyor'), ('completed', 'Tamamlandı'), ('failed', 'Başarısız')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='processing_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'image_processing_jobs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ImageMatch',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('similarity_score', models.FloatField()),
                ('match_confidence', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('source_vector', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='source_matches', to='image_matching.imagevector')),
                ('target_vector', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='target_matches', to='image_matching.imagevector')),
            ],
            options={
                'db_table': 'image_matches',
                'ordering': ['-similarity_score'],
                'unique_together': {('source_vector', 'target_vector')},
            },
        ),
    ]


