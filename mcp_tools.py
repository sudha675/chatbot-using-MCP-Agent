# mcp_tools.py
import re
import pytz
import base64
import requests
from PIL import Image
import io
from datetime import datetime

# Import weather client
try:
    from mcp_weather import MCPWeatherClient
    WEATHER_AVAILABLE = True
    print("✅ Real WeatherAPI module loaded successfully")
except ImportError:
    WEATHER_AVAILABLE = False
    print("❌ Weather module not available")
    
    class MCPWeatherClient:
        def __init__(self, api_key):
            self.api_key = api_key
        
        def get_current_weather(self, location):
            return {
                'success': False, 
                'error': 'Weather module not available.'
            }

# Import news functions
try:
    from live_news import fetch_live_news, fetch_recent_event_info, fetch_breaking_news
    NEWS_AVAILABLE = True
    print("✅ Live News module loaded successfully")
except ImportError as e:
    NEWS_AVAILABLE = False
    print(f"❌ News module import error: {e}")
    
    def fetch_live_news(query: str) -> str:
        return "News search temporarily unavailable."
    
    def fetch_recent_event_info(query: str) -> str:
        return fetch_live_news(query)
    
    def fetch_breaking_news() -> str:
        return "Breaking news temporarily unavailable."

class MCPClient:
    """MCP Client with REAL WeatherAPI and LIVE News"""
    
    def __init__(self):
        self.weather_client = MCPWeatherClient()  # Uses your WeatherAPI key
        
        self.tools = {
            'calculator': self.calculate,
            'time': self.get_current_time,
            'weather': self.get_weather,
            'news_search': self.news_search,
            'breaking_news': self.get_breaking_news,
            'web_search': self.web_search,
            'analyze_image': self.analyze_image,
            'unit_converter': self.convert_units,
        }
        
        print("🔧 MCP Client initialized with REAL WeatherAPI")

    def call_tool(self, tool_name, parameters):
        """Execute tool calls with proper error handling"""
        try:
            if tool_name in self.tools:
                print(f"🔧 Executing: {tool_name} with {parameters}")
                result = self.tools[tool_name](**parameters)
                return result
            else:
                return f"Tool '{tool_name}' not found."
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def get_weather(self, location="Chennai"):
        """Get REAL weather information from WeatherAPI.com"""
        try:
            if not location or location.strip() == "":
                location = "Chennai"
                
            print(f"🌤️ Fetching REAL weather for: {location}")
            weather_data = self.weather_client.get_current_weather(location)
            
            if weather_data['success']:
                data = weather_data
                return f"""🌤️ **REAL-TIME WEATHER: {data['location']}, {data['country']}** {data['emoji']}

🌡️ **Temperature**: {data['temperature_c']}°C ({data['temperature_f']}°F)
🤔 **Feels like**: {data['feels_like_c']}°C ({data['feels_like_f']}°F)
📝 **Condition**: {data['condition']}
💧 **Humidity**: {data['humidity']}%
🌬️ **Wind**: {data['wind_speed_kph']} km/h {data['wind_direction']}
📊 **Pressure**: {data['pressure_mb']} mb
👁️ **Visibility**: {data['visibility_km']} km
☁️ **Cloud Cover**: {data['cloud_cover']}%
🔆 **UV Index**: {data['uv_index']}
🕒 **Local Time**: {data['local_time']}

🔍 **Source**: {data['source']}"""
            
            else:
                error_msg = weather_data.get('error', 'Unknown error')
                return f"""❌ **Weather Service Error**

{error_msg}

🔧 **Quick Fix**:
1. Visit https://www.weatherapi.com/my/
2. Check your API key status
3. Ensure you have available API calls
4. Verify your API key in mcp_weather.py"""
                    
        except Exception as e:
            return f"❌ Weather service error: {str(e)}"

    def news_search(self, query):
        """Search for LIVE news"""
        try:
            if not query or query.strip() == "":
                query = "latest news"
            
            print(f"📰 Searching LIVE news for: {query}")
            
            if not NEWS_AVAILABLE:
                return "❌ News service unavailable."
            
            news_results = fetch_live_news(query)
            return news_results
            
        except Exception as e:
            return f"❌ News search error: {str(e)}"

    def get_breaking_news(self):
        """Get LIVE breaking news"""
        try:
            print("🚨 Fetching breaking news...")
            
            if not NEWS_AVAILABLE:
                return "❌ Breaking news unavailable."
            
            breaking_news = fetch_breaking_news()
            return breaking_news
            
        except Exception as e:
            return f"❌ Breaking news error: {str(e)}"

    def calculate(self, expression):
        """Basic calculator tool"""
        try:
            expression = expression.strip()
            if not expression:
                return "Please provide a mathematical expression."
            
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return "Only basic math operations allowed."
            
            result = eval(expression)
            return f"🧮 Calculation: {expression} = {result}"
            
        except ZeroDivisionError:
            return "❌ Math error: Division by zero"
        except Exception as e:
            return f"❌ Invalid expression: {str(e)}"

    def get_current_time(self, location="local"):
        """Enhanced time tool"""
        try:
            timezone_map = {
                "india": "Asia/Kolkata", "usa": "America/New_York", 
                "london": "Europe/London", "tokyo": "Asia/Tokyo",
                "local": "local"
            }
            
            location_lower = location.lower().strip()
            timezone = timezone_map.get(location_lower, "local")
            
            if timezone == "local":
                now = datetime.now()
                time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                return f"🕒 Local Time: {time_str}"
            else:
                try:
                    tz = pytz.timezone(timezone)
                    now = datetime.now(tz)
                    time_str = now.strftime('%Y-%m-%d %H:%M:%S %Z')
                    return f"🕒 Time in {location.title()}: {time_str}"
                except:
                    now = datetime.now()
                    time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                    return f"🕒 Time in {location.title()}: {time_str} (approx)"
                    
        except Exception as e:
            return f"❌ Error getting time: {str(e)}"

    def web_search(self, query):
        """General web search"""
        return self.news_search(query)

    def convert_units(self, value, from_unit, to_unit):
        """Unit converter tool"""
        try:
            value_float = float(value)
            
            conversions = {
                ('c', 'f'): lambda x: (x * 9/5) + 32,
                ('f', 'c'): lambda x: (x - 32) * 5/9,
                ('km', 'miles'): lambda x: x * 0.621371,
                ('miles', 'km'): lambda x: x * 1.60934,
                ('kg', 'pounds'): lambda x: x * 2.20462,
                ('pounds', 'kg'): lambda x: x * 0.453592,
            }
            
            from_unit_lower = from_unit.lower().replace(' ', '')
            to_unit_lower = to_unit.lower().replace(' ', '')
            
            key = (from_unit_lower, to_unit_lower)
            
            if key in conversions:
                result = conversions[key](value_float)
                return f"📐 Conversion: {value} {from_unit} = {result:.2f} {to_unit}"
            else:
                return "❌ Conversion not supported. Try: celsius/fahrenheit, km/miles, kg/pounds"
                
        except Exception as e:
            return f"❌ Conversion error: {str(e)}"

    def analyze_image(self, image_data=None):
        """Simple image analysis"""
        try:
            if not image_data:
                return "❌ No image data provided."
            
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            width, height = image.size
            format_type = image.format if image.format else "Unknown"
            mode = image.mode
            
            return f"""🖼️ Image Analysis

📏 Dimensions: {width} x {height} pixels
🎨 Color Mode: {mode}
📄 Format: {format_type}

💡 Upload with a question for detailed analysis."""
            
        except Exception as e:
            return f"❌ Image analysis error: {str(e)}"

# Test function
def test_real_services():
    """Test REAL weather and news services"""
    client = MCPClient()
    
    print("🧪 TESTING REAL WEATHERAPI & LIVE NEWS\n")
    
    test_cases = [
        ('weather', {'location': 'Chennai'}, "Real Chennai Weather"),
        ('weather', {'location': 'Mumbai'}, "Real Mumbai Weather"),
        ('news_search', {'query': 'technology'}, "Live Tech News"),
        ('breaking_news', {}, "Breaking News"),
    ]
    
    for tool_name, params, description in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing: {description}")
        print(f"{'='*70}")
        result = client.call_tool(tool_name, params)
        print(result)
        print(f"{'='*70}")

if __name__ == "__main__":
    test_real_services()