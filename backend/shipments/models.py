from django.db import models


class Shipment(models.Model):
    class Carrier(models.TextChoices):
        DEMO_EXPRESS = "DEMO_EXPRESS", "Demo Express"

    tracking_number = models.CharField(max_length=40, unique=True, db_index=True)
    carrier = models.CharField(max_length=32, choices=Carrier.choices, default=Carrier.DEMO_EXPRESS)
    current_status = models.CharField(max_length=80, default="Pending")
    current_location = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.tracking_number} ({self.current_status})"


class TrackingEvent(models.Model):
    shipment = models.ForeignKey(Shipment, related_name="events", on_delete=models.CASCADE)
    status = models.CharField(max_length=80)
    location = models.CharField(max_length=160, blank=True)
    event_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-event_time", "-created_at"]


class AutomationJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    shipment = models.ForeignKey(Shipment, related_name="jobs", on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
