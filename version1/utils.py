from datetime import timedelta
from version1.models import Truck, Driver
from version1.proLogsClient import PrologsAPIClient
from django.db import transaction
from dateutil import parser


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
    duty_time = driver.shift_work_minutes

    if driver.truck_type == "property":
        max_drive_minutes = driver.max_shift_drive_minutes or 660  # 11 hours
        max_duty_minutes = driver.max_shift_work_minutes or 840  # 14 hours

        # Check 11-hour driving limit
        if driver.shift_drive_minutes > max_drive_minutes:
            violations.append(
                {
                    "violation_type": "11-Hour Driving Limit",
                    "violation_description": f"Driver {driver.driver_id} drove for more than 11 hours.",
                }
            )

        # Check 14-hour on-duty limit
        if duty_time > max_duty_minutes:
            violations.append(
                {
                    "violation_type": "14-Hour On-Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} was on duty for more than 14 hours.",
                }
            )

        # Check 30-minute driving break requirement
        if driver.shift_drive_minutes >= 480 and not driver.took_break:
            violations.append(
                {
                    "violation_type": "30-Minute Break Requirement",
                    "violation_description": f"Driver {driver.driver_id} did not take a 30-minute break after 8 hours of driving.",
                }
            )

        # Check 60/70-hour limit
        if driver.cycle_work_minutes > driver.max_cycle_work_minutes:
            violations.append(
                {
                    "violation_type": "60/70-Hour On-Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} exceeded their cycle limit of {driver.max_cycle_work_minutes / 60} hours.",
                }
            )

        # Check sleeper berth provision
        if driver.sleeper_berth_time < 420:  # 7 hours
            violations.append(
                {
                    "violation_type": "Sleeper Berth Provision",
                    "violation_description": f"Driver {driver.driver_id} did not meet the sleeper berth requirement.",
                }
            )

    elif driver.truck_type == "passenger":
        max_drive_minutes = driver.max_shift_drive_minutes or 600  # 10 hours
        max_duty_minutes = driver.max_shift_work_minutes or 900  # 15 hours

        # Check 10-hour driving limit
        if driver.shift_drive_minutes > max_drive_minutes:
            violations.append(
                {
                    "violation_type": "10-Hour Driving Limit",
                    "violation_description": f"Driver {driver.driver_id} drove for more than 10 hours.",
                }
            )

        # Check 15-hour on-duty limit
        if duty_time > max_duty_minutes:
            violations.append(
                {
                    "violation_type": "15-Hour On-Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} was on duty for more than 15 hours.",
                }
            )

        # Check 60/70-hour limit
        if driver.cycle_work_minutes > driver.max_cycle_work_minutes:
            violations.append(
                {
                    "violation_type": "60/70-Hour On Duty Limit",
                    "violation_description": f"Driver {driver.driver_id} exceeded their cycle limit of {driver.max_cycle_work_minutes / 60} hours.",
                }
            )

        # Check sleeper berth provision
        if driver.sleeper_berth_time < 480:
            violations.append(
                {
                    "violation_type": "Sleeper Berth Provision",
                    "violation_description": f"Driver {driver.driver_id} did not meet the sleeper berth requirement.",
                }
            )

    return violations

