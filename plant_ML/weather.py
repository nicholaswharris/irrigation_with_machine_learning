"""
This application retrieves a One-Call weather request. The information is then returned in a single variable.

It utilizes two API Keys (which have been removed for privacy below).
The amount of calls this devices needs to make barely exceeds the number allowed in a day. By adding a second key, it also
allows for more testing (if needed) while avoiding hitting the daily limit.
"""

import pytz as pytz
import requests


def url_to_api(API_KEY):
    # One-Call API URL
    BASE_URL = "https://api.openweathermap.org/data/2.5/onecall?lat="
    # Latitude and Longitude for Asheville
    LAT = "{:.4f}".format(35.6009)
    LON = "{:.3f}".format(-82.554)
    # Convert to 'Merica, baby!
    UNITS = "imperial"
    # Store URL
    ONECALL_URL = BASE_URL + LAT + "&lon=" + LON + "&appid=" + API_KEY + "&units=" + UNITS
    return ONECALL_URL


def hourlyForecast():
    # API Token
    API_KEY1 = "INSERT YOUR FIRST API KEY HERE"
    API_KEY2 = "INSERT YOUR SECOND API KEY HERE"

    # HTTP request
    response = requests.get(url_to_api(API_KEY1))
    data = []

    # Checking the status code of request with first token
    if response.status_code == 200:
        # Getting data in JSON format
        data = response.json()
        return data

    # If first token fails, try the second one
    response = requests.get(url_to_api(API_KEY2))
    if response.status_code == 200:
        data = response.json()
        return data

    # Return API data or empty (if both tokens fail)
    return data
