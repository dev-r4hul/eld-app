import math
from django.utils import timezone
from datetime import timedelta
from version1.models import Truck, Driver, HOSViolation
from version1.proLogsClient import PrologsAPIClient
from django.db import transaction

def db_update_drivers() -> bool:
    try:
        prologObj = PrologsAPIClient()
        drivers_data = prologObj.get_drivers()

        existing_drivers = Driver.objects.in_bulk(field_name="driver_id")
        existing_trucks = Truck.objects.in_bulk(field_name="name")

        new_drivers = []
        update_drivers = []

        for driver_data in drivers_data:
            driver_id = driver_data["driverId"].strip()
            truck_name = driver_data.get("truckName")
            truck = existing_trucks.get(truck_name)

            driver_defaults = {
                "truck": truck,
                "duty_status": driver_data.get("dutyStatus"),
                "duty_status_start_time": driver_data.get("dutyStatusStartTime"),
                "shift_work_minutes": driver_data.get("shiftWorkMinutes"),
                "shift_drive_minutes": driver_data.get("shiftDriveMinutes"),
                "cycle_work_minutes": driver_data.get("cycleWorkMinutes"),
                "max_shift_work_minutes": driver_data.get("maxShiftWorkMinutes", 840),
                "max_shift_drive_minutes": driver_data.get("maxShiftDriveMinutes", 660),
                "max_cycle_work_minutes": driver_data.get("maxCycleWorkMinutes", 4200),
                "home_terminal_timezone_windows": driver_data.get(
                    "homeTerminalTimeZoneWindows"
                ),
                "home_terminal_timezone_iana": driver_data.get(
                    "homeTerminalTimeZoneIana"
                ),
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
                    "truck",
                    "duty_status",
                    "duty_status_start_time",
                    "shift_work_minutes",
                    "shift_drive_minutes",
                    "cycle_work_minutes",
                    "max_shift_work_minutes",
                    "max_shift_drive_minutes",
                    "max_cycle_work_minutes",
                    "home_terminal_timezone_windows",
                    "home_terminal_timezone_iana",
                ],
            )
    except Exception as ex:
        print(f"Eception in db_update_drivers : {ex}")
        return False
    else:
        return True


def db_update_trucks() -> bool:
    try:
        prologObj = PrologsAPIClient()
        trucks_data = prologObj.get_trucks()

        new_trucks = []
        update_trucks = []
        existing_trucks = Truck.objects.in_bulk(field_name="name")

        for truck_data in trucks_data:
            truck_name = truck_data["name"].strip()
            location = truck_data.get("location")
            latitude = truck_data.get("lat")
            longitude = truck_data.get("lng")
            speed = truck_data.get("speed")

            if truck_name in existing_trucks:
                truck = existing_trucks[truck_name]
                truck.location = location
                truck.latitude = latitude
                truck.longitude = longitude
                truck.speed = speed
                update_trucks.append(truck)
            else:
                new_trucks.append(
                    Truck(
                        name=truck_name,
                        location=location,
                        latitude=latitude,
                        longitude=longitude,
                        speed=speed,
                    )
                )

        with transaction.atomic():
            Truck.objects.bulk_create(new_trucks, ignore_conflicts=True)
            Truck.objects.bulk_update(
                update_trucks, fields=["location", "latitude", "longitude", "speed"]
            )
    except Exception as ex:
        print(f"Eception in db_update_trucks : {ex}")
        return False
    else:
        return True


def check_hos_compliance(driver):
    """
    Evaluates HOS compliance for a given driver based on FMCSA regulations.
    """
    violations = []
    current_time = timezone.now()

    if driver.truck_type == "property":
        max_drive_minutes = 660

        if driver.shift_drive_minutes > max_drive_minutes:
            violations.append(
                {
                    "violation_type": "11-Hour Driving Limit",
                    "violation_description": f"Driver {driver.driver_id} drove for more than 11 hours.",
                    "violation_time": current_time,
                }
            )

        # Check 14-hour on-duty limit
        duty_time = (current_time - driver.duty_status_start_time).total_seconds() / 60
        max_duty_minutes = 840  # 14 hours

        if duty_time > max_duty_minutes:
            violations.append(
                {
                    "violation_type": "14-Hour On-Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} was on duty for more than 14 hours.",
                    "violation_time": current_time,
                }
            )

        # Check 30-minute driving break requirement
        if driver.shift_drive_minutes >= 480 and not driver.took_break:
            violations.append(
                {
                    "violation_type": "30-Minute Break Requirement",
                    "violation_description": f"Driver {driver.driver_id} did not take a 30-minute break after 8 hours of driving.",
                    "violation_time": current_time,
                }
            )

        # Check 60/70-hour limit
        if driver.cycle_work_minutes > driver.max_cycle_work_minutes:
            violations.append(
                {
                    "violation_type": "60/70-Hour On-Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} exceeded their cycle limit of {driver.max_cycle_work_minutes / 60} hours.",
                    "violation_time": current_time,
                }
            )

        # Check sleeper berth provision
        if driver.sleeper_berth_time < 420:  # 7 hours
            violations.append(
                {
                    "violation_type": "Sleeper Berth Provision",
                    "violation_description": f"Driver {driver.driver_id} did not meet the sleeper berth requirement.",
                    "violation_time": current_time,
                }
            )

    elif driver.truck_type == "passenger":
        max_drive_minutes = 600

        if driver.shift_drive_minutes > max_drive_minutes:
            violations.append(
                {
                    "violation_type": "10-Hour Driving Limit",
                    "violation_description": f"Driver {driver.driver_id} drove for more than 10 hours.",
                    "violation_time": current_time,
                }
            )

        # Check 15-hour on-duty limit
        duty_time = (current_time - driver.duty_status_start_time).total_seconds() / 60
        max_duty_minutes = 900

        if duty_time > max_duty_minutes:
            violations.append(
                {
                    "violation_type": "15-Hour On-Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} was on duty for more than 15 hours.",
                    "violation_time": current_time,
                }
            )

        # Check 60/70-hour limit
        if driver.cycle_work_minutes > driver.max_cycle_work_minutes:
            violations.append(
                {
                    "violation_type": "60/70-Hour On Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} exceeded their cycle limit of {driver.max_cycle_work_minutes / 60} hours.",
                    "violation_time": current_time,
                }
            )

        # Check sleeper berth provision
        if driver.sleeper_berth_time < 480:
            violations.append(
                {
                    "violation_type": "Sleeper Berth Provision",
                    "violation_description": f"Driver {driver.driver_id} did not meet the sleeper berth requirement.",
                    "violation_time": current_time,
                }
            )

    # Store violations
    # for violation in violations:
    #     HOSViolation.objects.create(
    #         driver=driver,
    #         violation_type=violation['violation_type'],
    #         violation_description=violation['violation_description'],
    #         violation_time=violation['violation_time']
    #     )

    return violations


