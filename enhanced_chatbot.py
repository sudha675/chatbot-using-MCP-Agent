import requests
import base64
import io
import re
import json
from PIL import Image, ImageEnhance
import pytesseract
from datetime import datetime

# Import our custom modules
from email_agent import EmailAgent
from langchain_memory import LangChainConversationMemory
from mcp_tools import MCPClient
from live_news import fetch_live_news, fetch_breaking_news

class EnhancedChatbot:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # OPTIMIZED FOR GRANITE3.2-VISION with fallbacks
        self.multimodal_models = [
            "granite3.2-vision:latest",  # Primary model
            "granite3.2-vision",         # Alternate name
            "granite-vision",            # Fallback
            "llava:1.6-3b",              # Fast backup
            "llava:1.5-3b",              # Very fast backup
            "bakllava:1-7b",             # Quality backup
            "llava:7b"                    # Last resort
        ]
        
        self.text_models = [
            "granite3.2:latest",         # Text version for consistency
            "granite3.2",                # Alternate
            "gemma2:2b",                 # Fast fallback
            "llama2:7b",                  # Reliable fallback
            "mistral:7b",                  # Quality fallback
            "phi:2.7b"                    # Very fast
        ]
        
        self.available_models = self.get_available_models()
        self.ocr_available = self.check_ocr_availability()
        
        # Initialize components
        self.mcp_client = MCPClient()
        self.memory = LangChainConversationMemory()
        # EmailAgent uses the chatbot's own text generation for composing emails
        self.email_agent = EmailAgent(llm_generate=self._generate_email_content)
        
        # Simple cache for image analysis
        self.image_cache = {}
        
        print("=== Enhanced Chatbot Initialized ===")
        print("Optimized for Granite3.2-Vision")
        print("Available Features:")
        print(f"  Text AI Models: {len(self.available_models)} available")
        print(f"  Multimodal AI: {'Available' if self.get_multimodal_model() else 'Not Available'}")
        print(f"  OCR Text Extraction: {'Available' if self.ocr_available else 'Not Available'}")
        print(f"  Live News: Available")
        print(f"  Email Services: Available")
        print(f"  Memory Management: Available")
        print(f"  Code Generation: Available")
        print(f"  Tool Detection: Available")
        
        if not self.ocr_available:
            print("WARNING: OCR is not available. Install Tesseract for text extraction from images.")
        
        multimodal_model = self.get_multimodal_model()
        if multimodal_model:
            print(f"Primary Vision Model: {multimodal_model}")
        else:
            print("Granite3.2-Vision not available. Install with: ollama pull granite3.2-vision:latest")

    def check_ocr_availability(self):
        """Check if OCR (Tesseract) is available."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def get_available_models(self):
        """Retrieve available models from Ollama with robust parsing."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = []
                if 'models' in data:
                    for model in data['models']:
                        if 'name' in model:
                            models.append(model['name'])
                print(f"Found {len(models)} models: {models}")
                return models
            return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def get_text_model(self):
        """Choose a reliable text model that won't timeout."""
        if not self.available_models:
            return None
        # Prefer fast models
        priority_models = [
            "gemma2:2b", "phi:2.7b", "granite3.2:latest",
            "mistral:7b", "llama2:7b"
        ]
        for model_pattern in priority_models:
            for available_model in self.available_models:
                if model_pattern.lower() in available_model.lower():
                    print(f"Selected text model: {available_model}")
                    return available_model
        return self.available_models[0] if self.available_models else None

    def get_multimodal_model(self):
        """Get the fastest available multimodal model to prevent timeouts."""
        if not self.available_models:
            return None
        # Prioritize fast vision models
        priority_models = [
            "llava:1.6-3b", "llava:1.5-3b", "granite3.2-vision:latest",
            "llava:1.6-vicuna-3b", "bakllava:1-7b", "llava:7b"
        ]
        for preferred in priority_models:
            for available_model in self.available_models:
                if preferred.lower() in available_model.lower():
                    print(f"Selected vision model: {available_model}")
                    return available_model
        # Fallback to any multimodal model
        for available_model in self.available_models:
            if any(mm in available_model.lower() for mm in ["llava", "bakllava", "vision", "granite"]):
                print(f"Fallback vision model: {available_model}")
                return available_model
        return None

    def diagnose_ollama_status(self):
        """Diagnose Ollama status and model availability."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                status = {
                    'ollama_running': True,
                    'available_models': [m.get('name') for m in models],
                    'multimodal_available': bool(self.get_multimodal_model()),
                    'text_models_available': bool(self.get_text_model()),
                    'total_models': len(models)
                }
                return status
            else:
                return {'ollama_running': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'ollama_running': False, 'error': str(e)}

    # ---------- Image Processing ----------
    def process_image_data_for_ollama(self, image_data):
        """Return pure base64 string without data URL prefix."""
        try:
            if not image_data:
                return None
            # Already pure base64
            if (isinstance(image_data, str) and 
                not image_data.startswith('data:') and 
                re.match(r'^[A-Za-z0-9+/=]+$', image_data)):
                return image_data
            # Data URL
            if isinstance(image_data, str) and image_data.startswith('data:'):
                if ',' in image_data:
                    base64_part = image_data.split(',', 1)[1]
                    if re.match(r'^[A-Za-z0-9+/=]+$', base64_part):
                        return base64_part
                return None
            # Bytes
            if isinstance(image_data, bytes):
                return base64.b64encode(image_data).decode('utf-8')
            return None
        except Exception as e:
            print(f"Error processing image data: {e}")
            return None

    def optimize_image(self, image_data, max_size=(800, 800), quality=70):
        """Optimize image size for faster analysis."""
        try:
            processed_data = self.process_image_data_for_ollama(image_data)
            if not processed_data:
                return image_data
            image_bytes = base64.b64decode(processed_data)
            image = Image.open(io.BytesIO(image_bytes))
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            optimized_bytes = buffer.getvalue()
            return base64.b64encode(optimized_bytes).decode('utf-8')
        except Exception as e:
            print(f"Image optimization error: {e}")
            return self.process_image_data_for_ollama(image_data) or image_data

    def analyze_image_content(self, image_data, prompt="Describe this image in detail:"):
        """Analyze image content using multimodal model with caching."""
        # Generate cache key
        import hashlib
        img_hash = hashlib.md5(image_data[:10000].encode()).hexdigest()
        cache_key = f"{img_hash}_{prompt}"
        if cache_key in self.image_cache:
            print("Using cached image analysis")
            return self.image_cache[cache_key]

        try:
            model = self.get_multimodal_model()
            if not model:
                if self.ocr_available:
                    return "VISION MODEL NOT AVAILABLE - Using OCR:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return "Image analysis requires a vision model. Install with: ollama pull granite3.2-vision:latest"

            # Check connectivity
            try:
                test_response = requests.get("http://localhost:11434/api/tags", timeout=10)
                if test_response.status_code != 200:
                    if self.ocr_available:
                        return "OLLAMA SERVICE NOT AVAILABLE - Using OCR:\n\n" + self.extract_text_with_ocr(image_data)
                    else:
                        return "Ollama service not available."
                models_data = test_response.json()
                available_models = [m.get('name', '') for m in models_data.get('models', [])]
                if model not in available_models:
                    return f"MODEL {model} NOT LOADED. Please run: ollama pull {model}\n\nUsing OCR:\n\n" + self.extract_text_with_ocr(image_data)
            except Exception as e:
                if self.ocr_available:
                    return f"CANNOT CONNECT TO OLLAMA - Using OCR:\n\n{self.extract_text_with_ocr(image_data)}"
                else:
                    return f"Cannot connect to Ollama: {str(e)}"

            processed_image = self.process_image_data_for_ollama(image_data)
            if not processed_image:
                if self.ocr_available:
                    return "INVALID IMAGE DATA - Using OCR:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return "Invalid image data."

            optimized_image = self.optimize_image(processed_image)
            detailed_prompt = prompt + "\nProvide a comprehensive description covering main subjects, colors, context, and any notable details."
            payload = {
                "model": model,
                "prompt": detailed_prompt,
                "images": [optimized_image],
                "stream": False,
                "options": {"num_predict": 300, "temperature": 0.4}  # Reduced for speed
            }
            resp = requests.post(self.ollama_url, json=payload, timeout=60)
            if resp.status_code == 200:
                parsed = resp.json()
                analysis = self._parse_ollama_response_text(parsed)
                if analysis and len(analysis.strip()) > 10:
                    result = f"IMAGE ANALYSIS\n\n{analysis}\n\n---\nAnalyzed using {model}"
                    self.image_cache[cache_key] = result
                    return result
                elif self.ocr_available:
                    return "IMAGE ANALYSIS RETURNED EMPTY RESPONSE - Using OCR:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return "Image analysis returned empty response."
            else:
                error_msg = f"API Error: {resp.status_code}"
                if self.ocr_available:
                    return f"{error_msg} - Using OCR:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return f"Unable to analyze image: {error_msg}"
        except Exception as e:
            if self.ocr_available:
                return f"IMAGE ANALYSIS ERROR - Using OCR:\n\n{self.extract_text_with_ocr(image_data)}"
            else:
                return f"Image analysis error: {str(e)}"

    def extract_text_with_ocr(self, image_data):
        """Extract text from image using Tesseract OCR."""
        if not self.ocr_available:
            return "OCR not available. Please install Tesseract."
        try:
            if isinstance(image_data, str) and image_data.startswith('data:'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            # Preprocess for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            extracted = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
            cleaned = self._clean_ocr_text(extracted)
            if not cleaned.strip():
                return "No readable text could be extracted."
            return f"OCR TEXT EXTRACTION\n\n{cleaned}"
        except Exception as e:
            return f"OCR error: {str(e)}"

    def _clean_ocr_text(self, text):
        """Clean OCR output."""
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    # ---------- Email Generation ----------
    def _generate_email_content(self, prompt):
        """Generate email content using the text model. Used by EmailAgent."""
        model = self.get_text_model()
        if not model:
            return "Subject: Error\n\nUnable to generate email content at this time."
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 500, "temperature": 0.7}
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=30)
            if resp.status_code == 200:
                parsed = resp.json()
                return self._parse_ollama_response_text(parsed) or ""
            else:
                return ""
        except Exception:
            return ""

    # ---------- Tool Detection ----------
    def detect_email_request(self, message):
        """Detect if user wants to send an email."""
        if not message:
            return False
        message_lower = message.lower()
        email_keywords = ['send email', 'send mail', 'compose email', 'write email',
                          'email to', 'mail to', 'write a mail', 'write an email']
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        has_email = re.search(email_pattern, message) is not None
        return any(keyword in message_lower for keyword in email_keywords) or has_email

    def detect_ocr_request(self, message):
        """Detect if user explicitly wants OCR."""
        if not message:
            return False
        message_lower = message.lower()
        ocr_keywords = ['extract text', 'read text', 'ocr', 'text recognition',
                        'scan text', 'text from image', 'copy text from']
        return any(keyword in message_lower for keyword in ocr_keywords)

    def detect_code_request(self, message):
        """Detect if user is asking for code."""
        if not message:
            return False
        message_lower = message.lower()
        code_keywords = ['program', 'code', 'example', 'write a program',
                         'how to code', 'implementation', 'function', 'class']
        return any(keyword in message_lower for keyword in code_keywords)

    def detect_news_request(self, message):
        """Detect if user is asking for news."""
        if not message:
            return False
        message_lower = message.lower()
        news_keywords = ['news', 'headlines', 'breaking', 'current events',
                         'latest update', 'today news']
        return any(keyword in message_lower for keyword in news_keywords)

    def detect_tool_usage(self, message):
        """Detect which tool to use."""
        if not message:
            return None
        if self.detect_email_request(message):
            return 'email'
        if self.detect_ocr_request(message):
            return 'ocr'
        if self.detect_news_request(message):
            return 'news_search'
        # Weather
        weather_keywords = ['weather', 'temperature', 'forecast', 'humid']
        if any(keyword in message.lower() for keyword in weather_keywords):
            return 'weather'
        # Calculator
        math_patterns = [r'^\d+[\+\-\*\/]\d+$', r'calculate', r'what is \d+']
        if any(re.search(p, message.lower()) for p in math_patterns):
            return 'calculator'
        # Time
        if 'time' in message.lower():
            return 'time'
        return None

    def extract_tool_parameters(self, tool_name, message):
        """Extract parameters for tools."""
        if tool_name == 'weather':
            location_match = re.search(r'weather (?:in|for|at) (.+?)(?:\?|$)', message.lower())
            if location_match:
                return {'location': location_match.group(1).title()}
            return {'location': 'New Delhi'}
        elif tool_name == 'news_search':
            if 'breaking' in message.lower():
                return {'query': 'breaking news'}
            return {'query': 'latest news'}
        elif tool_name == 'calculator':
            math_match = re.search(r'([-+\d\.\(\)\s\*\/]+)', message)
            if math_match:
                return {'expression': math_match.group(1).strip()}
            return {'expression': message}
        elif tool_name == 'time':
            location_match = re.search(r'time in (.+?)(?:\?|$)', message.lower())
            if location_match:
                return {'location': location_match.group(1).title()}
            return {'location': 'local'}
        return {}

    def handle_news_request(self, parameters):
        """Fetch live news."""
        query = parameters.get('query', 'latest news')
        if query == 'breaking news':
            return fetch_breaking_news()
        else:
            return fetch_live_news(query)

    def handle_email_request(self, user_message):
        """Generate email preview."""
        return self.email_agent.generate_email_preview(user_message)

    def handle_email_auto_send(self, user_message):
        """Send email automatically."""
        return self.email_agent.send_email_auto(user_message)

    def create_contextual_response(self, tool_name, result):
        """Wrap tool result in a simple header."""
        headers = {
            'weather': 'WEATHER INFORMATION',
            'news_search': 'LIVE NEWS UPDATE',
            'calculator': 'CALCULATION RESULT',
            'time': 'CURRENT TIME',
            'ocr': 'OCR TEXT EXTRACTION'
        }
        header = headers.get(tool_name, tool_name.upper().replace('_', ' '))
        return f"{header}\n\n{result}"

    def generate_code_response(self, user_message):
        """Generate code response."""
        model = self.get_text_model()
        if not model:
            return "I can help with code. Please ask a specific programming question."
        prompt = f"""Provide a complete, runnable code example for: {user_message}
