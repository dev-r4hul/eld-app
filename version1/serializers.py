from rest_framework import serializers
from .models import Truck,Driver

class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'
class ScheduleRequestSerializer(serializers.Serializer):
    pickup_time = serializers.DateTimeField()
    dropoff_time = serializers.DateTimeField()
    total_distance = serializers.FloatField()
    avg_speed = serializers.FloatField()
    # current_time = serializers.DateTimeField()
    sleeper_berth_flexibility = serializers.BooleanField(default=True)
    driver_type = serializers.ChoiceField(choices=[('property', 'Property'), ('passenger', 'Passenger')])