import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from .models import HOSViolation
from django.conf import settings

PROLOGS_TOKEN_URL = "https://identity-stage.prologs.us/connect/token"

def get_access_token(refresh=False):
    """
    Obtain access token from token.json file.
    """

    token_file = 'token.json'
    tokenObj = {}

    if not refresh and Path(token_file).exists():
        with open(token_file,'r') as fp:
            tokenObj = json.load(fp)
            if 'access_token' in tokenObj:
                return tokenObj['access_token']

    else:
        tokenObj = refresh_access_token()
        with open(token_file,'w') as fp:
            json.dump(tokenObj,fp,indent=4)
        
    return tokenObj['access_token'] if 'access_token' in tokenObj else None

def refresh_access_token():
    """
    Obtain an access token from the ProLogs API.
    """

    data = {
        'grant_type': 'client_credentials',
        'client_id': settings.PROLOG_CLIENT_ID,
        'client_secret': settings.PROLOG_CLIENT_SECRET
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(PROLOGS_TOKEN_URL, data=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to obtain access token: {response.text}")
    


def check_hos_compliance(driver):
    """
    Evaluates HOS compliance for a given driver based on FMCSA regulations.
    """
    violations = []
    current_time = datetime.now()

    if driver.truck_type == 'property':
        max_drive_minutes = 660
        if driver.adverse_conditions:
            max_drive_minutes += 120

        if driver.shift_drive_minutes > max_drive_minutes:
            violations.append({
                'violation_type': '11-Hour Driving Limit',
                'violation_description': f"Driver {driver.driver_id} drove for more than 11 hours.",
                'violation_time': current_time,
            })

        # Check 14-hour on-duty limit
        duty_time = (current_time - driver.duty_status_start_time).total_seconds() / 60
        max_duty_minutes = 840  # 14 hours
        if driver.adverse_conditions:
            max_duty_minutes += 120  # Extend by 2 hours for adverse conditions

        if duty_time > max_duty_minutes:
            violations.append({
                'violation_type': '14-Hour On-Duty Limit',
                'violation_description': f"Driver {driver.driver_id} was on duty for more than 14 hours.",
                'violation_time': current_time,
            })

        # Check 30-minute driving break requirement
        if driver.shift_drive_minutes >= 480 and not driver.took_break:
            violations.append({
                'violation_type': '30-Minute Break Requirement',
                'violation_description': f"Driver {driver.driver_id} did not take a 30-minute break after 8 hours of driving.",
                'violation_time': current_time,
            })

        # Check 60/70-hour limit
        if driver.cycle_work_minutes > driver.max_cycle_work_minutes:
            violations.append({
                'violation_type': '60/70-Hour On-Duty Limit',
                'violation_description': f"Driver {driver.driver_id} exceeded their cycle limit of {driver.max_cycle_work_minutes / 60} hours.",
                'violation_time': current_time,
            })

        # Check sleeper berth provision
        if driver.sleeper_berth_time < 420:  # 7 hours
            violations.append({
                'violation_type': 'Sleeper Berth Provision',
                'violation_description': f"Driver {driver.driver_id} did not meet the sleeper berth requirement.",
                'violation_time': current_time,
            })

    elif driver.truck_type == 'passenger':
        max_drive_minutes = 600  
        if driver.adverse_conditions:
            max_drive_minutes += 120 

        if driver.shift_drive_minutes > max_drive_minutes:
            violations.append({
                'violation_type': '10-Hour Driving Limit',
                'violation_description': f"Driver {driver.driver_id} drove for more than 10 hours.",
                'violation_time': current_time,
            })

        # Check 15-hour on-duty limit
        duty_time = (current_time - driver.duty_status_start_time).total_seconds() / 60
        max_duty_minutes = 900 
        if driver.adverse_conditions:
            max_duty_minutes += 120  

        if duty_time > max_duty_minutes:
            violations.append({
                'violation_type': '15-Hour On-Duty Limit',
                'violation_description': f"Driver {driver.driver_id} was on duty for more than 15 hours.",
                'violation_time': current_time,
            })

        # Check 60/70-hour limit
        if driver.cycle_work_minutes > driver.max_cycle_work_minutes:
            violations.append({
                'violation_type': '60/70-Hour On Duty Limit',
                'violation_description': f"Driver {driver.driver_id} exceeded their cycle limit of {driver.max_cycle_work_minutes / 60} hours.",
                'violation_time': current_time,
            })

        # Check sleeper berth provision
        if driver.sleeper_berth_time < 480:
            violations.append({
                'violation_type': 'Sleeper Berth Provision',
                'violation_description': f"Driver {driver.driver_id} did not meet the sleeper berth requirement.",
                'violation_time': current_time,
            })

    # Store violations
    for violation in violations:
        HOSViolation.objects.create(
            driver=driver,
            violation_type=violation['violation_type'],
            violation_description=violation['violation_description'],
            violation_time=violation['violation_time']
        )

    return violations