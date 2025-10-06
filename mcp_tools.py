import re
import pytz
import base64
import requests
from PIL import Image
import io
from datetime import datetime

# Import weather client with error handling
try:
    from mcp_weather import MCPWeatherClient
    WEATHER_AVAILABLE = True
    print("✅ Weather module loaded successfully")
except ImportError:
    WEATHER_AVAILABLE = False
    print("⚠️ Weather module not available. Weather features will be limited.")
    
    class MCPWeatherClient:
        def __init__(self, api_key):
            self.api_key = api_key
        
        def get_current_weather(self, location):
            return {
                'success': False, 
                'error': 'Weather module not available. Please install required dependencies.'
            }

# Import news functions with error handling
try:
    from live_news import fetch_live_news, fetch_recent_event_info, fetch_breaking_news
    NEWS_AVAILABLE = True
    print("✅ News module loaded successfully")
except ImportError as e:
    NEWS_AVAILABLE = False
    print(f"❌ News module import error: {e}")
    
    # Fallback functions
    def fetch_live_news(query: str) -> str:
        return f"❌ News search temporarily unavailable. Please check if live_news.py exists and has proper imports."
    
    def fetch_recent_event_info(query: str) -> str:
        return fetch_live_news(query)
    
    def fetch_breaking_news() -> str:
        return "❌ Breaking news temporarily unavailable."

