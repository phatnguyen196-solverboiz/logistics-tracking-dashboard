from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone


def fail_duplicate_running_jobs(apps, schema_editor):
    """Keep the newest active job per shipment before adding the constraint."""
    AutomationJob = apps.get_model("shipments", "AutomationJob")
    database = schema_editor.connection.alias
    seen_shipments = set()
    duplicates = []

    jobs = AutomationJob.objects.using(database).filter(status="RUNNING").order_by(
        "shipment_id", "-created_at", "-pk"
    )
    for job in jobs.iterator():
        if job.shipment_id in seen_shipments:
            duplicates.append(job.pk)
        else:
            seen_shipments.add(job.shipment_id)

    if duplicates:
        AutomationJob.objects.using(database).filter(pk__in=duplicates).update(
            status="FAILED",
            finished_at=timezone.now(),
            error_message="Closed duplicate active job while applying tracking concurrency fix.",
        )


class Migration(migrations.Migration):
    dependencies = [("shipments", "0001_initial")]

    operations = [
        migrations.RunPython(fail_duplicate_running_jobs, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="automationjob",
            constraint=models.UniqueConstraint(
                condition=Q(status="RUNNING"),
                fields=("shipment",),
                name="one_running_job_per_ship",
            ),
        ),
    ]
