import requests
import json
from typing import Dict, Any, Optional
from pathlib import Path
from django.conf import settings

class PrologsAPIClient:
    PROLOGS_TOKEN_URL = "https://identity-stage.prologs.us/connect/token"
    BASE_URL = "https://publicapi-stage.prologs.us"

    def __init__(self):
        self.access_token = self.get_access_token()
        self.headers = self._create_headers()

    def _create_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_access_token(self, refresh: bool = False) -> str:
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
            tokenObj = self._request_new_access_token()
            with open(token_file,'w') as fp:
                json.dump(tokenObj,fp,indent=4)
            
        return tokenObj['access_token'] if 'access_token' in tokenObj else None

    def _request_new_access_token(self) -> str:
        """
        Obtain an access token from the ProLogs API.
        """

        data = {
            'grant_type': 'client_credentials',
            'client_id': settings.PROLOG_CLIENT_ID,
            'client_secret': settings.PROLOG_CLIENT_SECRET
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(self.PROLOGS_TOKEN_URL, data=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to obtain access token: {response.text}")

    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Make a GET request to the given endpoint and handle authorization.
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 401:
            self.access_token = self.get_access_token(refresh=True)
            self.headers = self._create_headers()
            response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()

        print(f"Failed to fetch data from {url}: {response.status_code}")
        return None

    def get_trucks(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data about trucks.
        """
        return self._make_request("/api/v1/trucks")

    def get_drivers(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data about drivers.
        """
        return self._make_request("/api/v1/drivers")
