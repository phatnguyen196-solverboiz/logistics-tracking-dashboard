import logging
import time
from collections.abc import Callable

from django.db import DatabaseError, transaction
from django.utils import timezone

from automation.carrier_base import CarrierTracker
from automation.demo_carrier import DemoExpressTracker
from automation.exceptions import TrackingAutomationError, TrackingNotFoundError
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
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.tracker_factory = tracker_factory or DemoExpressTracker
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.sleep = sleep

    def track_shipment(self, shipment: Shipment) -> AutomationJob:
        job = AutomationJob.objects.create(
            shipment=shipment,
            status=AutomationJob.Status.RUNNING,
            started_at=timezone.now(),
        )

        errors: list[str] = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = self.tracker_factory().track(shipment.tracking_number)
                with transaction.atomic():
                    locked_shipment = Shipment.objects.select_for_update().get(pk=shipment.pk)
                    locked_shipment.current_status = result.status
                    locked_shipment.current_location = result.location
                    locked_shipment.save(update_fields=["current_status", "current_location", "updated_at"])
                    TrackingEvent.objects.get_or_create(
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
            except TrackingNotFoundError as exc:
                errors.append(str(exc))
                logger.info("Tracking number was not found shipment=%s", shipment.pk)
                break
            except TrackingAutomationError as exc:
                errors.append(str(exc))
                logger.warning("Tracking attempt failed shipment=%s attempt=%s error=%s", shipment.pk, attempt, exc)
            except DatabaseError:
                errors.append("Unable to save the carrier update. Please retry.")
                logger.exception("Database update failed shipment=%s", shipment.pk)
                break
            except Exception as exc:  # defensive boundary around browser integrations
                errors.append("Unexpected automation error. Please retry.")
                logger.exception("Unexpected tracking failure shipment=%s attempt=%s", shipment.pk, attempt)

            if attempt < self.max_attempts:
                self.sleep(self.retry_delay_seconds * attempt)

        job.status = AutomationJob.Status.FAILED
        job.finished_at = timezone.now()
        job.error_message = errors[-1] if errors else "Tracking failed. Please retry."
        job.save(update_fields=["status", "finished_at", "error_message"])
        return job