def plan_driving_schedule(
    pickup_time,
    dropoff_time,
    total_distance,
    avg_speed,
    sleeper_berth_flexibility,
    driver_type="property",
):
    """
    Plan a driver's driving schedule based on pickup and dropoff times, including sleeper berth provision.

    :param pickup_time: Scheduled pickup time (datetime object)
    :param dropoff_time: Scheduled dropoff time (datetime object)
    :param total_distance: Total distance to be covered (in miles)
    :param avg_speed: Average driving speed (in miles per hour)
    :param sleeper_berth_flexibility: Boolean indicating if sleeper berth provision can be used
    :param driver_type: 'property' for property-carrying drivers or 'passenger' for passenger-carrying drivers
    :return: A driving schedule dict with detailed plan and HOS compliance status
    """

    if driver_type == "property":
        MAX_DRIVING_HOURS = 11
        REST_HOURS = 10
        MAX_SHIFT_HOURS = 14
    else:  # Passenger
        MAX_DRIVING_HOURS = 10
        REST_HOURS = 8
        MAX_SHIFT_HOURS = 15

    # Calculate total driving time needed
    total_driving_time = total_distance / avg_speed
    total_driving_hours = math.ceil(
        total_driving_time
    )  # Round up to the nearest hour for planning

    # Calculate time available until dropoff
    time_until_dropoff = dropoff_time - pickup_time
    available_hours = time_until_dropoff.total_seconds() / 3600

    # Initialize schedule
    schedule = {
        "start_time": pickup_time,
        "driving_periods": [],
        "rest_periods": [],
        "total_driving_hours": 0,
        "total_rest_hours": 0,
        "hos_compliance": True,
        "message": "",
    }

    # If total driving hours exceed available hours, we can't make it on time
    if total_driving_hours > available_hours:
        schedule["hos_compliance"] = False
        schedule["message"] = "Unable to meet dropoff time within HOS limits."
        return schedule

    # Calculate driving and rest periods
    current_driving_hours = 0
    current_rest_hours = 0
    driving_start_time = pickup_time

    while total_driving_hours > 0:
        # Calculate driving session
        driving_hours = min(total_driving_hours, MAX_DRIVING_HOURS)
        driving_end_time = driving_start_time + timedelta(hours=driving_hours)

        # Add driving session to schedule
        schedule["driving_periods"].append(
            {
                "start": driving_start_time,
                "end": driving_end_time,
                "hours": driving_hours,
            }
        )

        # Update schedule totals
        schedule["total_driving_hours"] += driving_hours
        total_driving_hours -= driving_hours
        current_driving_hours += driving_hours

        # Check if more driving is needed
        if total_driving_hours <= 0:
            break

        # Calculate rest period
        if sleeper_berth_flexibility and current_driving_hours >= 7:
            # Use sleeper berth split
            rest_hours = 3
            current_rest_hours += rest_hours

            # First rest split
            rest_end_time = driving_end_time + timedelta(hours=2)
            schedule["rest_periods"].append(
                {"start": driving_end_time, "end": rest_end_time, "hours": 2}
            )
            driving_start_time = rest_end_time

            # Second rest split
            rest_end_time = driving_start_time + timedelta(hours=1)
            schedule["rest_periods"].append(
                {"start": driving_start_time, "end": rest_end_time, "hours": 1}
            )
            driving_start_time = rest_end_time

            # Reset sleeper berth flexibility
            sleeper_berth_flexibility = False
        else:
            # Full rest period
            rest_hours = REST_HOURS
            current_rest_hours += rest_hours
            rest_end_time = driving_end_time + timedelta(hours=rest_hours)
            schedule["rest_periods"].append(
                {"start": driving_end_time, "end": rest_end_time, "hours": rest_hours}
            )
            driving_start_time = rest_end_time
            current_driving_hours = 0

        # Update schedule totals
        schedule["total_rest_hours"] += rest_hours

        # Check if we're exceeding shift limits
        if (driving_start_time - pickup_time).total_seconds() / 3600 > MAX_SHIFT_HOURS:
            schedule["hos_compliance"] = False
            schedule["message"] = "Exceeded maximum shift hours without adequate rest."
            return schedule

    # Final check for HOS compliance
    if (
        schedule["total_driving_hours"] > MAX_DRIVING_HOURS
        or schedule["total_rest_hours"] < REST_HOURS
    ):
        schedule["hos_compliance"] = False
        schedule["message"] = (
            "HOS violation detected: Driving or rest hours exceeded limits."
        )

    if schedule["hos_compliance"]:
        schedule["message"] = "Schedule is compliant with HOS regulations."

    return schedule
