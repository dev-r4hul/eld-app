from django.db import models

class Truck(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    speed = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Driver(models.Model):
    TRUCK_TYPE_CHOICES = [
        ('property', 'Property-Carrying'),
        ('passenger', 'Passenger-Carrying'),
    ]
    
    driver_id = models.CharField(max_length=255, unique=True)
    truck = models.ForeignKey('Truck', on_delete=models.SET_NULL, null=True)
    duty_status = models.CharField(max_length=50)
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
    adverse_conditions = models.BooleanField(default=False) 
    sleeper_berth_time = models.IntegerField(default=0)

    def __str__(self):
        return self.driver_id
    
class HOSViolation(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    violation_type = models.CharField(max_length=255)
    violation_description = models.TextField()
    violation_time = models.DateTimeField()

    def __str__(self):
        return f"{self.driver.driver_id} - {self.violation_type}"

