from rest_framework import serializers
from .models import Truck, Driver


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = "__all__"


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = "__all__"


class ScheduleRequestSerializer(serializers.Serializer):
    pickup_time = serializers.DateTimeField()
    dropoff_time = serializers.DateTimeField()
    loading_time = serializers.IntegerField()
    truck_type = serializers.ChoiceField(
        choices=[("property", "Property"), ("passenger", "Passenger")]
    )


class DutyStatusSerializer(serializers.Serializer):
    pickup_time = serializers.DateTimeField()
    dropoff_time = serializers.DateTimeField()
    truck_type = serializers.ChoiceField(
        choices=[("property", "Property"), ("passenger", "Passenger")]
    )
    duty_statuses = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
