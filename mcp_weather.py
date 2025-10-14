# mcp_weather.py
import requests
import os

class MCPWeatherClient:
    """MCP Client for REAL weather data using WeatherAPI.com"""
    
    def __init__(self, api_key=None):
        # Get API key from parameter, environment variable, or use default
        self.api_key = api_key or os.getenv('WEATHER_API_KEY') or "d529b74e696d40dc945102356251210"
        self.base_url = "http://api.weatherapi.com/v1"
        self._validate_api_key()
    
    def _validate_api_key(self):
        """Validate the API key"""
        if not self.api_key or self.api_key == "YOUR_WEATHERAPI_KEY_HERE":
            print("❌ WEATHER API KEY NOT CONFIGURED!")
            print("🔑 Please get a free API key from: https://www.weatherapi.com/")
            print("💡 Then set it in mcp_weather.py or as environment variable: WEATHER_API_KEY=your_key")
            return False
        
        print(f"✅ WeatherAPI key loaded: {self.api_key[:8]}...{self.api_key[-4:]}")
        return True

    def get_current_weather(self, location="Chennai"):
        """Get REAL current weather data from WeatherAPI.com"""
        try:
            # Check if API key is configured
            if not self.api_key or self.api_key == "YOUR_WEATHERAPI_KEY_HERE":
                return {
                    'success': False,
                    'error': 'WeatherAPI key not configured. Please get a free API key from https://www.weatherapi.com/ and update mcp_weather.py'
                }
            
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': location,
                'aqi': 'no'
            }
            
            print(f"🌤️ Fetching REAL weather for: {location}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract data from WeatherAPI response
                location_info = data['location']
                current = data['current']
                
                return {
                    'success': True,
                    'location': location_info['name'],
                    'country': location_info['country'],
                    'temperature_c': current['temp_c'],
                    'temperature_f': current['temp_f'],
                    'condition': current['condition']['text'],
                    'humidity': current['humidity'],
                    'wind_speed_kph': current['wind_kph'],
                    'wind_direction': current['wind_dir'],
                    'pressure_mb': current['pressure_mb'],
                    'visibility_km': current['vis_km'],
                    'feels_like_c': current['feelslike_c'],
                    'feels_like_f': current['feelslike_f'],
                    'uv_index': current['uv'],
                    'cloud_cover': current['cloud'],
                    'local_time': location_info['localtime'],
                    'emoji': self._get_weather_emoji(current['condition']['text']),
                    'source': 'WeatherAPI.com - Real Data'
                }
                
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Invalid WeatherAPI key. Please check your API key at https://www.weatherapi.com/my/'
                }
            elif response.status_code == 400:
                return {
                    'success': False,
                    'error': f'Invalid location: "{location}". Please check the spelling.'
                }
            elif response.status_code == 403:
                return {
                    'success': False,
                    'error': 'API key disabled or exceeded limits. Check your account at https://www.weatherapi.com/my/'
                }
            else:
                error_msg = f"WeatherAPI error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    pass
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Network error: Cannot connect to weather service. Check your internet connection.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Weather service timeout. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to fetch weather: {str(e)}'
            }
    
    def _get_weather_emoji(self, condition):
        """Get appropriate emoji for weather condition"""
        condition_lower = condition.lower()
        
        emoji_map = {
            'sunny': '☀️',
            'clear': '☀️',
            'partly cloudy': '⛅',
            'cloudy': '☁️',
            'overcast': '☁️',
            'mist': '🌫️',
            'fog': '🌫️',
            'light rain': '🌦️',
            'moderate rain': '🌧️',
            'heavy rain': '🌧️',
            'rain': '🌧️',
            'light snow': '🌨️',
            'snow': '❄️',
            'thunder': '⛈️',
            'thunderstorm': '⛈️',
            'drizzle': '💧',
            'windy': '💨'
        }
        
        for key, emoji in emoji_map.items():
            if key in condition_lower:
                return emoji
        
        return '🌤️'  # Default emoji

    def get_weather_forecast(self, location="Chennai", days=3):
        """Get weather forecast (optional feature)"""
        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': location,
                'days': days,
                'aqi': 'no',
                'alerts': 'no'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                forecast_days = data['forecast']['forecastday']
                
                forecast_info = []
                for day in forecast_days:
                    date = day['date']
                    condition = day['day']['condition']['text']
                    max_temp = day['day']['maxtemp_c']
                    min_temp = day['day']['mintemp_c']
                    
                    forecast_info.append({
                        'date': date,
                        'condition': condition,
                        'max_temp': max_temp,
                        'min_temp': min_temp,
                        'emoji': self._get_weather_emoji(condition)
                    })
                
                return {
                    'success': True,
                    'location': data['location']['name'],
                    'country': data['location']['country'],
                    'forecast': forecast_info
                }
            else:
                return {
                    'success': False,
                    'error': f'Forecast error: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Forecast service error: {str(e)}'
            }

# Test function with REAL API
def test_real_weather():
    """Test the REAL weather functionality with WeatherAPI"""
    client = MCPWeatherClient()
    
    print("🌤️ TESTING REAL WEATHERAPI INTEGRATION\n")
    
    test_locations = ["Chennai", "Mumbai", "Delhi", "London", "New York", "Tokyo"]
    
    for location in test_locations:
        print(f"\n{'='*70}")
        print(f"📍 Testing REAL weather for: {location}")
        print(f"{'='*70}")
        
        result = client.get_current_weather(location)
        
        if result['success']:
            data = result
            print(f"✅ REAL-TIME WEATHER DATA")
            print(f"📍 {data['location']}, {data['country']} {data['emoji']}")
            print(f"🌡️ Temperature: {data['temperature_c']}°C ({data['temperature_f']}°F)")
            print(f"🤔 Feels like: {data['feels_like_c']}°C ({data['feels_like_f']}°F)")
            print(f"📝 Condition: {data['condition']}")
            print(f"💧 Humidity: {data['humidity']}%")
            print(f"🌬️ Wind: {data['wind_speed_kph']} km/h {data['wind_direction']}")
            print(f"📊 Pressure: {data['pressure_mb']} mb")
            print(f"👁️ Visibility: {data['visibility_km']} km")
            print(f"☁️ Cloud Cover: {data['cloud_cover']}%")
            print(f"🔆 UV Index: {data['uv_index']}")
            print(f"🕒 Local Time: {data['local_time']}")
            print(f"🔍 Source: {data['source']}")
        else:
            print(f"❌ ERROR: {result['error']}")
            print(f"💡 Solution: Check your API key at https://www.weatherapi.com/my/")
        
        print(f"{'='*70}")

def test_api_key_status():
    """Test if the API key is working"""
    client = MCPWeatherClient()
    
    print("\n🔑 TESTING API KEY STATUS")
    print("="*50)
    
    # Test with a simple location
    result = client.get_current_weather("London")
    
    if result['success']:
        print("✅ API KEY IS WORKING! Real weather data is available.")
        print(f"📍 First test successful for: {result['location']}")
        print(f"🌡️ Current temp: {result['temperature_c']}°C")
    else:
        print("❌ API KEY ISSUE DETECTED")
        print(f"Error: {result['error']}")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Visit: https://www.weatherapi.com/my/")
        print("2. Check if your API key is active")
        print("3. Copy your API key from the dashboard")
        print("4. Replace the key in mcp_weather.py")
        print("5. Or set environment variable: WEATHER_API_KEY=your_actual_key")

if __name__ == "__main__":
    test_api_key_status()
    test_real_weather()