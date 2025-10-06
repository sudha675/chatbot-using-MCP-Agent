from flask import Flask, render_template, request, jsonify
import subprocess
import json
import uuid
import logging
import re
import requests
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'dev-key-for-chatbot-session'

# WeatherAPI.com Configuration - GET YOUR FREE API KEY FROM https://www.weatherapi.com/my/
WEATHERAPI_API_KEY = "YOUR_WEATHERAPI_KEY_HERE"  # Replace with your actual key
WEATHERAPI_BASE_URL = "http://api.weatherapi.com/v1"

class OllamaChatbot:
    def __init__(self, model_name="gemma3:1b"):
        self.model_name = model_name
    
    def send_message(self, message, system_prompt=None):
        """Send a message to Ollama with optional system prompt"""
        try:
            if system_prompt:
                full_message = f"System: {system_prompt}\n\nUser: {message}\nAssistant:"
            else:
                full_message = message
            
            cmd = ["ollama", "run", self.model_name, full_message]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                return response
            else:
                return f"Error: Failed to get response from Ollama"
                
        except subprocess.TimeoutExpired:
            return "Error: Request timed out"
        except Exception as e:
            return f"Error: {str(e)}"

class ContextManager:
    """Manages conversation context"""
    
    def __init__(self):
        self.conversation_context = []
        self.max_context_length = 6
    
    def update_context(self, user_question, ai_response):
        """Update conversation context"""
        self.conversation_context.append({
            'user': user_question,
            'assistant': ai_response,
            'timestamp': datetime.now()
        })
        
        if len(self.conversation_context) > self.max_context_length:
            self.conversation_context.pop(0)
    
    def get_context_for_llm(self):
        """Get relevant context for the LLM"""
        if not self.conversation_context:
            return ""
        
        context_text = "\n".join([
            f"User: {ctx['user']}\nAssistant: {ctx['assistant']}" 
            for ctx in self.conversation_context
        ])
        return context_text
    
    def clear_context(self):
        """Clear conversation context"""
        self.conversation_context = []

