from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AutomationJob, Shipment
from .serializers import AutomationJobSerializer, ShipmentSerializer, TrackingEventSerializer
from .services.tracking_service import TrackingService


class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def track(self, request, pk=None):
        shipment = self.get_object()
        if shipment.jobs.filter(status=AutomationJob.Status.RUNNING).exists():
            return Response(
                {"detail": "Tracking is already running for this shipment."},
                status=status.HTTP_409_CONFLICT,
            )
        job = TrackingService().track_shipment(shipment)
        response_status = status.HTTP_200_OK if job.status == AutomationJob.Status.SUCCESS else status.HTTP_502_BAD_GATEWAY
        return Response(AutomationJobSerializer(job).data, status=response_status)

    @action(detail=True, methods=["get"])
    def events(self, request, pk=None):
        shipment = self.get_object()
        return Response(TrackingEventSerializer(shipment.events.all(), many=True).data)


class AutomationJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AutomationJob.objects.select_related("shipment").all()
    serializer_class = AutomationJobSerializer
    http_method_names = ["get", "head", "options"]
