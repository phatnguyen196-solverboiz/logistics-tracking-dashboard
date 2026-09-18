from datetime import datetime, timezone as dt_timezone

import pytest

from automation.carrier_base import TrackingResult
from automation.exceptions import CarrierUnavailableError, TrackingNotFoundError
from shipments.models import AutomationJob, Shipment, TrackingEvent
from shipments.services.tracking_service import TrackingService


class CountingTracker:
    calls = 0

    def track(self, tracking_number: str) -> TrackingResult:
        type(self).calls += 1
        if type(self).calls < 3:
            raise CarrierUnavailableError("temporary outage")
        return TrackingResult(tracking_number, "Delivered", "Hanoi", datetime.now(dt_timezone.utc))


@pytest.mark.django_db
def test_carrier_service_retries_then_succeeds() -> None:
    CountingTracker.calls = 0
    shipment = Shipment.objects.create(tracking_number="VN000099")
    service = TrackingService(tracker_factory=CountingTracker, sleep=lambda _delay: None)
    job = service.track_shipment(shipment)
    assert CountingTracker.calls == 3
    assert job.status == AutomationJob.Status.SUCCESS
    assert shipment.events.count() == 1


@pytest.mark.django_db
def test_service_records_failure_after_three_attempts() -> None:
    class AlwaysFails:
        def track(self, tracking_number: str) -> TrackingResult:
            raise CarrierUnavailableError("offline")

    shipment = Shipment.objects.create(tracking_number="VN000100")
    job = TrackingService(tracker_factory=AlwaysFails, sleep=lambda _delay: None).track_shipment(shipment)
    assert job.status == AutomationJob.Status.FAILED
    assert job.finished_at is not None
    assert job.error_message == "offline"


@pytest.mark.django_db
def test_not_found_is_not_retried() -> None:
    class NotFoundTracker:
        calls = 0

        def track(self, tracking_number: str) -> TrackingResult:
            type(self).calls += 1
            raise TrackingNotFoundError("not found")

    shipment = Shipment.objects.create(tracking_number="VN000101")
    job = TrackingService(tracker_factory=NotFoundTracker, sleep=lambda _delay: None).track_shipment(shipment)
    assert NotFoundTracker.calls == 1
    assert job.status == AutomationJob.Status.FAILED
    assert job.error_message == "not found"


@pytest.mark.django_db
def test_repeated_identical_result_does_not_duplicate_history() -> None:
    event_time = datetime.now(dt_timezone.utc)

    class SameResultTracker:
        def track(self, tracking_number: str) -> TrackingResult:
            return TrackingResult(tracking_number, "Delivered", "Hanoi", event_time)

    shipment = Shipment.objects.create(tracking_number="VN000102")
    service = TrackingService(tracker_factory=SameResultTracker, sleep=lambda _delay: None)
    service.track_shipment(shipment)
    service.track_shipment(shipment)
    assert TrackingEvent.objects.filter(shipment=shipment).count() == 1
