from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.db import transaction
from .models import Truck, Driver, HOSViolation
from .serializers import TruckSerializer, DriverSerializer,HOSViolationSerializer
from .utils import get_access_token

class TruckListView(APIView):
    def get(self, request):
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get('https://publicapi-stage.prologs.us/api/v1/trucks', headers=headers)

        if response.status_code == 401:
            access_token = get_access_token(refresh=True)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.get('https://publicapi-stage.prologs.us/api/v1/trucks', headers=headers)
        

        if response.status_code == 200:
            trucks_data = response.json()

            new_trucks = []
            update_trucks = []
            existing_trucks = Truck.objects.in_bulk(field_name='name')
            
            for truck_data in trucks_data:
                truck_name = truck_data['name']
                location = truck_data.get('location')
                latitude = truck_data.get('lat')
                longitude = truck_data.get('lng')
                speed = truck_data.get('speed')
                
                if truck_name in existing_trucks:
                    truck = existing_trucks[truck_name]
                    truck.location = location
                    truck.latitude = latitude
                    truck.longitude = longitude
                    truck.speed = speed
                    update_trucks.append(truck)
                else:
                    new_trucks.append(Truck(
                        name=truck_name,
                        location=location,
                        latitude=latitude,
                        longitude=longitude,
                        speed=speed
                    ))

            with transaction.atomic():
                Truck.objects.bulk_create(new_trucks, ignore_conflicts=True)
                Truck.objects.bulk_update(update_trucks, fields=['location', 'latitude', 'longitude', 'speed'])

            trucks = Truck.objects.all()
            serializer = TruckSerializer(trucks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response({'error': 'Failed to fetch data from ProLogs API'}, status=response.status_code)

class DriverListView(APIView):
    def get(self, request):
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get('https://publicapi-stage.prologs.us/api/v1/drivers', headers=headers)
        
        if response.status_code == 401:
            access_token = get_access_token(refresh=True)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.get('https://publicapi-stage.prologs.us/api/v1/drivers', headers=headers)
            
        if response.status_code == 200:
            drivers_data = response.json()

            existing_drivers = Driver.objects.in_bulk(field_name='driver_id')
            existing_trucks = Truck.objects.in_bulk(field_name='name')

            new_drivers = []
            update_drivers = []

            for driver_data in drivers_data:
                driver_id = driver_data['driverId']
                truck_name = driver_data.get('truckName')
                truck = existing_trucks.get(truck_name) 

                driver_defaults = {
                    'truck': truck,
                    'duty_status': driver_data.get('dutyStatus'),
                    'duty_status_start_time': driver_data.get('dutyStatusStartTime'),
                    'shift_work_minutes': driver_data.get('shiftWorkMinutes'),
                    'shift_drive_minutes': driver_data.get('shiftDriveMinutes'),
                    'cycle_work_minutes': driver_data.get('cycleWorkMinutes'),
                    'max_shift_work_minutes': driver_data.get('maxShiftWorkMinutes', 840),
                    'max_shift_drive_minutes': driver_data.get('maxShiftDriveMinutes', 660),
                    'max_cycle_work_minutes': driver_data.get('maxCycleWorkMinutes', 4200),
                    'home_terminal_timezone_windows': driver_data.get('homeTerminalTimeZoneWindows'),
                    'home_terminal_timezone_iana': driver_data.get('homeTerminalTimeZoneIana'),
                }

                if driver_id in existing_drivers:
                    driver = existing_drivers[driver_id]
                    for field, value in driver_defaults.items():
                        setattr(driver, field, value)
                    update_drivers.append(driver)
                else:
                    new_drivers.append(Driver(driver_id=driver_id, **driver_defaults))

            with transaction.atomic():
                Driver.objects.bulk_create(new_drivers, ignore_conflicts=True)
                Driver.objects.bulk_update(
                    update_drivers,
                    fields=[
                        'truck',
                        'duty_status',
                        'duty_status_start_time',
                        'shift_work_minutes',
                        'shift_drive_minutes',
                        'cycle_work_minutes',
                        'max_shift_work_minutes',
                        'max_shift_drive_minutes',
                        'max_cycle_work_minutes',
                        'home_terminal_timezone_windows',
                        'home_terminal_timezone_iana',
                    ]
                )

            drivers = Driver.objects.all()
            serializer = DriverSerializer(drivers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response({'error': 'Failed to fetch data from ProLogs API'}, status=response.status_code)


class HOSViolationListView(APIView):
    def get(self, request):
        violations = HOSViolation.objects.all()
        serializer = HOSViolationSerializer(violations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)