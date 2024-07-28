from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from version1.models import Truck, Driver, HOSViolation
from version1.serializers import (
    TruckSerializer,
    DriverSerializer,
    HOSViolationSerializer,
    ScheduleRequestSerializer,
)
from version1.utils import (
    check_hos_compliance,
    plan_driving_schedule,
    db_update_drivers,
    db_update_trucks,
)


class TruckViewSet(APIView):
    def get(self, request, truck_id=None):
        if truck_id:
            try:
                truckObj = Truck.objects.get(name=truck_id)
            except Truck.DoesNotExist:
                return Response(
                    {"error": "Truck not found"}, status=status.HTTP_404_NOT_FOUND
                )
            else:
                serializer = TruckSerializer(truckObj)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            trucks = Truck.objects.all()
            serializer = TruckSerializer(trucks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class DriverViewSet(APIView):
    def get(self, request, driver_id=None):
        if driver_id:
            try:
                driverObj = Driver.objects.get(driver_id=driver_id)
            except Driver.DoesNotExist:
                return Response(
                    {"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND
                )
            else:
                serializer = DriverSerializer(driverObj)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            drivers = Driver.objects.all()
            serializer = DriverSerializer(drivers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class HOSViolationListView(APIView):
    def get(self, request):
        violations = HOSViolation.objects.all()
        serializer = HOSViolationSerializer(violations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DriverViolationView(APIView):
    def get(self, request, driver_id):
        try:
            driverObj = Driver.objects.get(driver_id=driver_id)
        except Driver.DoesNotExist:
            return Response(
                {"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND
            )
        else:
            violations = check_hos_compliance(driver=driverObj)
            return Response(violations, status=status.HTTP_200_OK)


class ScheduleView(APIView):
    def post(self, request):
        serializer = ScheduleRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            schedule = plan_driving_schedule(**data)
            return Response(schedule, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateDbView(APIView):
    def get(self, request, model=None):
        if model not in ["drivers", "trucks", "all"]:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if model == "drivers":
            updated = db_update_drivers()
            if updated:
                return Response(
                    {"message": "Drivers successfully updated in database"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "Not able to update drivers in database"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        elif model == "trucks":
            updated = db_update_trucks()
            if updated:
                return Response(
                    {"message": "Trucks successfully updated in database"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "Not able to update trucks in database"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            updated_drivers = db_update_drivers()
            updated_trucks = db_update_trucks()
            if updated_drivers and updated_trucks:
                return Response(
                    {"message": "Drivers and Trucks successfully updated in database"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "Not able to update drivers/trucks in database"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