class RealWeatherService:
    """Real weather data service using WeatherAPI.com"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = WEATHERAPI_BASE_URL
        
        # City mapping for common locations
        self.city_mapping = {
            "mumbai": "Mumbai",
            "delhi": "Delhi", 
            "bangalore": "Bangalore",
            "chennai": "Chennai",
            "kolkata": "Kolkata",
            "hyderabad": "Hyderabad",
            "pune": "Pune",
            "ahmedabad": "Ahmedabad",
            "jaipur": "Jaipur",
            "lucknow": "Lucknow",
            "new york": "New York",
            "london": "London",
            "tokyo": "Tokyo",
            "paris": "Paris",
            "dubai": "Dubai",
            "singapore": "Singapore",
            "sydney": "Sydney",
            "toronto": "Toronto",
            "berlin": "Berlin",
            "moscow": "Moscow",
            "los angeles": "Los Angeles",
            "chicago": "Chicago",
            "san francisco": "San Francisco",
            "seoul": "Seoul",
            "beijing": "Beijing",
            "shanghai": "Shanghai",
            "current": "auto:ip"
        }

    def get_weather_emoji(self, condition_code):
        """Convert weather condition to emoji"""
        emoji_map = {
            "Sunny": "☀️", "Clear": "☀️",
            "Partly cloudy": "⛅", "Cloudy": "☁️", "Overcast": "☁️",
            "Patchy rain": "🌦️", "Light rain": "🌦️", "Moderate rain": "🌧️", 
            "Heavy rain": "⛈️", "Thundery outbreaks": "⛈️",
            "Snow": "❄️", "Light snow": "❄️", "Heavy snow": "🌨️",
            "Fog": "🌫️", "Mist": "🌫️", "Haze": "🌫️"
        }
        return emoji_map.get(condition_code, "🌤️")

    def get_current_weather(self, location):
        """Get real-time current weather from WeatherAPI.com"""
        try:
            location_lower = location.lower().strip()
            mapped_location = self.city_mapping.get(location_lower, location)
            
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': mapped_location,
                'aqi': 'no'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract weather information
                location_name = data['location']['name']
                country = data['location']['country']
                region = data['location'].get('region', '')
                
                current = data['current']
                temp_c = current['temp_c']
                temp_f = current['temp_f']
                condition = current['condition']['text']
                condition_emoji = self.get_weather_emoji(condition)
                humidity = current['humidity']
                wind_kph = current['wind_kph']
                wind_mph = current['wind_mph']
                pressure_mb = current['pressure_mb']
                feelslike_c = current['feelslike_c']
                feelslike_f = current['feelslike_f']
                uv_index = current['uv']
                visibility_km = current['vis_km']
                
                # Get local time
                local_time = data['location']['localtime']
                
                return {
                    'success': True,
                    'location': location_name,
                    'country': country,
                    'region': region,
                    'temperature_c': temp_c,
                    'temperature_f': temp_f,
                    'condition': condition,
                    'emoji': condition_emoji,
                    'humidity': humidity,
                    'wind_speed_kph': wind_kph,
                    'wind_speed_mph': wind_mph,
                    'pressure': pressure_mb,
                    'feels_like_c': feelslike_c,
                    'feels_like_f': feelslike_f,
                    'uv_index': uv_index,
                    'visibility_km': visibility_km,
                    'local_time': local_time,
                    'source': 'WeatherAPI.com'
                }
            else:
                error_data = response.json()
                return {
                    'success': False, 
                    'error': f"API Error {response.status_code}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout - please try again'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def get_weather_forecast(self, location, days=3):
        """Get weather forecast from WeatherAPI.com"""
        try:
            location_lower = location.lower().strip()
            mapped_location = self.city_mapping.get(location_lower, location)
            
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': mapped_location,
                'days': days,
                'aqi': 'no',
                'alerts': 'no'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                location_name = data['location']['name']
                country = data['location']['country']
                
                forecast_data = []
                for day in data['forecast']['forecastday']:
                    date = day['date']
                    day_data = day['day']
                    
                    forecast_data.append({
                        'date': date,
                        'max_temp_c': day_data['maxtemp_c'],
                        'min_temp_c': day_data['mintemp_c'],
                        'max_temp_f': day_data['maxtemp_f'],
                        'min_temp_f': day_data['mintemp_f'],
                        'condition': day_data['condition']['text'],
                        'emoji': self.get_weather_emoji(day_data['condition']['text']),
                        'humidity': day_data['avghumidity'],
                        'chance_of_rain': day_data['daily_chance_of_rain'],
                        'uv_index': day_data['uv']
                    })
                
                return {
                    'success': True,
                    'location': location_name,
                    'country': country,
                    'forecast': forecast_data
                }
            else:
                error_data = response.json()
                return {
                    'success': False, 
                    'error': f"API Error {response.status_code}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Forecast error: {str(e)}'}

class MCPClient:
    """MCP Client with real WeatherAPI.com integration"""
    
    def __init__(self):
        self.weather_service = RealWeatherService(WEATHERAPI_API_KEY)
        self.tools = {
            'calculator': self.calculate,
            'time': self.get_current_time,
            'timezone_info': self.get_timezone_info,
            'day_info': self.get_day_info,
            'unit_converter': self.convert_units,
            'weather': self.get_weather,
            'weather_forecast': self.get_weather_forecast
        }
    
    def calculate(self, expression):
        """Basic calculator tool"""
        try:
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"🔢 **Calculation Result**: {expression} = {result}"
            else:
                return "❌ Only basic math operations allowed"
        except:
            return "❌ Invalid mathematical expression"
    
    def get_current_time(self, location="local"):
        """Enhanced time tool with timezone support"""
        try:
            timezone_map = {
                "india": "Asia/Kolkata",
                "usa": "America/New_York", 
                "us": "America/New_York",
                "new york": "America/New_York",
                "london": "Europe/London",
                "uk": "Europe/London",
                "tokyo": "Asia/Tokyo",
                "china": "Asia/Shanghai",
                "germany": "Europe/Berlin",
                "france": "Europe/Paris",
                "australia": "Australia/Sydney",
                "local": "local"
            }
            
            location_lower = location.lower()
            timezone = timezone_map.get(location_lower, "Asia/Kolkata" if "india" in location_lower else "local")
            
            if timezone == "local":
                now = datetime.now()
                time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                return f"🕒 **Current Local Time**: {time_str}"
            else:
                try:
                    tz = pytz.timezone(timezone)
                    now = datetime.now(tz)
                    time_str = now.strftime('%Y-%m-%d %H:%M:%S %Z%z')
                    return f"🕒 **Current Time in {location.title()}**: {time_str}"
                except:
                    now = datetime.now()
                    time_str = now.strftime('%Y-%m-%d %H:%M:%S')
                    return f"🕒 **Current Time in {location.title()}**: {time_str} (approximate)"
                    
        except Exception as e:
            return f"❌ Error getting time: {str(e)}"
    
    def get_day_info(self, location="india"):
        """Get day of the week and date information"""
        try:
            timezone_map = {
                "india": "Asia/Kolkata",
                "usa": "America/New_York",
                "london": "Europe/London",
                "local": "local"
            }
            
            location_lower = location.lower()
            timezone = timezone_map.get(location_lower, "Asia/Kolkata")
            
            if timezone == "local":
                now = datetime.now()
            else:
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
            
            day_name = now.strftime('%A')
            date_str = now.strftime('%B %d, %Y')
            week_number = now.strftime('%U')
            year = now.strftime('%Y')
            
            return f"""📅 **Day Information for {location.title()}**:

