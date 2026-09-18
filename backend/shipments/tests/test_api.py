from datetime import datetime, timezone as dt_timezone

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from automation.carrier_base import TrackingResult
from automation.exceptions import TrackingNotFoundError
from shipments.models import AutomationJob, Shipment, TrackingEvent
from shipments.services.tracking_service import TrackingService


class SuccessfulTracker:
    def track(self, tracking_number: str) -> TrackingResult:
        return TrackingResult(
            tracking_number=tracking_number,
            status="In Transit",
            location="Da Nang",
            updated_at=datetime(2026, 9, 18, 7, 30, tzinfo=dt_timezone.utc),
        )


class FailedTracker:
    def track(self, tracking_number: str) -> TrackingResult:
        raise TrackingNotFoundError(f"{tracking_number} not found")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def shipment(db) -> Shipment:
    return Shipment.objects.create(tracking_number="VN000001", carrier=Shipment.Carrier.DEMO_EXPRESS)


@pytest.mark.django_db
def test_create_shipment(api_client: APIClient) -> None:
    response = api_client.post(reverse("shipment-list"), {"tracking_number": "vn000001", "carrier": "DEMO_EXPRESS"}, format="json")
    assert response.status_code == 201
    assert response.data["tracking_number"] == "VN000001"


@pytest.mark.django_db
def test_duplicate_tracking_number_validation(api_client: APIClient, shipment: Shipment) -> None:
    response = api_client.post(reverse("shipment-list"), {"tracking_number": "vn000001", "carrier": "DEMO_EXPRESS"}, format="json")
    assert response.status_code == 400
    assert "already exists" in str(response.data).lower()


@pytest.mark.django_db
def test_list_and_retrieve_shipments(api_client: APIClient, shipment: Shipment) -> None:
    listing = api_client.get(reverse("shipment-list"))
    detail = api_client.get(reverse("shipment-detail", args=[shipment.pk]))
    assert listing.status_code == 200
    assert len(listing.data) == 1
    assert detail.data["tracking_number"] == "VN000001"


@pytest.mark.django_db
def test_invalid_tracking_number(api_client: APIClient) -> None:
    response = api_client.post(reverse("shipment-list"), {"tracking_number": "!?", "carrier": "DEMO_EXPRESS"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_valid_tracking_job_creates_event(api_client: APIClient, shipment: Shipment, monkeypatch) -> None:
    monkeypatch.setattr(
        "shipments.views.TrackingService",
        lambda: TrackingService(tracker_factory=SuccessfulTracker, sleep=lambda _delay: None),
    )
    response = api_client.post(reverse("shipment-track", args=[shipment.pk]))
    shipment.refresh_from_db()
    assert response.status_code == 200
    assert response.data["status"] == AutomationJob.Status.SUCCESS
    assert shipment.current_status == "In Transit"
    assert TrackingEvent.objects.filter(shipment=shipment, location="Da Nang").exists()


@pytest.mark.django_db
def test_failed_tracking_job(api_client: APIClient, shipment: Shipment, monkeypatch) -> None:
    monkeypatch.setattr(
        "shipments.views.TrackingService",
        lambda: TrackingService(tracker_factory=FailedTracker, sleep=lambda _delay: None),
    )
    response = api_client.post(reverse("shipment-track", args=[shipment.pk]))
    assert response.status_code == 502
    assert response.data["status"] == AutomationJob.Status.FAILED
    assert "attempt 3" in response.data["error_message"]


@pytest.mark.django_db
def test_events_endpoint(api_client: APIClient, shipment: Shipment) -> None:
    TrackingEvent.objects.create(
        shipment=shipment,
        status="Delivered",
        location="Ho Chi Minh City",
        event_time=datetime.now(dt_timezone.utc),
    )
    response = api_client.get(reverse("shipment-events", args=[shipment.pk]))
    assert response.status_code == 200
    assert response.data[0]["status"] == "Delivered"


@pytest.mark.django_db
def test_job_retrieve(api_client: APIClient, shipment: Shipment) -> None:
    job = AutomationJob.objects.create(shipment=shipment)
    response = api_client.get(reverse("job-detail", args=[job.pk]))
    assert response.status_code == 200
    assert response.data["status"] == AutomationJob.Status.PENDING
