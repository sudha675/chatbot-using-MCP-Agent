import requests
import base64
import io
import re
import json
import time
from PIL import Image
import pytesseract
from mcp_tools import MCPClient

class ConversationMemory:
    """Handles conversation context and memory"""
    
    def __init__(self, max_history=10):
        self.conversation_history = []
        self.max_history = max_history
        self.current_context = {}
    
    def add_interaction(self, user_message, assistant_response):
        """Add a conversation turn to history"""
        interaction = {
            'user': user_message,
            'assistant': assistant_response,
            'timestamp': time.time()
        }
        
        self.conversation_history.append(interaction)
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
        
        # Update current context
        self._update_context(user_message, assistant_response)
    
    def _update_context(self, user_message, assistant_response):
        """Update current context based on the conversation"""
        # Extract potential topics from messages
        topics = self._extract_topics(user_message + " " + assistant_response)
        self.current_context = {
            'last_user_message': user_message,
            'last_assistant_response': assistant_response,
            'topics': topics,
            'conversation_length': len(self.conversation_history)
        }
    
    def _extract_topics(self, text):
        """Extract main topics from text"""
        topics = set()
        
        # Common topic patterns
        topic_patterns = {
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network'],
            'technology': ['technology', 'tech', 'software', 'computer', 'digital', 'programming'],
            'science': ['science', 'scientific', 'research', 'experiment'],
            'weather': ['weather', 'temperature', 'climate', 'forecast'],
            'news': ['news', 'headlines', 'current events', 'breaking'],
            'education': ['education', 'learn', 'study', 'teaching', 'school'],
            'business': ['business', 'company', 'industry', 'market'],
            'health': ['health', 'medical', 'medicine', 'doctor'],
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.add(topic)
        
        return list(topics)
    
    def get_conversation_context(self):
        """Get formatted context for the AI"""
        if not self.conversation_history:
            return "No previous conversation."
        
        context = "Previous conversation:\n"
        for i, interaction in enumerate(self.conversation_history[-3:], 1):  # Last 3 exchanges
            context += f"{i}. User: {interaction['user']}\n"
            context += f"   Assistant: {interaction['assistant'][:100]}...\n"
        
        return context
    
    def is_follow_up_question(self, current_message):
        """Check if current message is a follow-up to previous conversation"""
        if len(self.conversation_history) < 1:
            return False
        
        last_interaction = self.conversation_history[-1]
        last_user_msg = last_interaction['user'].lower()
        current_msg = current_message.lower()
        
        # Follow-up indicators
        follow_up_indicators = [
            'it', 'that', 'this', 'those', 'these',
            'how about', 'what about', 'and what', 'also',
            'in that case', 'following that',
            'where', 'when', 'how', 'why', 'who'
        ]
        
        # Check for pronouns and follow-up phrases
        has_follow_up_indicators = any(indicator in current_msg for indicator in follow_up_indicators)
        
        # Check if topics are related
        previous_topics = set(self._extract_topics(last_user_msg))
        current_topics = set(self._extract_topics(current_msg))
        topics_related = len(previous_topics.intersection(current_topics)) > 0
        
        return has_follow_up_indicators or topics_related

class EnhancedChatbot:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.multimodal_models = ["llava:7b", "llava:13b", "bakllava:7b", "llava:1.6"]
        self.text_models = ["gemma2:2b", "llama3:8b", "mistral", "llama2"]
        self.available_models = self.get_available_models()
        self.ocr_available = self.check_ocr_availability()
        
        # Initialize MCP Client and Conversation Memory
        self.mcp_client = MCPClient()
        self.memory = ConversationMemory()
        
        print("🤖 Enhanced Chatbot initialized with conversation memory")

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
        
        # Check if this is a follow-up question
        is_follow_up = self.memory.is_follow_up_question(user_message)
        
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
        
        # Add follow-up context if needed
        if is_follow_up and self.memory.conversation_history:
            last_topic = self.memory.current_context.get('topics', [])
            if last_topic:
                follow_up_prefix = f"Following up on our discussion about {last_topic[0]}, "
                import random
                if tool_name in contextual_responses:
                    base_response = random.choice(contextual_responses[tool_name])
                    return follow_up_prefix + base_response.lower()
        
        # Default response
        if tool_name in contextual_responses:
            import random
            return random.choice(contextual_responses[tool_name])
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

    def generate_conversational_response(self, user_message):
        """Generate a response that maintains conversation context"""
        model = self.get_text_model()
        if not model:
            return "I'm here to help! What would you like to know?"
        
        # Build context-aware prompt
        conversation_context = self.memory.get_conversation_context()
        
        prompt = f"""
        Conversation History:
        {conversation_context}
        
        Current User Message: {user_message}
        
        You are a helpful AI assistant. The user is engaging in a conversation with you.
        Please provide a natural, contextual response that:
        1. Acknowledges the conversation history if relevant
        2. Answers the current question directly
        3. Shows understanding of the topic continuity
        4. Is friendly and engaging
        
        If this seems like a follow-up question, connect it to the previous discussion.
        You have access to real-time tools for weather, news, calculations, etc.
        
        Response:
        """
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 600,
                "temperature": 0.7,
                "top_k": 50,
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get('response', "I understand. What would you like to know more about?")
            else:
                return "I'm here to help! What would you like to discuss?"
        except:
            return "I understand. How can I assist you further?"

    def send_message_with_image(self, message, image_data=None):
        """Main message processing with conversation memory"""
        try:
            final_response = ""
            
            # Case 1: Image processing
            if image_data:
                print("🖼️ Processing image...")
                
                multimodal_model = self.get_multimodal_model()
                
                if multimodal_model:
                    optimized_image = self.optimize_image(image_data)
                    
                    if message and message.strip():
                        analysis_prompt = message
                    else:
                        analysis_prompt = "What is this image? Describe what you see in detail."
                    
                    analysis_result = self.analyze_image_content(optimized_image, analysis_prompt)
                    
                    if message and message.strip():
                        final_response = f"Regarding your question '{message}', here's what I see in the image:\n\n{analysis_result}"
                    else:
                        final_response = f"Here's what I see in this image:\n\n{analysis_result}"
                else:
                    final_response = "I'd love to analyze this image, but I need a visual analysis model."

            # Case 2: Tool detection and usage
            elif message and message.strip():
                tool_name = self.detect_tool_usage(message)
                if tool_name:
                    print(f"🔧 Using MCP tool: {tool_name}")
                    parameters = self.extract_tool_parameters(tool_name, message)
                    tool_result = self.mcp_client.call_tool(tool_name, parameters)
                    
                    # Create contextual response
                    final_response = self.create_contextual_response(message, tool_name, tool_result)
                else:
                    # Generate conversational response for non-tool queries
                    final_response = self.generate_conversational_response(message)

            # Case 3: No message
            else:
                if self.memory.conversation_history:
                    final_response = "What would you like to know more about?"
                else:
                    final_response = "Hello! I'm your AI assistant. You can ask me about weather, news, calculations, or upload images. How can I help you?"

            # Store in memory
            self.memory.add_interaction(message or "[Image Upload]", final_response)
            
            return final_response
                
        except requests.exceptions.ConnectionError:
            error_msg = "I'm having connection issues, but you can still try asking your question."
            self.memory.add_interaction(message, error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"I encountered an issue: {str(e)}. Let's try again."
            self.memory.add_interaction(message, error_msg)
            return error_msg

# Test conversation flow
def test_conversation_flow():
    """Test the conversation memory system"""
    chatbot = EnhancedChatbot()
    
    conversation_flow = [
        "What is artificial intelligence?",
        "Where is it used in real world?",
        "How does machine learning relate to AI?",
        "What are some practical applications?",
        "Tell me about healthcare applications"
    ]
    
    print("🧪 Testing Conversation Flow...")
    print("=" * 60)
    
    for i, message in enumerate(conversation_flow, 1):
        print(f"\n💬 Turn {i}: {message}")
        print("---")
        response = chatbot.send_message_with_image(message)
        print(f"🤖 {response}")
        print("-" * 50)
        
        # Show memory state
        print(f"🧠 Memory: {len(chatbot.memory.conversation_history)} interactions")
        print(f"📚 Topics: {chatbot.memory.current_context.get('topics', [])}")
        print(f"🔗 Follow-up: {chatbot.memory.is_follow_up_question(message)}")

if __name__ == "__main__":
    test_conversation_flow()