class MCPClient:
    """MCP Client with weather, news, calculator, and image analysis"""
    
    def __init__(self):
        # Initialize with demo API key - replace with your actual keys
        self.weather_client = MCPWeatherClient("your_weatherapi_key_here")
        
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
        
        print("🔧 MCP Client initialized with tools:", list(self.tools.keys()))
    
    def call_tool(self, tool_name, parameters):
        """Execute tool calls with proper error handling"""
        try:
            if tool_name in self.tools:
                print(f"🔧 Executing tool: {tool_name} with params: {parameters}")
                result = self.tools[tool_name](**parameters)
                print(f"✅ Tool {tool_name} executed successfully")
                return result
            else:
                available_tools = ", ".join([f"'{tool}'" for tool in self.tools.keys()])
                return f"❌ Tool '{tool_name}' not found. Available tools: {available_tools}"
        except Exception as e:
            return f"❌ Error executing tool {tool_name}: {str(e)}"
    
    def calculate(self, expression):
        """Basic calculator tool"""
        try:
            expression = expression.strip()
            if not expression:
                return "❌ Please provide a mathematical expression to calculate."
            
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return "❌ Only basic math operations allowed (numbers, +, -, *, /, ., ())"
            
            if len(expression) > 100:
                return "❌ Expression too long. Please use simpler calculations."
            
            result = eval(expression)
            return f"🔢 **Calculation Result**: `{expression}` = **{result}**"
            
        except ZeroDivisionError:
            return "❌ Math error: Division by zero"
        except SyntaxError:
            return "❌ Invalid mathematical expression syntax"
        except Exception as e:
            return f"❌ Invalid mathematical expression: {str(e)}"
    
    def get_current_time(self, location="local"):
        """Enhanced time tool with timezone support"""
        try:
            timezone_map = {
                "india": "Asia/Kolkata", "usa": "America/New_York", "us": "America/New_York",
                "new york": "America/New_York", "uk": "Europe/London", "london": "Europe/London",
                "tokyo": "Asia/Tokyo", "japan": "Asia/Tokyo", "china": "Asia/Shanghai",
                "germany": "Europe/Berlin", "france": "Europe/Paris", "australia": "Australia/Sydney",
                "canada": "America/Toronto", "local": "local"
            }
            
            location_lower = location.lower().strip()
            timezone = timezone_map.get(location_lower, "local")
            
            if timezone == "local":
                now = datetime.now()
                time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                day_str = now.strftime('%A')
                return f"🕒 **Current Local Time**: {time_str}\n📅 **Day**: {day_str}"
            else:
                try:
                    tz = pytz.timezone(timezone)
                    now = datetime.now(tz)
                    time_str = now.strftime('%Y-%m-%d %H:%M:%S %Z%z')
                    day_str = now.strftime('%A')
                    return f"🕒 **Current Time in {location.title()}**: {time_str}\n📅 **Day**: {day_str}"
                except:
                    now = datetime.now()
                    time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                    return f"🕒 **Current Time in {location.title()}**: {time_str} (approximate)"
                    
        except Exception as e:
            return f"❌ Error getting time: {str(e)}"
    
    def get_weather(self, location="New Delhi"):
        """Get real-time weather"""
        try:
            if not location or location.strip() == "":
                location = "New Delhi"
                
            print(f"🌍 Fetching weather for: {location}")
            weather_data = self.weather_client.get_current_weather(location)
            
            if weather_data['success']:
                data = weather_data
                return f"""🌍 **Current Weather in {data['location']}, {data['country']}** {data['emoji']}

🌡️ **Temperature**: {data['temperature_c']:.1f}°C ({data['temperature_f']:.1f}°F)
📝 **Condition**: {data['condition']}
💧 **Humidity**: {data['humidity']}%
🌬️ **Wind Speed**: {data['wind_speed_kph']} km/h
💨 **Wind Direction**: {data['wind_direction']}
🌫️ **Pressure**: {data['pressure_mb']} mb
👁️ **Visibility**: {data['visibility_km']} km
🕒 **Local Time**: {data['local_time']}"""
            else:
                error_msg = weather_data.get('error', 'Unknown error')
                return f"❌ **Weather Error**: {error_msg}"
                
        except Exception as e:
            return f"❌ **Weather Tool Error**: {str(e)}"
    
    def news_search(self, query):
        """Search for recent news and events"""
        try:
            if not query or query.strip() == "":
                query = "latest news"
            
            print(f"🔍 Searching news for: {query}")
            
            if not NEWS_AVAILABLE:
                return "❌ News search is currently unavailable. Please check if live_news.py exists and all dependencies are installed."
            
            news_results = fetch_live_news(query)
            return news_results
            
        except Exception as e:
            return f"❌ **News Search Error**: {str(e)}"
    
    def get_breaking_news(self):
        """Get breaking news headlines"""
        try:
            print("🚨 Fetching breaking news...")
            
            if not NEWS_AVAILABLE:
                return "❌ Breaking news is currently unavailable."
            
            breaking_news = fetch_breaking_news()
            return breaking_news
            
        except Exception as e:
            return f"❌ **Breaking News Error**: {str(e)}"
    
    def web_search(self, query):
        """General web search"""
        try:
            if not query or query.strip() == "":
                return "❌ Please provide a search query."
            
            print(f"🌐 Web searching for: {query}")
            
            if not NEWS_AVAILABLE:
                return "❌ Web search is currently unavailable."
            
            web_results = fetch_live_news(query)
            if web_results and "❌" not in web_results and "No results" not in web_results:
                return f"🌐 **Web Search Results for '{query}'**\n\n{web_results}"
            else:
                return f"❌ No web results found for '{query}'."
                
        except Exception as e:
            return f"❌ **Web Search Error**: {str(e)}"
    
    def convert_units(self, value, from_unit, to_unit):
        """Unit converter tool"""
        try:
            if not value or not from_unit or not to_unit:
                return "❌ Please provide value, from_unit, and to_unit parameters."
            
            try:
                value_float = float(value)
            except ValueError:
                return "❌ Please provide a valid numeric value for conversion."
            
            conversions = {
                ('c', 'f'): lambda x: (x * 9/5) + 32, ('celsius', 'fahrenheit'): lambda x: (x * 9/5) + 32,
                ('f', 'c'): lambda x: (x - 32) * 5/9, ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
                ('km', 'miles'): lambda x: x * 0.621371, ('kilometers', 'miles'): lambda x: x * 0.621371,
                ('miles', 'km'): lambda x: x * 1.60934, ('miles', 'kilometers'): lambda x: x * 1.60934,
                ('kg', 'pounds'): lambda x: x * 2.20462, ('kilograms', 'pounds'): lambda x: x * 2.20462,
                ('pounds', 'kg'): lambda x: x * 0.453592, ('pounds', 'kilograms'): lambda x: x * 0.453592,
            }
            
            from_unit_lower = from_unit.lower().replace(' ', '').replace('-', '')
            to_unit_lower = to_unit.lower().replace(' ', '').replace('-', '')
            
            key = (from_unit_lower, to_unit_lower)
            
            if key in conversions:
                result = conversions[key](value_float)
                return f"📐 **Unit Conversion**: {value} {from_unit} = **{result:.4f} {to_unit}**"
            else:
                supported_units = [
                    "• Temperature: celsius ↔ fahrenheit",
                    "• Distance: km ↔ miles", 
                    "• Weight: kg ↔ pounds",
                ]
                return f"❌ Conversion from '{from_unit}' to '{to_unit}' not supported.\n\n✅ **Supported conversions**:\n" + "\n".join(supported_units)
                
        except Exception as e:
            return f"❌ Error converting units: {str(e)}"
    
    def analyze_image(self, image_data=None):
        """Simple image analysis - basic info"""
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
            file_size_kb = len(image_bytes) / 1024
            
            return f"""🖼️ **Image Analysis**

📏 **Dimensions**: {width} × {height} pixels
🎨 **Color Mode**: {mode}
📄 **Format**: {format_type}
💾 **File Size**: {file_size_kb:.1f} KB

💡 Upload this image with a question for detailed visual analysis."""
            
        except Exception as e:
            return f"❌ Error analyzing image: {str(e)}"

# Test function
def test_mcp_tools():
    """Test all MCP tools"""
    client = MCPClient()
    
    test_cases = [
        ('calculator', {'expression': '15 * 25 + 8'}, "Basic calculation"),
        ('time', {'location': 'london'}, "Time in London"),
        ('weather', {'location': 'New Delhi'}, "Weather in New Delhi"),
        ('news_search', {'query': 'technology'}, "Technology news"),
        ('breaking_news', {}, "Breaking news"),
    ]
    
    print("🧪 Testing MCP Tools...")
    print("=" * 60)
    
    for tool_name, params, description in test_cases:
        print(f"\n🔧 Testing {tool_name} - {description}...")
        result = client.call_tool(tool_name, params)
        print(f"Result: {result[:200]}{'...' if len(result) > 200 else ''}")
        print("-" * 50)

if __name__ == "__main__":
    test_mcp_tools()