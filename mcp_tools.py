import re
import pytz
import base64
import requests
from PIL import Image
import io
from datetime import datetime

try:
    from mcp_weather import MCPWeatherClient
    WEATHER_AVAILABLE = True
except ImportError:
    WEATHER_AVAILABLE = False
    class MCPWeatherClient:
        def get_current_weather(self, location):
            return {'success': False, 'error': 'Weather module not available.'}

try:
    from live_news import fetch_live_news, fetch_breaking_news
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    def fetch_live_news(q): return "News service unavailable."
    def fetch_breaking_news(): return "Breaking news unavailable."

class MCPClient:
    """MCP Client with real WeatherAPI and live news."""
    def __init__(self):
        self.weather_client = MCPWeatherClient()
        self.tools = {
            'calculator': self.calculate,
            'time': self.get_current_time,
            'weather': self.get_weather,
            'news_search': self.news_search,
            'web_search': self.web_search,
            'unit_converter': self.convert_units,
        }

    def call_tool(self, tool_name, parameters):
        try:
            if tool_name in self.tools:
                return self.tools[tool_name](**parameters)
            return f"Tool '{tool_name}' not found."
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def get_weather(self, location="Chennai"):
        try:
            data = self.weather_client.get_current_weather(location)
            if data['success']:
                return f"""🌤️ **REAL-TIME WEATHER: {data['location']}, {data['country']}** {data['emoji']}
🌡️ Temperature: {data['temperature_c']}°C ({data['temperature_f']}°F)
🤔 Feels like: {data['feels_like_c']}°C ({data['feels_like_f']}°F)
📝 Condition: {data['condition']}
💧 Humidity: {data['humidity']}%
🌬️ Wind: {data['wind_speed_kph']} km/h {data['wind_direction']}
📊 Pressure: {data['pressure_mb']} mb
👁️ Visibility: {data['visibility_km']} km
☁️ Cloud Cover: {data['cloud_cover']}%
🔆 UV Index: {data['uv_index']}
🕒 Local Time: {data['local_time']}"""
            else:
                return f"Weather error: {data.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Weather service error: {str(e)}"

    def news_search(self, query):
        if not NEWS_AVAILABLE:
            return "News service unavailable."
        return fetch_live_news(query)

    def calculate(self, expression):
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"🧮 {expression} = {result}"
        except Exception as e:
            return f"Invalid expression: {str(e)}"

    def get_current_time(self, location="local"):
        tz_map = {"india": "Asia/Kolkata", "usa": "America/New_York", "uk": "Europe/London"}
        tz_name = tz_map.get(location.lower(), "local")
        if tz_name == "local":
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return f"🕒 Local Time: {now}"
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
            return f"🕒 Time in {location.title()}: {now}"
        except:
            return f"🕒 Time in {location.title()}: (timezone lookup failed)"

    def web_search(self, query):
        return self.news_search(query)

    def convert_units(self, value, from_unit, to_unit):
        try:
            v = float(value)
            conversions = {
                ('c','f'): lambda x: (x*9/5)+32, ('f','c'): lambda x: (x-32)*5/9,
                ('km','miles'): lambda x: x*0.621371, ('miles','km'): lambda x: x*1.60934,
                ('kg','pounds'): lambda x: x*2.20462, ('pounds','kg'): lambda x: x*0.453592,
            }
            key = (from_unit.lower().replace(' ',''), to_unit.lower().replace(' ',''))
            if key in conversions:
                res = conversions[key](v)
                return f"📐 {value} {from_unit} = {res:.2f} {to_unit}"
            else:
                return "Conversion not supported. Try: celsius/fahrenheit, km/miles, kg/pounds"
        except:
            return "Invalid conversion request."