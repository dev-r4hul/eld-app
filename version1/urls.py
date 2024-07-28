from django.urls import path
from .views import (
    HOSViolationListView,
    DriverViolationView,
    ScheduleView,
    DriverViewSet,
    TruckViewSet,
    UpdateDbView,
)

urlpatterns = [
    path("trucks/", TruckViewSet.as_view(), name="truck-list"),
    path("trucks/<int:truck_id>/", TruckViewSet.as_view(), name="truck"),
    path("drivers/", DriverViewSet.as_view(), name="driver-list"),
    path("drivers/<int:driver_id>/", DriverViewSet.as_view(), name="driver"),
    path("schedule/", ScheduleView.as_view(), name="plan_schedule"),
    path("update_db/<str:model>/", UpdateDbView.as_view(), name="update_db"),
    path("violations/", HOSViolationListView.as_view(), name="hos-violation-list"),
    path(
        "violations/<int:driver_id>/",
        DriverViolationView.as_view(),
        name="driver-violations",
    ),
]