def plan_driving_schedule(
    pickup_time,
    dropoff_time,
    loading_time: int,
    truck_type: str = "property",
):
    """
    Plan a driver's driving schedule based on pickup and dropoff times, including sleeper berth provision.

    :return: A driving schedule dict with a detailed plan
    """

    if truck_type == "property":
        MAX_DRIVING_HOURS = 11
        REST_HOURS = 10
    else:  # Passenger
        MAX_DRIVING_HOURS = 10
        REST_HOURS = 8

    time_until_dropoff = dropoff_time - pickup_time
    total_available_time = time_until_dropoff.total_seconds() / 3600
    total_driving_time = total_available_time - (loading_time / 60)
    driving_start_time = pickup_time + timedelta(minutes=loading_time)
    remaining_drive = 0

    schedule = {
        "start_time": driving_start_time,
        "driving_periods": [],
        "rest_periods": [],
        "total_driving_hours": 0,
        "total_rest_hours": 0,
    }

    while total_driving_time > 0:
        driving_hours = min(total_driving_time, MAX_DRIVING_HOURS)

        driving_end_time = driving_start_time + timedelta(hours=driving_hours)

        schedule["driving_periods"].append(
            {
                "start": driving_start_time,
                "end": driving_end_time,
                "hours": driving_hours,
            }
        )

        schedule["total_driving_hours"] += driving_hours
        total_driving_time -= driving_hours

        if total_driving_time <= 0 or driving_end_time >= dropoff_time:
            if driving_end_time >= dropoff_time:
                remaining_drive = driving_end_time - dropoff_time
                remaining_drive = remaining_drive.total_seconds() / 3600
                remaining_drive = MAX_DRIVING_HOURS - remaining_drive
            break

        rest_hours = REST_HOURS
        rest_end_time = driving_end_time + timedelta(hours=rest_hours)

        if rest_end_time > dropoff_time:
            rest_hours = (dropoff_time - driving_end_time).total_seconds() / 3600
            rest_end_time = dropoff_time

        schedule["rest_periods"].append(
            {
                "start": driving_end_time,
                "end": rest_end_time,
                "hours": rest_hours,
            }
        )

        schedule["total_rest_hours"] += rest_hours

        driving_start_time = rest_end_time
        if driving_start_time >= dropoff_time:
            break
    
    if remaining_drive: # add remaining hours in driving periods

        schedule["driving_periods"].append(
            {
                "start": schedule["rest_periods"][-1]['end'],
                "end": schedule["rest_periods"][-1]['end'] + timedelta(hours=remaining_drive),
                "hours": remaining_drive,
            }
        )

    schedule["message"] = "Schedule planned successfully within the given limits."
    return schedule

def check_hos_violation(
    pickup_time, dropoff_time, duty_statuses, truck_type="property"
):
    """
    Checks for HOS violations based on given duty statuses.

    :return: tuple - (violation, corrected_schedule)
    """

    if truck_type == "property":
        MAX_DRIVING_HOURS = 11
        REST_HOURS = 10
    else:  # Passenger
        MAX_DRIVING_HOURS = 10
        REST_HOURS = 8

    violation = False
    corrected_schedule = []

    for i, duty_status in enumerate(duty_statuses):
        start_time = parser.parse(duty_status["start_time"])
        end_time = parser.parse(duty_status["end_time"])

        if end_time < start_time:
            raise Exception(f"Invalid time interval {start_time} - {end_time}")

        if i == 0:
            if start_time < pickup_time:
                raise Exception(
                    f"Invalid start_time {start_time} : start_time must be equal or greater than pickup_time"
                )
        else:
            if start_time < parser.parse(duty_statuses[i - 1]["end_time"]):
                raise Exception(
                    f"Invalid start_time {start_time} : start_time must be equal or greater than end_time of previous status"
                )

        status = duty_status["status"]
        duration = (end_time - start_time).total_seconds() / 3600

        if truck_type == "property" and duration > 8:
            violation = True
            corrected_schedule.append(
                {
                    "suggestion": f"Driver Drove more than 8 cumulative hours without taking 30 minutes break in between {start_time} - {end_time}. Recommended to take 30 minute break",
                }
            )

        if status in ("driving", "D") and duration > MAX_DRIVING_HOURS:
            violation = True
            corrected_schedule.append(
                {
                    "suggestion": f"Exceeded driving limit between {start_time} - {end_time}. Recommend rest for {REST_HOURS} hours.",
                }
            )

        if (
            status in ("off_duty", "sleeper_berth", "SB", "OFF")
            and duration < REST_HOURS
        ):
            violation = True
            corrected_schedule.append(
                {
                    "suggestion": f"Insufficient rest between {start_time} - {end_time}. Increase rest time to {int(REST_HOURS - duration)} hours.",
                }
            )

    if not violation:
        corrected_schedule.append({"suggestion": "No violations detected."})

    return violation, corrected_schedule