Include necessary imports and comments. Wrap code in ```language``` blocks."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 800, "temperature": 0.3}
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=60)
            if resp.status_code == 200:
                parsed = resp.json()
                result = self._parse_ollama_response_text(parsed)
                return self._ensure_code_formatting(result or "Here's a code example.")
            else:
                return "I can provide a code example. Please try again."
        except Exception:
            return "Error generating code."

    def _ensure_code_formatting(self, text):
        """Ensure code blocks are present."""
        if '```' not in text:
            lines = text.split('\n')
            code_lines = [line for line in lines if re.match(r'^\s*(def |class |import |from |if |for |while |\w+\s*=)', line)]
            if code_lines:
                text = '```python\n' + '\n'.join(code_lines) + '\n```'
        return text

    def generate_concise_response(self, user_message):
        """Generate a detailed response for general queries."""
        if self.detect_code_request(user_message):
            return self.generate_code_response(user_message)
        model = self.get_text_model()
        if not model:
            return "I'm here to help. What would you like to know?"
        context = self.memory.get_conversation_context()
        prompt = f"""{context}
Current Question: {user_message}
Provide a comprehensive, detailed answer covering key concepts, practical examples, and important considerations.
Answer:"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 400, "temperature": 0.7}  # Reduced for speed
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=30)
            if resp.status_code == 200:
                parsed = resp.json()
                return self._parse_ollama_response_text(parsed) or "I understand your question. Let me provide detailed information."
            else:
                return "I'd like to give you a detailed answer. Please try again."
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def _parse_ollama_response_text(self, response_json):
        """Extract text from Ollama response."""
        if not response_json:
            return ""
        if isinstance(response_json, dict):
            if 'response' in response_json:
                return response_json['response']
            if 'output' in response_json:
                return response_json['output']
            if 'result' in response_json:
                return response_json['result']
            if 'choices' in response_json and response_json['choices']:
                first = response_json['choices'][0]
                if isinstance(first, dict):
                    if 'text' in first:
                        return first['text']
                    if 'message' in first and isinstance(first['message'], dict):
                        return first['message'].get('content', '')
            try:
                return json.dumps(response_json)
            except:
                return str(response_json)
        return str(response_json)

    def send_message_with_image(self, message, image_data=None):
        """Main entry point for processing a message (with optional image)."""
        try:
            final_response = ""
            tool_used = None

            if image_data:
                print("Processing image...")
                if self.detect_ocr_request(message):
                    final_response = self.extract_text_with_ocr(image_data)
                    tool_used = "ocr"
                else:
                    final_response = self.analyze_image_content(image_data, message or "Describe this image:")
                    tool_used = "image_analysis"
            elif message and message.strip():
                tool_name = self.detect_tool_usage(message)
                if tool_name:
                    if tool_name == 'email':
                        final_response = self.handle_email_auto_send(message)
                        tool_used = "email"
                    elif tool_name == 'news_search':
                        params = self.extract_tool_parameters(tool_name, message)
                        final_response = self.handle_news_request(params)
                        tool_used = "news_search"
                    elif tool_name == 'ocr':
                        final_response = "Please upload an image containing text."
                        tool_used = "ocr"
                    else:
                        params = self.extract_tool_parameters(tool_name, message)
                        result = self.mcp_client.call_tool(tool_name, params)
                        final_response = self.create_contextual_response(tool_name, result)
                        tool_used = tool_name
                else:
                    final_response = self.generate_concise_response(message)
                    tool_used = "conversation"
            else:
                final_response = self._get_welcome_message()
                tool_used = "greeting"

            self.memory.add_interaction(message or "[Image Upload]", final_response, tool_used)
            return final_response
        except Exception as e:
            error_msg = f"Service temporarily unavailable. Error: {str(e)}"
            self.memory.add_interaction(message, error_msg, "error")
            return error_msg

    def _get_welcome_message(self):
        vision = self.get_multimodal_model()
        ocr = "Available" if self.ocr_available else "Not Available"
        return f"""AI ASSISTANT - Enhanced with Full Image Support

VISION CAPABILITIES:
- Advanced image understanding using {vision if vision else 'vision models'}
- Detailed visual descriptions
- Status: {'Available' if vision else 'Not Available'}

OCR TEXT EXTRACTION:
- Extract text from images, screenshots, documents
- Status: {ocr}

REAL-TIME TOOLS:
- Weather forecasts for any location
- Mathematical calculations
- Time zone information
- Unit conversions
- Live news updates
- Professional email composition

Just ask me anything or upload an image! I'll provide thorough analysis.

What would you like to explore today?"""

    # Memory management
    def get_conversation_summary(self):
        return self.memory.get_conversation_summary()

    def clear_memory(self):
        self.memory.clear_memory()
        return "Conversation memory cleared"

    def get_conversation_history(self):
        return self.memory.get_conversation_context()