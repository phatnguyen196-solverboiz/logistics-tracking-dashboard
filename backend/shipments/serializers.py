from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import AutomationJob, Shipment, TrackingEvent
from .services.validators import normalize_tracking_number


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            "id",
            "tracking_number",
            "carrier",
            "current_status",
            "current_location",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["current_status", "current_location", "created_at", "updated_at"]

    def validate_tracking_number(self, value: str) -> str:
        try:
            normalized = normalize_tracking_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        queryset = Shipment.objects.filter(tracking_number__iexact=normalized)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A shipment with this tracking number already exists.")
        return normalized


class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = ["id", "shipment", "status", "location", "event_time", "created_at"]
        read_only_fields = fields


class AutomationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationJob
        fields = [
            "id",
            "shipment",
            "status",
            "started_at",
            "finished_at",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields
