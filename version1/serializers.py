from rest_framework import serializers
from .models import Truck,Driver,HOSViolation

class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'

class HOSViolationSerializer(serializers.ModelSerializer):
    driver_id = serializers.CharField(source='driver.driver_id', read_only=True)

    class Meta:
        model = HOSViolation
        fields = ['driver_id', 'violation_type', 'violation_description', 'violation_time']

class ScheduleRequestSerializer(serializers.Serializer):
    pickup_time = serializers.DateTimeField()
    dropoff_time = serializers.DateTimeField()
    total_distance = serializers.FloatField()
    avg_speed = serializers.FloatField()
    # current_time = serializers.DateTimeField()
    sleeper_berth_flexibility = serializers.BooleanField(default=True)
    driver_type = serializers.ChoiceField(choices=[('property', 'Property'), ('passenger', 'Passenger')])