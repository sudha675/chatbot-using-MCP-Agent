import requests

class MCPWeatherClient:
    """MCP Client for weather data using WeatherAPI.com"""
    
    def __init__(self, api_key=None):
        # Use provided API key or try to get from environment
        self.api_key = "39d05c8526d54160a1a51827250410"  # REPLACE THIS WITH YOUR ACTUAL KEY
        self.base_url = "http://api.weatherapi.com/v1"
        
        if not self.api_key or self.api_key == "YOUR_WEATHERAPI_KEY_HERE":
            print("❌ WEATHER API KEY NOT SET!")
            print("🔑 Please get a free API key from: https://www.weatherapi.com/")
            print("💡 Then replace 'YOUR_WEATHERAPI_KEY_HERE' with your actual key")
    
    def get_current_weather(self, location="Kolkata"):
        """Get current weather data from WeatherAPI.com"""
        try:
            # Check if API key is set
            if not self.api_key or self.api_key == "YOUR_WEATHERAPI_KEY_HERE":
                return {
                    'success': False,
                    'error': 'WeatherAPI key not configured. Please get a free API key from https://www.weatherapi.com/ and replace "YOUR_WEATHERAPI_KEY_HERE" in mcp_weather.py'
                }
            
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': location,
                'aqi': 'no'
            }
            
            print(f"🌍 Fetching weather for: {location}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant data
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
                    'local_time': location_info['localtime'],
                    'emoji': self._get_weather_emoji(current['condition']['text'])
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Invalid WeatherAPI key. Please check your API key at https://www.weatherapi.com/'
                }
            elif response.status_code == 400:
                return {
                    'success': False,
                    'error': f'Invalid location: {location}. Please check the spelling.'
                }
            else:
                return {
                    'success': False,
                    'error': f'Weather API error: {response.status_code} - {response.text}'
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
        """Get emoji for weather condition"""
        condition_lower = condition.lower()
        
        if 'sunny' in condition_lower or 'clear' in condition_lower:
            return '☀️'
        elif 'partly cloudy' in condition_lower:
            return '⛅'
        elif 'cloud' in condition_lower:
            return '☁️'
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return '🌧️'
        elif 'snow' in condition_lower:
            return '❄️'
        elif 'storm' in condition_lower or 'thunder' in condition_lower:
            return '⛈️'
        elif 'mist' in condition_lower or 'fog' in condition_lower:
            return '🌫️'
        elif 'wind' in condition_lower:
            return '💨'
        else:
            return '🌤️'

# Test function
def test_weather():
    """Test weather functionality"""
    client = MCPWeatherClient()
    
    test_locations = ["Kolkata", "London", "New York", "Tokyo"]
    
    for location in test_locations:
        print(f"\n🌍 Testing weather for: {location}")
        result = client.get_current_weather(location)
        
        if result['success']:
            data = result
            print(f"✅ Weather in {data['location']}, {data['country']}: {data['temperature_c']}°C {data['emoji']}")
            print(f"   Condition: {data['condition']}")
            print(f"   Humidity: {data['humidity']}%")
            print(f"   Wind: {data['wind_speed_kph']} km/h")
        else:
            print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    print("🧪 Testing Weather Client...")
    test_weather()