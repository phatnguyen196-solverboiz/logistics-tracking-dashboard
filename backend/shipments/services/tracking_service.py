import logging
import time
from collections.abc import Callable

from django.db import DatabaseError, transaction
from django.utils import timezone

from automation.carrier_base import CarrierTracker
from automation.demo_carrier import DemoExpressTracker
from automation.exceptions import TrackingAutomationError
from shipments.models import AutomationJob, Shipment, TrackingEvent

logger = logging.getLogger(__name__)


class TrackingService:
    def __init__(
        self,
        tracker_factory: Callable[[], CarrierTracker] | None = None,
        max_attempts: int = 3,
        retry_delay_seconds: float = 0.25,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.tracker_factory = tracker_factory or DemoExpressTracker
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.sleep = sleep

    def track_shipment(self, shipment: Shipment) -> AutomationJob:
        job = AutomationJob.objects.create(shipment=shipment)
        job.status = AutomationJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])

        errors: list[str] = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = self.tracker_factory().track(shipment.tracking_number)
                with transaction.atomic():
                    locked_shipment = Shipment.objects.select_for_update().get(pk=shipment.pk)
                    locked_shipment.current_status = result.status
                    locked_shipment.current_location = result.location
                    locked_shipment.save(update_fields=["current_status", "current_location", "updated_at"])
                    TrackingEvent.objects.create(
                        shipment=locked_shipment,
                        status=result.status,
                        location=result.location,
                        event_time=result.updated_at,
                    )
                    job.status = AutomationJob.Status.SUCCESS
                    job.finished_at = timezone.now()
                    job.error_message = ""
                    job.save(update_fields=["status", "finished_at", "error_message"])
                logger.info("Tracking succeeded shipment=%s attempt=%s", shipment.pk, attempt)
                return job
            except (TrackingAutomationError, DatabaseError) as exc:
                errors.append(f"attempt {attempt}: {exc}")
                logger.warning("Tracking attempt failed shipment=%s attempt=%s error=%s", shipment.pk, attempt, exc)
            except Exception as exc:  # defensive boundary around browser integrations
                errors.append(f"attempt {attempt}: unexpected automation error")
                logger.exception("Unexpected tracking failure shipment=%s attempt=%s", shipment.pk, attempt)

            if attempt < self.max_attempts:
                self.sleep(self.retry_delay_seconds * attempt)

        job.status = AutomationJob.Status.FAILED
        job.finished_at = timezone.now()
        job.error_message = "; ".join(errors)
        job.save(update_fields=["status", "finished_at", "error_message"])
        return job
