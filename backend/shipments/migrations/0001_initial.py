from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tracking_number", models.CharField(db_index=True, max_length=40, unique=True)),
                ("carrier", models.CharField(choices=[("DEMO_EXPRESS", "Demo Express")], default="DEMO_EXPRESS", max_length=32)),
                ("current_status", models.CharField(default="Pending", max_length=80)),
                ("current_location", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="TrackingEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(max_length=80)),
                ("location", models.CharField(blank=True, max_length=160)),
                ("event_time", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("shipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="shipments.shipment")),
            ],
            options={"ordering": ["-event_time", "-created_at"]},
        ),
        migrations.CreateModel(
            name="AutomationJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("RUNNING", "Running"), ("SUCCESS", "Success"), ("FAILED", "Failed")], db_index=True, default="PENDING", max_length=16)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("shipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="shipments.shipment")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
