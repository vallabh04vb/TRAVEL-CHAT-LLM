import requests
from .config import WEATHER_API_KEY, WEATHER_API_URL

class WeatherAgent:
    @staticmethod
    def get_weather(city: str) -> str:
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        try:
            response = requests.get(WEATHER_API_URL, params=params)
            response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
            data = response.json()
            
            # Parse the response to extract weather data
            weather = data.get("weather", [{}])[0].get("description", "no description available")
            temp = data.get("main", {}).get("temp", "N/A")
            
            return f"The weather in {city} is currently {weather} with a temperature of {temp}°C."
        except requests.exceptions.RequestException as e:
            # Handle HTTP errors
            return f"Unable to retrieve weather data at the moment. Error: {e}"
        except KeyError:
            # Handle JSON structure errors if keys are missing
            return "Weather data is not available in the expected format."

