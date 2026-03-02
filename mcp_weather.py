import requests
import os

class MCPWeatherClient:
    """MCP Client for REAL weather data using WeatherAPI.com"""
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('WEATHER_API_KEY') or "d529b74e696d40dc945102356251210"
        self.base_url = "http://api.weatherapi.com/v1"

    def get_current_weather(self, location="Chennai"):
        try:
            url = f"{self.base_url}/current.json"
            params = {'key': self.api_key, 'q': location, 'aqi': 'no'}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                loc = data['location']
                cur = data['current']
                return {
                    'success': True,
                    'location': loc['name'],
                    'country': loc['country'],
                    'temperature_c': cur['temp_c'],
                    'temperature_f': cur['temp_f'],
                    'condition': cur['condition']['text'],
                    'humidity': cur['humidity'],
                    'wind_speed_kph': cur['wind_kph'],
                    'wind_direction': cur['wind_dir'],
                    'pressure_mb': cur['pressure_mb'],
                    'visibility_km': cur['vis_km'],
                    'feels_like_c': cur['feelslike_c'],
                    'feels_like_f': cur['feelslike_f'],
                    'uv_index': cur['uv'],
                    'cloud_cover': cur['cloud'],
                    'local_time': loc['localtime'],
                    'emoji': self._get_weather_emoji(cur['condition']['text']),
                }
            else:
                return {'success': False, 'error': f"WeatherAPI error {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_weather_emoji(self, condition):
        cond = condition.lower()
        if 'sunny' in cond or 'clear' in cond:
            return '☀️'
        if 'partly cloudy' in cond:
            return '⛅'
        if 'cloudy' in cond or 'overcast' in cond:
            return '☁️'
        if 'rain' in cond:
            return '🌧️'
        if 'snow' in cond:
            return '❄️'
        if 'thunder' in cond:
            return '⛈️'
        if 'mist' in cond or 'fog' in cond:
            return '🌫️'
        return '🌤️'