• **Today is**: {day_name}
• **Date**: {date_str}
• **Week number**: {week_number}
• **Year**: {year}
• **Timezone**: {tz if timezone != 'local' else 'Local Time'}"""
            
        except Exception as e:
            return f"❌ Error getting day info: {str(e)}"
    
    def get_timezone_info(self, location="india"):
        """Get detailed timezone information"""
        try:
            timezone_info = {
                "india": {
                    "timezone": "IST (India Standard Time)",
                    "utc_offset": "UTC+5:30",
                    "no_daylight_saving": "India does not observe daylight saving time",
                    "covers_entire_country": "Single timezone for entire country",
                    "difference_from_utc": "5 hours 30 minutes ahead of UTC"
                },
                "usa": {
                    "timezone": "Multiple timezones (ET, CT, MT, PT)",
                    "utc_offset": "UTC-5 to UTC-8",
                    "daylight_saving": "Observes DST from March to November",
                    "main_timezones": "Eastern, Central, Mountain, Pacific"
                },
                "london": {
                    "timezone": "GMT/BST (Greenwich Mean Time / British Summer Time)",
                    "utc_offset": "UTC+0 (UTC+1 during BST)",
                    "daylight_saving": "Observes BST from last Sunday in March to last Sunday in October"
                }
            }
            
            location_lower = location.lower()
            info = timezone_info.get(location_lower, timezone_info["india"])
            
            response = f"🌍 **Timezone Information for {location.title()}**:\n\n"
            for key, value in info.items():
                response += f"• **{key.replace('_', ' ').title()}**: {value}\n"
            
            return response
            
        except Exception as e:
            return f"❌ Error getting timezone info: {str(e)}"
    
    def get_weather(self, location="current"):
        """Get real-time weather using WeatherAPI.com"""
        weather_data = self.weather_service.get_current_weather(location)
        
        if weather_data['success']:
            data = weather_data
            
            # UV index interpretation
            uv_level = "Low" if data['uv_index'] <= 2 else "Moderate" if data['uv_index'] <= 5 else "High" if data['uv_index'] <= 7 else "Very High"
            
            return f"""🌍 **Current Weather in {data['location']}, {data['country']}** {data['emoji']}

🌡️ **Temperature**: {data['temperature_c']:.1f}°C ({data['temperature_f']:.1f}°F)
💭 **Feels Like**: {data['feels_like_c']:.1f}°C ({data['feels_like_f']:.1f}°F)
📝 **Condition**: {data['condition']}
💧 **Humidity**: {data['humidity']}%
🌬️ **Wind Speed**: {data['wind_speed_kph']} km/h ({data['wind_speed_mph']} mph)
🌡️ **Pressure**: {data['pressure']} mb
☀️ **UV Index**: {data['uv_index']} ({uv_level})
👁️ **Visibility**: {data['visibility_km']} km
🕒 **Local Time**: {data['local_time']}

🔍 **Source**: {data['source']}"""
        else:
            return f"""❌ **Unable to fetch weather for '{location}'**

**Error**: {weather_data['error']}

💡 **Try these supported cities**:
• **Indian Cities**: Mumbai, Delhi, Bangalore, Chennai, Kolkata, Hyderabad, Pune
• **International**: New York, London, Tokyo, Paris, Dubai, Singapore, Sydney
• **Or ask**: "current weather", "weather here"

🔧 **Make sure your WeatherAPI.com key is valid**"""
    
    def get_weather_forecast(self, location, days=3):
        """Get weather forecast"""
        forecast_data = self.weather_service.get_weather_forecast(location, days)
        
        if forecast_data['success']:
            data = forecast_data
            forecast_text = f"🌍 **{days}-Day Forecast for {data['location']}, {data['country']}**\n\n"
            
            for i, day in enumerate(data['forecast']):
                date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                
                forecast_text += f"""📅 **{day_name} ({day['date']})** {day['emoji']}
• **High**: {day['max_temp_c']:.1f}°C ({day['max_temp_f']:.1f}°F)
• **Low**: {day['min_temp_c']:.1f}°C ({day['min_temp_f']:.1f}°F)
• **Condition**: {day['condition']}
• **Rain Chance**: {day['chance_of_rain']}%
• **Humidity**: {day['humidity']}%
• **UV Index**: {day['uv_index']}

