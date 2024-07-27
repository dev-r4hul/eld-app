from django.urls import path
from .views import TruckListView, DriverListView,HOSViolationListView

urlpatterns = [
    path('trucks/', TruckListView.as_view(), name='truck-list'),
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('violations/', HOSViolationListView.as_view(), name='hos-violation-list'),
]
