from rest_framework.routers import DefaultRouter

from .views import AutomationJobViewSet, ShipmentViewSet

router = DefaultRouter()
router.register("shipments", ShipmentViewSet, basename="shipment")
router.register("jobs", AutomationJobViewSet, basename="job")

urlpatterns = router.urls