"""
            
            forecast_text += f"🔍 **Source**: WeatherAPI.com"
            return forecast_text
        else:
            return f"❌ Unable to get forecast for {location}: {forecast_data['error']}"
    
    def convert_units(self, value, from_unit, to_unit):
        """Unit conversion tool"""
        try:
            value = float(value)
            conversions = {
                ('celsius', 'fahrenheit'): lambda x: (x * 9/5) + 32,
                ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
                ('km', 'miles'): lambda x: x * 0.621371,
                ('miles', 'km'): lambda x: x * 1.60934,
                ('meters', 'feet'): lambda x: x * 3.28084,
                ('feet', 'meters'): lambda x: x * 0.3048,
                ('kg', 'pounds'): lambda x: x * 2.20462,
                ('pounds', 'kg'): lambda x: x * 0.453592,
                ('liters', 'gallons'): lambda x: x * 0.264172,
                ('gallons', 'liters'): lambda x: x * 3.78541,
            }
            key = (from_unit.lower(), to_unit.lower())
            if key in conversions:
                result = conversions[key](value)
                return f"📐 **Unit Conversion**: {value} {from_unit} = {result:.2f} {to_unit}"
            else:
                return f"❌ Conversion from {from_unit} to {to_unit} not supported\n\n💡 Supported conversions: Celsius/Fahrenheit, KM/Miles, Meters/Feet, KG/Pounds, Liters/Gallons"
        except:
            return "❌ Invalid conversion request. Please check your values and units."
    
    def call_tool(self, tool_name, parameters):
        """Call a tool with parameters"""
        if tool_name in self.tools:
            try:
                return self.tools[tool_name](**parameters)
            except Exception as e:
                return f"❌ Error using {tool_name}: {str(e)}"
        return f"❌ Tool {tool_name} not found"

class SmartMCPChatbot:
    """Chatbot with real WeatherAPI.com integration and direct responses"""
    
    def __init__(self):
        self.llm = OllamaChatbot("gemma3:1b")
        self.mcp_client = MCPClient()
        self.context_manager = ContextManager()
        
        self.tool_system_prompt = """
        You are an AI assistant with access to various tools including REAL weather data from WeatherAPI.com.

        Available tools:
        - calculator: for mathematical calculations
        - time: for current time in different locations
        - day_info: for day of the week and date information
        - timezone_info: for detailed timezone information
        - weather: for REAL weather information
        - weather_forecast: for weather forecast
        - unit_converter: for unit conversions

        When you need to use a tool, respond with exactly: TOOL_CALL: tool_name parameters

        For normal conversation, just respond naturally without TOOL_CALL.

        Important: Always provide direct, helpful answers without showing tool usage or multiple options.
        """
    
    def parse_tool_call(self, response):
        """Parse tool call from LLM response"""
        tool_pattern = r'TOOL_CALL:\s*(\w+)\s*(.*)'
        match = re.search(tool_pattern, response)
        if match:
            tool_name = match.group(1).strip()
            parameters_str = match.group(2).strip()
            
            params = self.parse_parameters(tool_name, parameters_str)
            return {"name": tool_name, "params": params}
        return None
    
    def parse_parameters(self, tool_name, parameters_str):
        """Parse parameters for different tools"""
        if tool_name == "calculator":
            return {"expression": parameters_str}
        elif tool_name == "weather":
            return {"location": parameters_str or "current"}
        elif tool_name == "weather_forecast":
            parts = parameters_str.split()
            if len(parts) >= 2:
                try:
                    days = int(parts[-1])
                    location = ' '.join(parts[:-1])
                    return {"location": location, "days": days}
                except:
                    return {"location": parameters_str, "days": 3}
            return {"location": parameters_str or "current", "days": 3}
        elif tool_name == "time":
            return {"location": parameters_str or "local"}
        elif tool_name == "day_info":
            return {"location": parameters_str or "india"}
        elif tool_name == "timezone_info":
            return {"location": parameters_str or "india"}
        elif tool_name == "unit_converter":
            parts = parameters_str.split()
            if len(parts) >= 3:
                return {"value": parts[0], "from_unit": parts[1], "to_unit": parts[2]}
            return {"value": "1", "from_unit": "km", "to_unit": "miles"}
        return {}
    
    def detect_direct_tool_use(self, user_message):
        """Detect direct tool usage without LLM intervention"""
        user_lower = user_message.lower()
        
        # Weather detection
        if any(word in user_lower for word in ['weather', 'temperature', 'forecast', 'humidity']):
            if 'forecast' in user_lower:
                location_match = re.search(r'forecast (?:for|in) (.+)', user_lower)
                if location_match:
                    location = location_match.group(1).strip()
                    return "weather_forecast", {"location": location, "days": 3}
            else:
                location_match = re.search(r'weather (?:in|for) (.+)', user_lower)
                if location_match:
                    location = location_match.group(1).strip()
                    return "weather", {"location": location}
                elif 'weather' in user_lower:
                    return "weather", {"location": "current"}
        
        # Calculator detection
        if user_lower.startswith(('calculate', 'compute', 'what is')) and any(op in user_lower for op in ['+', '-', '*', '/']):
            math_expr = re.search(r'(?:calculate|compute|what is) (.+)', user_lower)
            if math_expr:
                expr = math_expr.group(1).strip()
                return "calculator", {"expression": expr}
        
        # Time detection
        if any(word in user_lower for word in ['time', 'current time']):
            location_match = re.search(r'time (?:in|for) (.+)', user_lower)
            location = location_match.group(1).strip() if location_match else "local"
            return "time", {"location": location}
        
        # Unit conversion detection
        if 'convert' in user_lower:
            convert_match = re.search(r'convert (\d+(?:\.\d+)?) (\w+) to (\w+)', user_lower)
            if convert_match:
                value, from_unit, to_unit = convert_match.groups()
                return "unit_converter", {"value": value, "from_unit": from_unit, "to_unit": to_unit}
        
        return None, None
    
    def process_message(self, user_message):
        """Process message with real weather API and direct responses"""
        
        # First, check if this is a direct tool query
        tool_name, tool_params = self.detect_direct_tool_use(user_message)
        
        if tool_name:
            # Use the tool directly and return the result
            tool_result = self.mcp_client.call_tool(tool_name, tool_params)
            self.context_manager.update_context(user_message, tool_result)
            return tool_result
        
        # Get relevant context from previous conversation
        context = self.context_manager.get_context_for_llm()
        
        if context:
            enhanced_message = f"{context}\n\nCurrent question: {user_message}"
        else:
            enhanced_message = user_message
        
        # Let the LLM decide if tools are needed
        llm_response = self.llm.send_message(enhanced_message, self.tool_system_prompt)
        
        # Check if LLM wants to use a tool
        tool_call = self.parse_tool_call(llm_response)
        
        if tool_call:
            # Use the tool and get the result directly
            tool_result = self.mcp_client.call_tool(tool_call["name"], tool_call["params"])
            response = tool_result
        else:
            # For regular conversation, use the LLM response directly
            response = llm_response
        
        # Update conversation context
        self.context_manager.update_context(user_message, response)
        
        return response
    
    def clear_conversation(self):
        """Clear conversation context"""
        self.context_manager.clear_context()

# Initialize the smart chatbot
smart_chatbot = SmartMCPChatbot()

# Conversation storage
conversations = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        conversation_id = data.get("conversation_id", "")
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = {'chatbot': SmartMCPChatbot()}
        
        if conversation_id not in conversations:
            conversations[conversation_id] = {'chatbot': SmartMCPChatbot()}
        
        chatbot_instance = conversations[conversation_id]['chatbot']
        
        response = chatbot_instance.process_message(user_message)
        
        return jsonify({
            "response": response,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "Sorry, I encountered an error. Please try again."}), 500

@app.route("/new_chat", methods=["POST"])
def new_chat():
    """Start a new conversation"""
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = {'chatbot': SmartMCPChatbot()}
    return jsonify({"conversation_id": conversation_id})

@app.route("/clear", methods=["POST"])
def clear_chat():
    """Clear conversation context"""
    data = request.json
    conversation_id = data.get("conversation_id", "")
    
    if conversation_id in conversations:
        conversations[conversation_id]['chatbot'].clear_conversation()
        return jsonify({"message": "Conversation cleared"})
    else:
        return jsonify({"error": "Conversation not found"}), 404

if __name__ == "__main__":
    print("🚀 Smart Chatbot with Real WeatherAPI.com is running!")
    print("🌍 Weather: 'weather in Mumbai', 'current weather in London'")
    print("📅 Forecast: '3-day forecast for Delhi', 'forecast for Tokyo'")
    print("🔢 Calculator: 'calculate 15 * 20'")
    print("🕒 Time: 'time in London', 'current time in India'")
    print("📐 Unit Converter: 'convert 10 km to miles'")
    print("🔑 GET YOUR FREE API KEY FROM: https://www.weatherapi.com/my/")
    print("💡 Replace WEATHERAPI_API_KEY with your actual key!")
    app.run(debug=True, host='0.0.0.0', port=5000)