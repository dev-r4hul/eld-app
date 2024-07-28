from django.db import models

class Truck(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    speed = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

TRUCK_TYPE_CHOICES = [
    ('property', 'Property-Carrying'),
    ('passenger', 'Passenger-Carrying'),
]

DUTY_STATUS = [
    ('D', 'Driving'),
    ('SB', 'Sleeper Berth'),
    ('OFF', 'Off-Duty'),
    ('ODND', 'On-Duty Not Driving'),
]
class Driver(models.Model):

    driver_id = models.CharField(max_length=255, unique=True,db_index=True)
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True)
    duty_status = models.CharField(max_length=50, choices=DUTY_STATUS)
    duty_status_start_time = models.DateTimeField(null=True, blank=True)
    shift_work_minutes = models.IntegerField(default=0)
    shift_drive_minutes = models.IntegerField(default=0)
    cycle_work_minutes = models.IntegerField(default=0)
    max_shift_work_minutes = models.IntegerField(default=840) 
    max_shift_drive_minutes = models.IntegerField(default=660)
    max_cycle_work_minutes = models.IntegerField(default=4200)
    took_break = models.BooleanField(default=False)
    home_terminal_timezone_windows = models.CharField(max_length=255, null=True, blank=True)
    home_terminal_timezone_iana = models.CharField(max_length=255, null=True, blank=True)
    truck_type = models.CharField(max_length=20, choices=TRUCK_TYPE_CHOICES, default='property')
    sleeper_berth_time = models.IntegerField(default=0)

    def __str__(self):
        return self.driver_id