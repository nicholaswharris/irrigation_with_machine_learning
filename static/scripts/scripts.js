const api = 'bad79916d1735c73875bb6031a34ed31';
window.addEventListener('load', () => {});


# One-Call API URL
BASE_URL = "https://api.openweathermap.org/data/2.5/onecall?lat="
LAT = "{:.4f}".format(35.6009)
LON = "{:.3f}".format(-82.554)
API_KEY = "bad79916d1735c73875bb6031a34ed31"
UNITS = "imperial"
ONECALL_URL = BASE_URL + LAT + "&lon=" + LON + "&appid=" + API_KEY + "&units=" + UNITS

# Used to convert UTC to EST
est = pytz.timezone('US/Eastern')
utc = pytz.utc
timefmt = '%Y-%m-%d %H:%M:%S %Z'
