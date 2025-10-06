import requests
import base64
import io
import re
from PIL import Image
import pytesseract
from mcp_tools import MCPClient

class EnhancedChatbot:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.multimodal_models = ["llava:7b", "llava:13b", "bakllava:7b", "llava:1.6"]
        self.text_models = ["gemma2:2b", "llama3:8b", "mistral", "llama2"]
        self.available_models = self.get_available_models()
        self.ocr_available = self.check_ocr_availability()
        
        # Initialize MCP Client
        self.mcp_client = MCPClient()
        
        print("🤖 Enhanced Chatbot initialized with contextual responses")

    def check_ocr_availability(self):
        """Check if OCR (Tesseract) is available."""
        try:
            pytesseract.get_tesseract_version()
            print("✅ OCR is available")
            return True
        except:
            print("❌ OCR not available")
            return False

    def get_available_models(self):
        """Check available models in Ollama."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                print(f"✅ Available models: {models}")
                return models
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Ollama not reachable: {e}")
            return []

    def get_text_model(self):
        """Choose a text model"""
        if not self.available_models:
            return None
        for model in self.text_models:
            for available_model in self.available_models:
                if model in available_model:
                    print(f"🤖 Using text model: {available_model}")
                    return available_model
        return self.available_models[0]

    def get_multimodal_model(self):
        """Get available multimodal model for image analysis"""
        if not self.available_models:
            return None
            
        for model_pattern in self.multimodal_models:
            for available_model in self.available_models:
                if model_pattern in available_model.lower():
                    print(f"🖼️ Using multimodal model: {available_model}")
                    return available_model
        
        print("❌ No multimodal model available for image analysis")
        return None

    def analyze_image_content(self, image_data, prompt="What do you see in this image?"):
        """Analyze image content using multimodal model (LLaVA)"""
        try:
            model = self.get_multimodal_model()
            if not model:
                return "I'd love to analyze this image, but I need a multimodal model like LLaVA. Please install one with: `ollama pull llava:7b`"

            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            print(f"🔍 Analyzing image with {model}...")
            
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "num_predict": 500,
                    "temperature": 0.3,
                    "top_k": 40,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', 'No analysis received')
                return analysis
            else:
                return "I'm having trouble analyzing the image right now. Please try again in a moment."
                
        except requests.exceptions.Timeout:
            return "The image analysis is taking longer than expected. Please try again with a smaller image or different query."
        except Exception as e:
            return f"I encountered an error while analyzing the image: {str(e)}"

    def create_contextual_response(self, user_message, tool_name, tool_result):
        """Create a natural, contextual response that connects the tool output with the user's message"""
        
        # Remove error markers for cleaner responses
        clean_result = tool_result.replace("❌", "").replace("**", "").strip()
        
        contextual_responses = {
            'weather': [
                f"Sure! Here's the current weather in {user_message.split('in ')[-1].replace('?', '') if 'in ' in user_message else 'that location'}:\n\n{tool_result}",
                f"Let me check the weather for you:\n\n{tool_result}",
                f"According to the latest weather data:\n\n{tool_result}"
            ],
            'news_search': [
                f"Here are the latest news stories about '{user_message.split('about ')[-1].replace('?', '') if 'about ' in user_message else user_message}':\n\n{tool_result}",
                f"I found these recent news articles for you:\n\n{tool_result}",
                f"Here's what's happening in the news regarding your query:\n\n{tool_result}"
            ],
            'breaking_news': [
                f"Here are the latest breaking news headlines:\n\n{tool_result}",
                f"These are the top breaking stories right now:\n\n{tool_result}",
                f"Here's the latest breaking news:\n\n{tool_result}"
            ],
            'web_search': [
                f"I searched for '{user_message.split('for ')[-1].replace('?', '') if 'for ' in user_message else user_message}' and found:\n\n{tool_result}",
                f"Here's what I found about your search:\n\n{tool_result}",
                f"Based on my search:\n\n{tool_result}"
            ],
            'calculator': [
                f"Let me calculate that for you:\n\n{tool_result}",
                f"Here's the calculation result:\n\n{tool_result}",
                f"The answer is:\n\n{tool_result}"
            ],
            'time': [
                f"Here's the current time:\n\n{tool_result}",
                f"According to my clock:\n\n{tool_result}",
                f"The current time is:\n\n{tool_result}"
            ],
            'unit_converter': [
                f"I've converted that for you:\n\n{tool_result}",
                f"Here's the conversion result:\n\n{tool_result}",
                f"The converted value is:\n\n{tool_result}"
            ]
        }
        
        # Default response if no specific template exists
        if tool_name in contextual_responses:
            import random
            response_templates = contextual_responses[tool_name]
            return random.choice(response_templates)
        else:
            return tool_result

    def detect_tool_usage(self, message):
        """Detect which tool to use based on message content"""
        if not message:
            return None
            
        message_lower = message.lower()
        
        # Weather detection
        weather_keywords = ['weather', 'temperature', 'forecast', 'humidity', 'rain', 'sunny', 'cloudy']
        if any(keyword in message_lower for keyword in weather_keywords):
            return 'weather'
        
        # News detection
        news_keywords = ['news', 'latest', 'current events', 'breaking', 'recent', 'update', 'headlines']
        if any(keyword in message_lower for keyword in news_keywords):
            if 'breaking' in message_lower:
                return 'breaking_news'
            return 'news_search'
        
        # Web search detection
        search_keywords = ['search for', 'find information', 'look up', 'web search', 'google']
        if any(keyword in message_lower for keyword in search_keywords):
            return 'web_search'
        
        # Calculator detection
        math_patterns = [r'\d+[\+\-\*\/]', 'calculate', 'solve', 'what is', 'times', 'plus', 'minus', 'multiply', 'divide']
        if any(re.search(pattern, message_lower) for pattern in math_patterns if isinstance(pattern, str)) or \
           any(pattern in message_lower for pattern in math_patterns if not isinstance(pattern, str)):
            math_match = re.search(r'(\d+[\+\-\*\/\d\.\(\) ]+)', message)
            if math_match:
                return 'calculator'
        
        # Time detection
        if 'time' in message_lower and ('current' in message_lower or 'what' in message_lower or 'now' in message_lower):
            return 'time'
        
        # Unit conversion detection
        unit_keywords = ['convert', 'to', 'kilograms to pounds', 'miles to km', 'celsius to fahrenheit']
        if any(keyword in message_lower for keyword in unit_keywords):
            return 'unit_converter'
            
        return None

    def extract_tool_parameters(self, tool_name, message):
        """Extract parameters for different tools"""
        if tool_name == 'weather':
            location_match = re.search(r'weather (?:in|for|at) (.+?)(?:\?|$)', message.lower())
            if location_match:
                return {'location': location_match.group(1).title()}
            return {'location': 'New Delhi'}
        
        elif tool_name in ['news_search', 'web_search']:
            if 'news about' in message.lower():
                query = message.lower().split('news about')[-1].strip()
            elif 'search for' in message.lower():
                query = message.lower().split('search for')[-1].strip()
            elif 'latest' in message.lower():
                query = message.lower().split('latest')[-1].strip()
            else:
                # More intelligent query extraction
                query = re.sub(r'(what is|what are|tell me about|show me|find|search|news|information about)\s+', '', message.lower()).strip()
                query = re.sub(r'[?\.,!]', '', query).strip()
            
            return {'query': query if query else 'current events'}
        
        elif tool_name == 'calculator':
            math_match = re.search(r'(\d+[\+\-\*\/\d\.\(\) ]+)', message)
            if math_match:
                return {'expression': math_match.group(1).strip()}
            numbers = re.findall(r'\d+', message)
            if numbers and ('plus' in message.lower() or '+' in message):
                return {'expression': f"{numbers[0]} + {numbers[1]}" if len(numbers) > 1 else numbers[0]}
            return {'expression': message}
        
        elif tool_name == 'time':
            location_match = re.search(r'time (?:in|at) (.+?)(?:\?|$)', message.lower())
            if location_match:
                return {'location': location_match.group(1).title()}
            return {'location': 'local'}
        
        elif tool_name == 'unit_converter':
            if 'to' in message.lower():
                parts = message.lower().split(' to ')
                if len(parts) == 2:
                    value_match = re.search(r'(\d+(?:\.\d+)?)', parts[0])
                    if value_match:
                        return {
                            'value': value_match.group(1),
                            'from_unit': parts[0].replace(value_match.group(1), '').strip(),
                            'to_unit': parts[1].strip()
                        }
            return {'value': '1', 'from_unit': 'celsius', 'to_unit': 'fahrenheit'}
        
        return {}

    def optimize_image(self, image_data):
        """Optimize image size for analysis"""
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85, optimize=True)
            optimized_bytes = buffer.getvalue()
            
            optimized_b64 = base64.b64encode(optimized_bytes).decode('utf-8')
            return f"data:image/jpeg;base64,{optimized_b64}"
            
        except Exception as e:
            print(f"⚠️ Image optimization failed: {e}")
            return image_data

    def send_message_with_image(self, message, image_data=None):
        """Main message processing with contextual responses"""
        try:
            # Case 1: Image processing
            if image_data:
                print("🖼️ Processing image...")
                
                # Analyze visual content if multimodal model is available
                multimodal_model = self.get_multimodal_model()
                
                if multimodal_model:
                    optimized_image = self.optimize_image(image_data)
                    
                    if message and message.strip():
                        analysis_prompt = message
                    else:
                        analysis_prompt = "What is this image? Describe what you see in detail."
                    
                    print(f"🔍 Analyzing image content with {multimodal_model}...")
                    analysis_result = self.analyze_image_content(optimized_image, analysis_prompt)
                    
                    # Create contextual response for images
                    if message and message.strip():
                        return f"Regarding your question '{message}', here's what I see in the image:\n\n{analysis_result}"
                    else:
                        return f"Here's what I see in this image:\n\n{analysis_result}"
                else:
                    return "I'd love to analyze this image for you, but I need a visual analysis model. Please install LLaVA with: `ollama pull llava:7b`"

            # Case 2: Tool detection and usage
            if message and message.strip():
                tool_name = self.detect_tool_usage(message)
                if tool_name:
                    print(f"🔧 Using MCP tool: {tool_name}")
                    parameters = self.extract_tool_parameters(tool_name, message)
                    tool_result = self.mcp_client.call_tool(tool_name, parameters)
                    
                    # Create contextual response instead of raw tool output
                    contextual_response = self.create_contextual_response(message, tool_name, tool_result)
                    return contextual_response

            # Case 3: Regular text conversation
            if not message or not message.strip():
                return "Hello! I'm your AI assistant. You can ask me about weather, news, calculations, time, unit conversions, or upload images for analysis. How can I help you today?"
                
            model = self.get_text_model()
            if not model:
                return "I'm currently unable to process general conversations. Please make sure Ollama is running and you have language models installed."

            # Enhanced prompt for contextual conversations
            conversation_prompt = f"""
            User: {message}
            
            You are a helpful AI assistant that has access to real-time tools for:
            - Weather information for any location
            - Latest news and breaking news
            - Web searches for current information
            - Mathematical calculations
            - Current time in different timezones
            - Unit conversions
            - Image analysis (when images are uploaded)
            
            If the user is asking for something that could use these tools, gently suggest they try:
            "You can ask me about current weather in any city"
            "I can show you the latest news about any topic"
            "I can help with calculations and conversions"
            "Feel free to upload images for analysis"
            
            Otherwise, provide a helpful, friendly response.
            """
            
            payload = {
                "model": model,
                "prompt": conversation_prompt,
                "stream": False,
                "options": {
                    "num_predict": 500, 
                    "temperature": 0.7,
                }
            }
            
            print(f"📝 Using {model} for conversation...")
            resp = requests.post(self.ollama_url, json=payload, timeout=45)
            
            if resp.status_code == 200:
                return resp.json().get('response', "I'm here to help! What would you like to know?")
            else:
                return "I'm having trouble connecting to my conversation model right now. You can still use my tools for weather, news, calculations, and more!"
                
        except requests.exceptions.ConnectionError:
            return "I can't connect to my AI models right now, but you can still use my tools for weather, news, calculations, and other real-time information!"
        except requests.exceptions.Timeout:
            return "This is taking longer than expected. You might want to try a simpler query or use one of my quick tools like weather or news search."
        except Exception as e:
            return f"I encountered an unexpected issue: {str(e)}\n\nBut don't worry! You can still ask me about weather, news, calculations, and more."

# Test the contextual responses
def test_contextual_responses():
    """Test the contextual response system"""
    chatbot = EnhancedChatbot()
    
    test_messages = [
        "what is current weather in kolkata",
        "latest news about technology",
        "calculate 15 * 25 + 8",
        "current time in london",
        "convert 10 kilometers to miles",
        "breaking news"
    ]
    
    print("🧪 Testing Contextual Responses...")
    print("=" * 60)
    
    for message in test_messages:
        print(f"\n💬 User: {message}")
        tool_name = chatbot.detect_tool_usage(message)
        if tool_name:
            print(f"🔧 Detected tool: {tool_name}")
            parameters = chatbot.extract_tool_parameters(tool_name, message)
            print(f"📋 Parameters: {parameters}")
            
            # Simulate tool result for testing
            simulated_result = f"Simulated result for {tool_name} with {parameters}"
            contextual_response = chatbot.create_contextual_response(message, tool_name, simulated_result)
            print(f"🤖 Response: {contextual_response}")
        else:
            print("❌ No tool detected")
        
        print("-" * 50)

if __name__ == "__main__":
    test_contextual_responses()