# enhanced_chatbot.py
import requests
import base64
import io
import re
import json
import time
import random
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
from datetime import datetime

# Import our custom modules
from email_agent import EmailAgent
from langchain_memory import LangChainConversationMemory
from pdf_processor import PDFProcessor
from mcp_tools import MCPClient
from live_news import fetch_live_news, fetch_breaking_news, fetch_newsapi_country_news

class EnhancedChatbot:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # OPTIMIZED FOR GRANITE3.2-VISION with fallbacks
        self.multimodal_models = [
            "granite3.2-vision:latest",  # Primary model
            "granite3.2-vision",         # Alternate name
            "granite-vision",            # Fallback
            "llava:1.6-3b",              # Fast backup
            "llava:1.5-3b",              # Reliable backup
            "bakllava:1-7b",             # Quality backup
            "llava:7b"                   # Last resort
        ]
        
        self.text_models = [
            "granite3.2:latest",         # Text version for consistency
            "granite3.2",                # Alternate
            "gemma2:2b",                 # Fast fallback
            "llama2:7b",                 # Reliable fallback
            "mistral:7b",                # Quality fallback
            "phi:2.7b"                   # Very fast
        ]
        
        self.available_models = self.get_available_models()
        self.ocr_available = self.check_ocr_availability()
        
        # Initialize components
        self.mcp_client = MCPClient()
        self.memory = LangChainConversationMemory()
        self.email_agent = EmailAgent()
        self.pdf_processor = PDFProcessor()
        
        # Store current PDF data for email attachments
        self.current_pdf_data = None
        
        # Enhanced initialization message
        print("=== Enhanced Chatbot Initialized ===")
        print("Optimized for Granite3.2-Vision")
        print("Available Features:")
        print(f"  Text AI Models: {len(self.available_models)} available")
        print(f"  Multimodal AI: {'Available' if self.get_multimodal_model() else 'Not Available'}")
        print(f"  OCR Text Extraction: {'Available' if self.ocr_available else 'Not Available'}")
        print(f"  PDF Processing: Available")
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
                
                # Handle different response formats
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
            
        # Prefer Granite models for consistency, then fast models
        priority_models = [
            "granite3.2:latest",     # Primary
            "granite3.2",            # Alternate
            "gemma2:2b",             # Fast
            "phi:2.7b",              # Very fast
            "mistral:7b",            # Reliable
            "llama2:7b"              # Fallback
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
            
        # Priority order - fastest first
        priority_models = [
            "granite3.2-vision:latest",  # Primary
            "granite3.2-vision",         # Alternate
            "granite-vision",            # Fallback
            "llava:1.6-3b",              # Fast
            "llava:1.5-3b",              # Very fast
            "llava:1.6-vicuna-3b",       # Lightweight
            "bakllava:1-7b",             # Balanced
            "llava:7b",                  # Fallback
            "llava:13b"                  # Last resort
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
            # Check Ollama service
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

    def process_image_data_for_ollama(self, image_data):
        """
        Process image data for Ollama API - CRITICAL FIX
        Returns pure base64 string without data URL prefix
        """
        try:
            if not image_data:
                return None
                
            print(f"Processing image data (length: {len(image_data)})")
            
            # If it's already a pure base64 string (no data URL), return as is
            if (isinstance(image_data, str) and 
                not image_data.startswith('data:') and 
                len(image_data) > 100 and
                re.match(r'^[A-Za-z0-9+/=]+$', image_data)):
                print("Already pure base64")
                return image_data
                
            # Handle data URL format: "data:image/jpeg;base64,{base64_data}"
            if isinstance(image_data, str) and image_data.startswith('data:'):
                print("Processing data URL")
                if ',' in image_data:
                    # Extract the base64 part after the comma
                    base64_part = image_data.split(',', 1)[1]
                    # Validate it's actually base64
                    if re.match(r'^[A-Za-z0-9+/=]+$', base64_part):
                        print(f"Extracted base64 (length: {len(base64_part)})")
                        return base64_part
                    else:
                        print("Invalid base64 in data URL")
                        return None
                else:
                    print("Malformed data URL - no comma found")
                    return None
                    
            # If it's bytes, convert to base64
            if isinstance(image_data, bytes):
                print("Converting bytes to base64")
                return base64.b64encode(image_data).decode('utf-8')
                
            print(f"Unsupported image data type: {type(image_data)}")
            return None
            
        except Exception as e:
            print(f"Error processing image data: {e}")
            return None

    def debug_image_data(self, image_data):
        """Debug method to check image data format."""
        debug_info = {
            "type": type(image_data).__name__,
            "length": len(image_data) if isinstance(image_data, (str, bytes)) else "N/A",
            "starts_with": image_data[:50] + "..." if isinstance(image_data, str) else "N/A",
            "is_base64": False,
            "has_data_prefix": False
        }
        
        if isinstance(image_data, str):
            debug_info["has_data_prefix"] = image_data.startswith('data:')
            # Check if it's valid base64 (rough check)
            base64_part = image_data
            if debug_info["has_data_prefix"] and ',' in image_data:
                base64_part = image_data.split(',', 1)[1]
            
            debug_info["is_base64"] = bool(re.match(r'^[A-Za-z0-9+/=]*$', base64_part))
            debug_info["base64_length"] = len(base64_part)
        
        return debug_info

    def optimize_image(self, image_data, max_size=(1024, 1024), quality=85):
        """Optimize image size for analysis with proper base64 handling."""
        try:
            print("Optimizing image...")
            
            # Process the image data first
            processed_data = self.process_image_data_for_ollama(image_data)
            if not processed_data:
                print("Image processing failed, returning original")
                return image_data
                
            # Convert base64 to image
            try:
                image_bytes = base64.b64decode(processed_data)
                image = Image.open(io.BytesIO(image_bytes))
                print(f"Original image size: {image.size}")
            except Exception as e:
                print(f"Error opening image: {e}")
                return processed_data

            # Resize if too large
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                print(f"Resizing image to {max_size}")
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"New image size: {image.size}")
                
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # Save optimized image
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            optimized_bytes = buffer.getvalue()
            
            # Return pure base64 without data URL prefix for Ollama
            optimized_b64 = base64.b64encode(optimized_bytes).decode('utf-8')
            print(f"Image optimized: {len(optimized_b64)} chars")
            return optimized_b64
            
        except Exception as e:
            print(f"Image optimization error: {e}")
            # Return processed data (pure base64) even if optimization fails
            return self.process_image_data_for_ollama(image_data) or image_data

    def analyze_image_content(self, image_data, prompt="Describe this image in detail:"):
        """Analyze image content using multimodal model with proper base64 handling."""
        try:
            model = self.get_multimodal_model()
            if not model:
                # Fallback to OCR if no vision model available
                if self.ocr_available:
                    return "VISION MODEL NOT AVAILABLE - Using OCR for text extraction instead:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return "Image analysis requires a vision model. Install with: ollama pull granite3.2-vision:latest"

            # CRITICAL: Check if Ollama is actually running and model is loaded
            try:
                # Test Ollama connectivity
                test_response = requests.get("http://localhost:11434/api/tags", timeout=10)
                if test_response.status_code != 200:
                    if self.ocr_available:
                        return "OLLAMA SERVICE NOT AVAILABLE - Using OCR for text extraction:\n\n" + self.extract_text_with_ocr(image_data)
                    else:
                        return "Ollama service not available. Please start Ollama service."
                
                # Check if specific model is loaded
                models_data = test_response.json()
                available_models = [m.get('name', '') for m in models_data.get('models', [])]
                if model not in available_models:
                    return f"MODEL {model} NOT LOADED - Please load the model first: ollama pull {model}\n\nUsing OCR instead:\n\n" + self.extract_text_with_ocr(image_data)
                    
            except requests.exceptions.RequestException as e:
                if self.ocr_available:
                    return f"CANNOT CONNECT TO OLLAMA - Error: {str(e)}\n\nUsing OCR for text extraction:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return f"Cannot connect to Ollama service: {str(e)}"

            # CRITICAL FIX: Use the new base64 processing method
            processed_image_data = self.process_image_data_for_ollama(image_data)
            
            if not processed_image_data:
                if self.ocr_available:
                    return "INVALID IMAGE DATA - Using OCR for text extraction:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return "Invalid image data provided. Please check the image format."

            # Optimize image for faster processing
            optimized_image = self.optimize_image(processed_image_data)
            
            print(f"Sending image to {model} (optimized base64 length: {len(optimized_image)})")

            # Enhanced prompt for detailed image analysis
            detailed_prompt = """
            Provide a comprehensive and detailed description of this image. Include:

            1. MAIN SUBJECT AND SETTING:
            - Primary objects, people, or scenes
            - Environment and background details
            - Overall composition and framing

            2. VISUAL CHARACTERISTICS:
            - Colors, lighting, and mood
            - Style and artistic elements
            - Notable visual features

            3. CONTEXT AND INTERPRETATION:
            - Possible meaning or story
            - Cultural or historical context if apparent
            - Emotional impact or atmosphere

            4. DETAILED OBSERVATIONS:
            - Specific elements worth noting
            - Technical aspects if relevant
            - Unique or distinctive features

            Be thorough and descriptive in your analysis.
            """
            
            if prompt != "Describe this image in detail:":
                detailed_prompt = prompt + "\n" + detailed_prompt

            payload = {
                "model": model,
                "prompt": detailed_prompt,
                "images": [optimized_image],  # Use OPTIMIZED data
                "stream": False,
                "options": {
                    "num_predict": 800,  # Increased for detailed analysis
                    "temperature": 0.4,
                    "top_k": 40,
                    "top_p": 0.9
                }
            }
            
            print(f"Sending request to Ollama...")
            
            # INCREASED TIMEOUT to 120 seconds for detailed analysis
            resp = requests.post(self.ollama_url, json=payload, timeout=120)
            
            if resp.status_code == 200:
                parsed = resp.json()
                analysis = self._parse_ollama_response_text(parsed)
                
                if not analysis or len(analysis.strip()) < 10:
                    return "IMAGE ANALYSIS RETURNED EMPTY RESPONSE - Using OCR instead:\n\n" + self.extract_text_with_ocr(image_data)
                    
                # Format the response nicely
                formatted_response = f"IMAGE ANALYSIS\n\n{analysis}\n\n---\nAnalyzed using {model}"
                return formatted_response
            else:
                error_msg = f"API Error: {resp.status_code} - {resp.text}"
                print(f"API Error: {error_msg}")
                if self.ocr_available:
                    return "IMAGE ANALYSIS API ERROR - Using OCR for text extraction:\n\n" + self.extract_text_with_ocr(image_data)
                else:
                    return f"Unable to analyze image: {error_msg}"
                    
        except requests.exceptions.Timeout:
            # Fallback to OCR on timeout
            if self.ocr_available:
                return "IMAGE ANALYSIS TIMEOUT (120s) - Vision model is taking too long to respond. This could be due to:\n- Large image size\n- High system load\n- Model not fully loaded\n\nUsing OCR for text extraction:\n\n" + self.extract_text_with_ocr(image_data)
            else:
                return "Image analysis timed out after 120 seconds. Please try again later."
        except Exception as e:
            error_msg = str(e)
            print(f"Image analysis error: {error_msg}")
            if self.ocr_available:
                return f"IMAGE ANALYSIS ERROR - Error: {error_msg}\n\nUsing OCR for text extraction:\n\n{self.extract_text_with_ocr(image_data)}"
            else:
                return f"Image analysis error: {error_msg}"

    def extract_text_with_ocr(self, image_data, parameters=None):
        """Extract text from image using Tesseract OCR with enhanced processing."""
        if not self.ocr_available:
            return self._get_ocr_installation_instructions()
            
        try:
            print("Performing OCR text extraction...")
            
            # Handle different image data formats
            if isinstance(image_data, str) and image_data.startswith('data:'):
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
            
            # Convert base64 to image
            try:
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                print(f"OCR image size: {image.size}")
            except Exception as e:
                return f"Error processing image for OCR: {str(e)}"

            # Preprocess image for better OCR results
            processed_image = self.preprocess_image_for_ocr(image)
            
            # Configure OCR parameters
            ocr_config = self.get_ocr_config(parameters)
            
            # Perform OCR
            print("Extracting text with Tesseract...")
            extracted_text = pytesseract.image_to_string(processed_image, config=ocr_config)
            
            # Clean and format the extracted text
            cleaned_text = self.clean_ocr_text(extracted_text)
            
            if not cleaned_text.strip():
                return """OCR RESULT

No readable text could be extracted from this image.

Tips for better OCR results:
- Ensure the image is clear and well-lit
- Text should be clearly visible and not too small
- Try using a higher resolution image
- Ensure text is not distorted or rotated"""

            # Analyze text quality and provide statistics
            word_count = len(cleaned_text.split())
            char_count = len(cleaned_text)
            line_count = len(cleaned_text.split('\n'))
            
            stats = f"EXTRACTION STATISTICS:\n- Words: {word_count}\n- Characters: {char_count}\n- Lines: {line_count}"
            
            return f"""OCR TEXT EXTRACTION

{stats}

EXTRACTED TEXT:
{cleaned_text}

Note: OCR accuracy depends on image quality and text clarity."""
            
        except Exception as e:
            return f"OCR Processing Error: {str(e)}"

    def preprocess_image_for_ocr(self, image):
        """Preprocess image to improve OCR accuracy."""
        try:
            print("Preprocessing image for OCR...")
            
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)  # Increase contrast
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Resize if too small (minimum 300px width for better OCR)
            if image.size[0] < 300:
                new_width = 600
                ratio = new_width / image.size[0]
                new_height = int(image.size[1] * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized image to: {image.size}")
            
            return image
            
        except Exception as e:
            print(f"OCR preprocessing failed: {e}")
            return image

    def get_ocr_config(self, parameters):
        """Get OCR configuration based on parameters."""
        config = '--oem 3 --psm 6'  # Default: LSTM + uniform block of text
        
        if parameters:
            language = parameters.get('language', 'eng')
            config += f' -l {language}'
            
            if parameters.get('enhance', True):
                config += ' -c preserve_interword_spaces=1'
        
        return config

    def clean_ocr_text(self, text):
        """Clean and format OCR extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        
        # Fix common OCR errors
        replacements = {
            '|': 'I',
            '0': 'O',  # Context-dependent, be careful
            '1': 'I',  # Context-dependent
        }
        
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text

    def _get_ocr_installation_instructions(self):
        """Get OCR installation instructions."""
        return """OCR functionality is not available. 

To enable OCR text extraction, please install Tesseract OCR:

INSTALLATION INSTRUCTIONS:

Windows:
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Or use: choco install tesseract

macOS:
- brew install tesseract

Linux (Ubuntu/Debian):
- sudo apt update && sudo apt install tesseract-ocr

After installation, restart the application."""

    def detect_email_request(self, message):
        """Detect if user wants to send an email."""
        if not message:
            return False
            
        message_lower = message.lower()
        email_keywords = [
            'send email', 'send mail', 'compose email', 'write email',
            'email to', 'mail to', 'write a mail', 'write an email',
            'sent a mail', 'sent an email', 'invite', 'invitation'
        ]
        
        # Check for email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        has_email = re.search(email_pattern, message) is not None
        
        return any(keyword in message_lower for keyword in email_keywords) or has_email

    def detect_pdf_request(self, message):
        """Detect if user wants to process a PDF."""
        if not message:
            return False
            
        message_lower = message.lower()
        pdf_keywords = [
            'pdf', 'document', 'read pdf', 'analyze pdf', 'pdf summary',
            'extract from pdf', 'pdf main points', 'summarize pdf'
        ]
        
        return any(keyword in message_lower for keyword in pdf_keywords)

    def detect_ocr_request(self, message):
        """Detect if user explicitly wants to extract text from images using OCR."""
        if not message:
            return False
            
        message_lower = message.lower()
        ocr_keywords = [
            'extract text', 'read text', 'ocr', 'text recognition', 'scan text',
            'read document', 'text from image', 'copy text from', 'text in image',
            'read this image', 'extract words', 'text extraction', 'optical character',
            'scan document', 'text recognition from', 'what text is in this image',
            'get text from', 'text in this'
        ]
        
        # More specific matching to avoid false positives
        return any(f" {keyword} " in f" {message_lower} " for keyword in ocr_keywords)

    def detect_code_request(self, message):
        """Detect if user is asking for code examples."""
        if not message:
            return False
            
        message_lower = message.lower()
        code_keywords = [
            'program', 'code', 'example', 'write a program', 'how to code',
            'implementation', 'function', 'class', 'script', 'algorithm',
            'switch case', 'if else', 'loop', 'method', 'example code',
            'sample code', 'code snippet', 'programming'
        ]
        
        programming_languages = [
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby',
            'go', 'rust', 'swift', 'kotlin', 'typescript', 'html', 'css',
            'sql', 'bash', 'shell'
        ]
        
        has_code_keyword = any(keyword in message_lower for keyword in code_keywords)
        has_language = any(lang in message_lower for lang in programming_languages)
        
        return has_code_keyword or has_language

    def detect_news_request(self, message):
        """Detect if user is asking for news - ENHANCED WITH LIVE NEWS."""
        if not message:
            return False
            
        message_lower = message.lower()
        
        # News keywords
        news_keywords = [
            'news', 'headlines', 'breaking', 'current events', 'latest update',
            'today news', 'recent news', "what's happening", 'current affairs',
            'top stories', 'news update', 'live news'
        ]
        
        # Country-specific news requests
        country_keywords = [
            'india news', 'us news', 'usa news', 'uk news', 'canada news',
            'australia news', 'germany news', 'france news', 'japan news',
            'world news', 'international news'
        ]
        
        has_news_keyword = any(keyword in message_lower for keyword in news_keywords)
        has_country_news = any(keyword in message_lower for keyword in country_keywords)
        has_breaking = 'breaking' in message_lower and 'news' in message_lower
        
        return has_news_keyword or has_country_news or has_breaking

    def detect_tool_usage(self, message):
        """Simplified and more reliable tool detection - ENHANCED WITH OCR & NEWS."""
        if not message:
            return None
            
        message_lower = message.lower().strip()
        
        # Priority-based detection
        if self.detect_email_request(message):
            return 'email'
        
        if self.detect_pdf_request(message):
            return 'pdf_analysis'
        
        # OCR DETECTION - HIGH PRIORITY for images
        if self.detect_ocr_request(message):
            return 'ocr'
        
        # NEWS DETECTION - HIGH PRIORITY
        if self.detect_news_request(message):
            return 'news_search'
        
        # WEATHER - with more comprehensive patterns
        weather_keywords = [
            'weather', 'temperature', 'forecast', 'humid', 'wind', 
            'degrees', 'celsius', 'fahrenheit'
        ]
        
        weather_phrases = [
            'what is the weather', "what's the weather", 'current weather',
            'how is the weather', 'weather like', 'weather in', 'weather at',
            'temperature in', 'temperature at', 'how hot', 'how cold'
        ]
        
        has_weather_keyword = any(keyword in message_lower for keyword in weather_keywords)
        has_weather_phrase = any(phrase in message_lower for phrase in weather_phrases)
        
        if has_weather_keyword or has_weather_phrase:
            return 'weather'
        
        # CALCULATOR - only clear math
        math_patterns = [
            r'^\d+[\+\-\*\/]\d+$',
            r'calculate\s+[-\d\.\s\+\-\*\/\(\)]+',
            r'compute\s+[-\d\.\s\+\-\*\/\(\)]+', 
            r'what is\s+[-\d\.\s\+\-\*\/\(\)]+',
            r'^\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?$'
        ]
        
        # Additional check: if message contains ONLY numbers and operators
        math_only_pattern = r'^[\d\+\-\*\/\(\)\.\s]+$'
        has_clear_math = any(re.search(pattern, message_lower) for pattern in math_patterns)
        is_math_only = re.match(math_only_pattern, message_lower.replace(' ', ''))
        
        if has_clear_math or is_math_only:
            return 'calculator'
        
        # TIME
        time_keywords = ['time', 'current time', 'what time', 'time now', 'time in']
        if any(keyword in message_lower for keyword in time_keywords):
            return 'time'
        
        # UNIT CONVERSION
        unit_keywords = ['convert', 'kilograms to', 'miles to', 'celsius to', 'pounds to', 'km to']
        if any(keyword in message_lower for keyword in unit_keywords):
            return 'unit_converter'
            
        return None

    def extract_tool_parameters(self, tool_name, message):
        """Extract parameters for different tools - ENHANCED WITH NEWS & OCR."""
        message_lower = message.lower()
        
        if tool_name == 'weather':
            # Extract location from weather queries
            location_patterns = [
                r'weather (?:in|for|at) (.+?)(?:\?|$)',
                r'temperature (?:in|for|at) (.+?)(?:\?|$)',
                r'forecast (?:in|for|at) (.+?)(?:\?|$)',
                r'weather (.+?)$'
            ]
            
            for pattern in location_patterns:
                location_match = re.search(pattern, message_lower)
                if location_match:
                    location = location_match.group(1).strip()
                    # Clean up the location
                    location = re.sub(r'[^\w\s]', '', location)  # Remove punctuation
                    if location and len(location) > 1:
                        return {'location': location.title()}
            
            # Default location if none found
            return {'location': 'New Delhi'}
        
        elif tool_name == 'news_search':
            # Enhanced news query extraction
            country_map = {
                'india': ['india', 'indian'],
                'usa': ['usa', 'us', 'united states', 'america'],
                'uk': ['uk', 'united kingdom', 'britain'],
                'canada': ['canada', 'canadian'],
                'australia': ['australia'],
                'germany': ['germany'],
                'france': ['france'],
                'japan': ['japan']
            }
            
            # Detect specific country
            detected_country = None
            for country, keywords in country_map.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_country = country
                    break
            
            if detected_country:
                return {'query': detected_country, 'country': detected_country}
            elif 'breaking' in message_lower:
                return {'query': 'breaking news', 'country': 'global'}
            elif 'world' in message_lower or 'international' in message_lower:
                return {'query': 'world news', 'country': 'global'}
            else:
                return {'query': 'latest news', 'country': 'india'}  # Default to India news
        
        elif tool_name == 'calculator':
            # Extract math expression
            math_match = re.search(r'([-+\d\.\(\)\s\*\/]+)', message)
            if math_match:
                return {'expression': math_match.group(1).strip()}
            return {'expression': message}
        
        elif tool_name == 'time':
            # Extract location for time
            location_match = re.search(r'time in (.+?)(?:\?|$)', message_lower)
            if location_match:
                return {'location': location_match.group(1).title()}
            return {'location': 'local'}
        
        elif tool_name == 'unit_converter':
            # Basic unit conversion parameters (placeholder; can be improved)
            return {'value': '1', 'from_unit': 'celsius', 'to_unit': 'fahrenheit'}
        
        elif tool_name == 'ocr':
            # OCR-specific parameters
            return {'language': 'eng', 'enhance': True}
        
        return {}

    def handle_news_request(self, parameters):
        """Handle news requests using live_news.py."""
        try:
            query = parameters.get('query', 'latest news')
            country = parameters.get('country', 'india')
            
            print(f"Fetching news for: {query} (country: {country})")
            
            # Use the live_news module
            if query == 'breaking news':
                news_result = fetch_breaking_news()
            else:
                news_result = fetch_live_news(query)
            
            # Format the response
            if isinstance(news_result, str) and news_result.startswith("ERROR"):
                return f"NEWS UPDATE\n\n{news_result}\n\nPlease try again later or check your internet connection."
            elif isinstance(news_result, str):
                return f"LIVE NEWS UPDATE\n\n{news_result}\n\nStay informed with the latest developments from reliable news sources."
            else:
                # If module returns structured data, attempt to stringify
                try:
                    return f"LIVE NEWS UPDATE\n\n{json.dumps(news_result, indent=2)}"
                except Exception:
                    return "LIVE NEWS UPDATE\n\n(Received news in unexpected format.)"
                
        except Exception as e:
            return f"NEWS SERVICE\n\nUnable to fetch news at the moment. Error: {str(e)}\n\nPlease try again later."

    def handle_ocr_request(self, image_data, parameters=None):
        """Handle OCR text extraction from images with better error handling."""
        if not self.ocr_available:
            return self._get_ocr_installation_instructions()

        try:
            # Enhanced image validation
            if not image_data or (isinstance(image_data, str) and len(image_data) < 100):
                return "Invalid image data provided for OCR processing."
            
            # Extract text from image using OCR
            extracted_text = self.extract_text_with_ocr(image_data, parameters)
            return extracted_text
            
        except Exception as e:
            error_detail = str(e)
            if "tesseract is not installed" in error_detail.lower():
                return "Tesseract OCR not found. Please install Tesseract OCR and ensure it's in your system PATH."
            else:
                return f"OCR Processing Error: {error_detail}"

    def process_pdf_content(self, pdf_data, user_message=""):
        """Process PDF and extract detailed content."""
        try:
            print("Processing PDF content...")
            
            # Extract text from PDF
            extraction_result = self.pdf_processor.extract_text_from_pdf(pdf_data)
            
            if not extraction_result.get('success', False):
                return f"PDF ERROR\n\n{extraction_result.get('error', 'Unknown error')}"
            
            # Analyze PDF structure with more detail
            structure = self.pdf_processor.analyze_pdf_structure(extraction_result.get('text', ''))
            extraction_result['structure'] = structure
            
            # Generate comprehensive report
            detailed_report = self.generate_detailed_pdf_summary(extraction_result, user_message)
            
            # Store PDF data for potential email sending
            self.current_pdf_data = extraction_result
            
            return detailed_report
            
        except Exception as e:
            return f"PDF PROCESSING ERROR\n\n{str(e)}"

    def generate_detailed_pdf_summary(self, extraction_result, user_message):
        """Generate comprehensive PDF summary."""
        model = self.get_text_model()
        if not model:
            return self.pdf_processor.format_pdf_report(extraction_result)
        
        prompt = f"""
        Based on the following PDF content, provide a COMPREHENSIVE summary:

        PDF STRUCTURE:
        - Pages: {extraction_result.get('metadata', {}).get('pages', 'N/A')}
        - Key Topics: {extraction_result.get('key_points', [])[:3]}

        CONTENT EXCERPT (first 1000 characters):
        {extraction_result.get('text','')[:1000]}...

        User's specific interest: {user_message}

        Please provide a detailed summary covering:
        1. MAIN PURPOSE AND SCOPE
        2. KEY FINDINGS OR ARGUMENTS 
        3. IMPORTANT DETAILS AND EXAMPLES
        4. OVERALL SIGNIFICANCE OR IMPLICATIONS

        Ensure the summary is thorough yet readable, highlighting the most important aspects of the document.

        Detailed Summary:
        """
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 600,
                "temperature": 0.6,
            }
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=30)
            if resp.status_code == 200:
                parsed = resp.json()
                detailed_summary = self._parse_ollama_response_text(parsed)
                if detailed_summary:
                    return f"COMPREHENSIVE PDF ANALYSIS\n\n{detailed_summary}\n\n{self.pdf_processor.format_pdf_report(extraction_result)}"
            # fallback to local formatting if API fails
            return self.pdf_processor.format_pdf_report(extraction_result)
        except Exception:
            return self.pdf_processor.format_pdf_report(extraction_result)

    def handle_pdf_email_request(self, user_message, pdf_data):
        """Handle PDF analysis and email sending request."""
        try:
            # First process the PDF
            pdf_analysis = self.process_pdf_content(pdf_data, user_message)
            
            if pdf_analysis.startswith("PDF ERROR"):
                return pdf_analysis
            
            # Extract recipient email from user message
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_message)
            recipient_email = email_match.group(0) if email_match else None
            
            if not recipient_email:
                return f"{pdf_analysis}\n\nERROR: No recipient email found. Please specify an email address."
            
            # Try to send email automatically with PDF content
            enhanced_message = f"PDF Analysis Summary for {recipient_email}\n\n{pdf_analysis}"
            send_result = self.email_agent.send_email_auto(enhanced_message)
            
            return f"{pdf_analysis}\n\n{send_result}"
            
        except Exception as e:
            return f"PROCESSING ERROR\n\n{str(e)}"

    def handle_email_request(self, user_message):
        """Handle email composition and sending."""
        try:
            # Generate email preview
            email_preview = self.email_agent.generate_email_preview(user_message)
            
            response = f"""
{email_preview}

I can automatically send this email using configured credentials. Ready to proceed?
"""
            return response
            
        except Exception as e:
            return f"Error composing email: {str(e)}"

    def handle_email_auto_send(self, user_message):
        """Handle email composition and automatic sending with default credentials."""
        try:
            # Try to send automatically
            send_result = self.email_agent.send_email_auto(user_message)
            
            if isinstance(send_result, str) and "SUCCESS" in send_result:
                return f"Email Sent Successfully\n\n{send_result}"
            else:
                return f"Action Required\n\n{send_result}"
            
        except Exception as e:
            return f"Email processing error: {str(e)}"

    def _parse_ollama_response_text(self, response_json):
        """
        Helper: try extracting human-readable text from various Ollama-like responses.
        """
        if not response_json:
            return ""
        # Common shapes:
        # 1) {"response": "text..."}
        # 2) {"choices": [{"message": {"content": "..."}}], ...}
        # 3) {"output": "text"} or {"result": "text"}
        if isinstance(response_json, dict):
            if 'response' in response_json and isinstance(response_json['response'], str):
                return response_json['response']
            if 'output' in response_json and isinstance(response_json['output'], str):
                return response_json['output']
            if 'result' in response_json and isinstance(response_json['result'], str):
                return response_json['result']
            # choices pattern
            if 'choices' in response_json and isinstance(response_json['choices'], list) and response_json['choices']:
                first = response_json['choices'][0]
                # try nested
                if isinstance(first, dict):
                    # a few possibilities
                    if 'text' in first:
                        return first['text']
                    if 'message' in first and isinstance(first['message'], dict):
                        # try content
                        return first['message'].get('content', '') or first['message'].get('text', '')
            # last fallback: stringify
            try:
                return json.dumps(response_json)
            except Exception:
                return str(response_json)
        else:
            # if array or string
            try:
                return str(response_json)
            except Exception:
                return ""

    def create_contextual_response(self, user_message, tool_name, tool_result):
        """Create contextual responses for tools."""
        contextual_responses = {
            'weather': f"WEATHER INFORMATION\n\n{tool_result}",
            'news_search': f"LIVE NEWS UPDATE\n\n{tool_result}",
            'calculator': f"CALCULATION RESULT\n\n{tool_result}",
            'time': f"CURRENT TIME\n\n{tool_result}",
            'unit_converter': f"UNIT CONVERSION\n\n{tool_result}",
            'web_search': f"SEARCH RESULTS\n\n{tool_result}",
            'ocr': f"OCR TEXT EXTRACTION\n\n{tool_result}"
        }
        
        return contextual_responses.get(tool_name, tool_result)

    def generate_code_response(self, user_message):
        """Generate responses with actual code examples."""
        model = self.get_text_model()
        if not model:
            return "I'm here to help. What would you like to know?"
        
        # Get conversation context from LangChain memory
        conversation_context = self.memory.get_conversation_context()
        is_follow_up = self.memory.is_follow_up_question(user_message)
        
        # Enhanced prompt for code generation with memory context
        prompt = f"""
        {conversation_context}
        
        Current User Request: {user_message}
        Is this a follow-up question: {is_follow_up}

        You are an expert programming assistant. The user wants actual runnable code.

        CRITICAL INSTRUCTIONS:
        - You MUST provide complete, runnable code examples
        - Wrap ALL code in ``` ``` code blocks with the correct language
        - Include proper imports and dependencies
        - Add comments to explain key parts
        - Show example usage with output
        - Make sure the code is syntactically correct
        - If this is a follow-up, connect it to previous discussion

        Response Structure:
        1. Brief explanation (1-2 sentences)
        2. Complete code example in ```language ``` blocks
        3. Example usage and expected output
        4. Key points summary

        Now provide the actual code for: {user_message}
        """
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 800,  # More tokens for code
                "temperature": 0.3,   # Lower temperature for consistent code
                "top_k": 40,
            }
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=60)
            if resp.status_code == 200:
                parsed = resp.json()
                result = self._parse_ollama_response_text(parsed)
                return self.ensure_code_formatting(result or "I'll provide you with a complete code example.")
            else:
                return "I can help with coding questions. Let me provide you with a complete code example."
        except Exception:
            return "I understand you need code. Let me provide you with a working example."

    def ensure_code_formatting(self, text):
        """Ensure the response has proper code formatting."""
        if '```' not in text:
            lines = text.split('\n')
            in_code_block = False
            code_lines = []
            formatted_lines = []
            
            for line in lines:
                # Detect start of code (imports, def/class, or typical code patterns)
                if (re.match(r'^\s*(def |class |import |from |if |for |while |\w+\s*=)', line) and 
                    not in_code_block and len(line.strip()) > 0):
                    in_code_block = True
                    formatted_lines.append('```python')
                    code_lines = [line]
                elif in_code_block:
                    # continue code block until an obviously non-code line encountered
                    if line.strip() == '' or re.match(r'^\s', line) or re.match(r'^[#\w]', line.strip()):
                        code_lines.append(line)
                    else:
                        in_code_block = False
                        formatted_lines.extend(code_lines)
                        formatted_lines.append('```')
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            
            if in_code_block and code_lines:
                formatted_lines.extend(code_lines)
                formatted_lines.append('```')
            
            text = '\n'.join(formatted_lines)
        
        return text

    def generate_concise_response(self, user_message):
        """Generate detailed, comprehensive responses with memory context."""
        # Check if this is a code-related question
        if self.detect_code_request(user_message):
            return self.generate_code_response(user_message)
            
        model = self.get_text_model()
        if not model:
            return "I'm here to help. What would you like to know?"
        
        # Get conversation context from LangChain memory
        conversation_context = self.memory.get_conversation_context()
        is_follow_up = self.memory.is_follow_up_question(user_message)
        
        prompt = f"""
        {conversation_context}
        
        Current Question: {user_message}
        Is this a follow-up: {is_follow_up}

        Provide a COMPREHENSIVE and DETAILED answer. Structure your response with:

        MAIN EXPLANATION:
        - Clear, thorough definition/explanation of the topic
        - Cover fundamental concepts and principles
        - Provide context and background information

        KEY ASPECTS:
        - 3-5 important characteristics or components
        - Practical implications or real-world applications
        - Current relevance or modern context

        PRACTICAL CONSIDERATIONS:
        - How this applies in real scenarios
        - Benefits, challenges, or important considerations
        - Future trends or developments if relevant

        If this is a follow-up question, explicitly connect it to our previous discussion and expand on related concepts.

        Ensure the response flows naturally as one cohesive paragraph while covering all these aspects comprehensively.

        Answer in detail:
        """
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 800,
                "temperature": 0.7,
                "top_k": 50,
            }
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=45)
            if resp.status_code == 200:
                parsed = resp.json()
                result = self._parse_ollama_response_text(parsed) or "I understand your question. Let me provide detailed information about this topic."
                
                # Ensure response is sufficiently detailed
                word_count = len(result.split())
                if word_count < 80:
                    enhancement_prompt = f"""
                    The following answer is too brief. Please expand it to be more comprehensive while maintaining accuracy:

                    Original Question: {user_message}
                    Current Answer: {result}

                    Please provide a more detailed explanation covering:
                    1. Core concepts and definitions
                    2. Key characteristics and components  
                    3. Practical applications and examples
                    4. Important considerations or context

                    Expanded Detailed Answer:
                    """
                    
                    enhancement_payload = {
                        "model": model,
                        "prompt": enhancement_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 600,
                            "temperature": 0.7,
                        }
                    }
                    
                    enhancement_resp = requests.post(self.ollama_url, json=enhancement_payload, timeout=30)
                    if enhancement_resp.status_code == 200:
                        enhancement_parsed = enhancement_resp.json()
                        result = self._parse_ollama_response_text(enhancement_parsed) or result
                
                return result
            else:
                return "I'd like to provide you with a comprehensive explanation. Let me share detailed information about this topic covering the key concepts, practical applications, and important considerations that will help you understand it thoroughly."
        except Exception as e:
            return f"I want to give you a detailed response about this topic. Error: {str(e)}"

    def send_message_with_image_and_pdf(self, message, image_data=None, pdf_data=None):
        """Main message processing with enhanced image and PDF support."""
        try:
            final_response = ""
            tool_used = None
            
            print(f"Processing message: '{message}'")
            print(f"Image data: {'Yes' if image_data else 'No'}")
            print(f"PDF data: {'Yes' if pdf_data else 'No'}")

            # Case 1: PDF processing
            if pdf_data:
                print("Processing PDF...")
                if self.detect_email_request(message):
                    final_response = self.handle_pdf_email_request(message, pdf_data)
                    tool_used = "pdf_email"
                else:
                    final_response = self.process_pdf_content(pdf_data, message)
                    tool_used = "pdf_analysis"

            # Case 2: Image processing
            elif image_data:
                print("Processing image...")
                
                # Debug image data
                debug_info = self.debug_image_data(image_data)
                print(f"Image debug: {debug_info}")
                
                # Check if user specifically wants OCR
                wants_ocr = self.detect_ocr_request(message)
                
                # If user explicitly asks for OCR, use OCR
                if wants_ocr:
                    print("User requested OCR")
                    if self.ocr_available:
                        parameters = self.extract_tool_parameters('ocr', message)
                        final_response = self.handle_ocr_request(image_data, parameters)
                        tool_used = "ocr"
                    else:
                        final_response = self._get_ocr_installation_instructions()
                        tool_used = "ocr_error"
                
                # Otherwise, try image analysis with vision model
                else:
                    try:
                        multimodal_model = self.get_multimodal_model()
                        if multimodal_model:
                            print(f"Using vision model: {multimodal_model}")
                            
                            # Use the enhanced analyze_image_content method
                            if message and message.strip():
                                analysis_prompt = message
                            else:
                                analysis_prompt = "Describe this image in detail:"
                            
                            final_response = self.analyze_image_content(image_data, analysis_prompt)
                            tool_used = "image_analysis"
                        else:
                            # Fallback to OCR if no vision model
                            print("No vision model, falling back to OCR")
                            if self.ocr_available:
                                final_response = "VISION MODEL NOT AVAILABLE - Using OCR for text extraction instead:\n\n" + self.extract_text_with_ocr(image_data)
                                tool_used = "ocr_fallback"
                            else:
                                final_response = "No image analysis models available. Install Granite3.2-Vision or Tesseract OCR."
                                tool_used = "image_analysis_error"
                                
                    except Exception as e:
                        print(f"Image analysis error: {e}")
                        # Fallback to OCR on any error
                        if self.ocr_available:
                            final_response = f"IMAGE ANALYSIS FAILED - Using OCR for text extraction:\n\n{self.extract_text_with_ocr(image_data)}"
                            tool_used = "ocr_fallback"
                        else:
                            final_response = f"Image analysis error: {str(e)}"
                            tool_used = "image_analysis_error"

            # Case 3: Tool detection and usage
            elif message and message.strip():
                tool_name = self.detect_tool_usage(message)
                print(f"Detected tool: {tool_name} for message: '{message}'")
                
                if tool_name:
                    if tool_name == 'email':
                        final_response = self.handle_email_auto_send(message)
                        tool_used = "email"
                    elif tool_name == 'pdf_analysis':
                        final_response = "I can analyze PDF documents. Please upload a PDF file."
                        tool_used = "pdf_analysis"
                    elif tool_name == 'news_search':
                        parameters = self.extract_tool_parameters(tool_name, message)
                        print(f"Calling Live News with params: {parameters}")
                        final_response = self.handle_news_request(parameters)
                        tool_used = "news_search"
                    elif tool_name == 'ocr':
                        final_response = "I can extract text from images using OCR. Please upload an image containing text."
                        tool_used = "ocr"
                    else:
                        parameters = self.extract_tool_parameters(tool_name, message)
                        print(f"Calling MCP tool {tool_name} with params: {parameters}")
                        tool_result = self.mcp_client.call_tool(tool_name, parameters)
                        final_response = self.create_contextual_response(message, tool_name, tool_result)
                        tool_used = tool_name
                else:
                    # Generate detailed response for general queries
                    final_response = self.generate_concise_response(message)
                    tool_used = "conversation"

            # Case 4: No message
            else:
                if getattr(self.memory, "conversation_metadata", None) and len(self.memory.conversation_metadata) > 0:
                    final_response = "What would you like to know more about? I'm ready to provide you with detailed explanations and comprehensive information on any topic you're interested in exploring further."
                else:
                    final_response = self._get_welcome_message()
                tool_used = "greeting"

            # Store in LangChain memory
            user_input = message or "[File Upload]" 
            if pdf_data:
                user_input += " (PDF)"
            elif image_data:
                user_input += " (Image)"
                
            self.memory.add_interaction(user_input, final_response, tool_used)
            
            print(f"Response generated using: {tool_used}")
            return final_response
                
        except Exception as e:
            error_msg = f"Service temporarily unavailable. Error: {str(e)}"
            print(f"Error in send_message: {str(e)}")
            try:
                self.memory.add_interaction(message, error_msg, "error")
            except Exception:
                pass
            return error_msg

    def _get_welcome_message(self):
        """Get comprehensive welcome message."""
        multimodal_model = self.get_multimodal_model()
        vision_status = "Available" if multimodal_model else "Not Available"
        ocr_status = "Available" if self.ocr_available else "Not Available"
        
        return f"""AI ASSISTANT - Enhanced with Full Image Support

I'm designed to provide you with comprehensive responses and advanced file processing:

VISION CAPABILITIES:
- Advanced image understanding using {multimodal_model if multimodal_model else 'vision models'}
- Detailed visual descriptions and object recognition
- Context-aware image interpretation
- Professional image analysis
- Status: {vision_status}

OCR TEXT EXTRACTION:
- Extract text from images, screenshots, and documents
- Read text from photos of documents, signs, or books
- Convert image text to editable format
- Support for multiple languages
- Status: {ocr_status}

DOCUMENT PROCESSING:
- PDF analysis and summarization
- Document structure recognition
- Key points extraction

REAL-TIME TOOLS:
- Weather forecasts for any location
- Mathematical calculations
- Time zone information
- Unit conversions

Just ask me anything or upload an image/PDF! I'll provide thorough, well-structured analysis.

What would you like to explore today?"""

    # Backward compatibility method
    def send_message_with_image(self, message, image_data=None):
        return self.send_message_with_image_and_pdf(message, image_data, None)
    
    # Memory management methods
    def get_conversation_summary(self):
        """Get conversation summary from LangChain memory"""
        return self.memory.get_conversation_summary()
    
    def clear_memory(self):
        """Clear LangChain memory"""
        self.memory.clear_memory()
        return "Conversation memory cleared"
    
    def get_conversation_history(self):
        """Get conversation history from LangChain memory"""
        return self.memory.get_conversation_context()


# Test functions for image functionality
def test_image_functionality():
    """Test image analysis and OCR functionality"""
    bot = EnhancedChatbot()
    
    print("Testing Image Functionality...")
    print("=" * 60)
    
    # Check system status
    status = bot.diagnose_ollama_status()
    print(f"Ollama Running: {status.get('ollama_running', False)}")
    print(f"Total Models: {status.get('total_models', 0)}")
    print(f"Vision Model: {bot.get_multimodal_model()}")
    print(f"OCR Available: {bot.ocr_available}")
    
    # Test base64 processing
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    debug_info = bot.debug_image_data(test_image)
    print(f"Base64 Debug: {debug_info}")
    
    processed = bot.process_image_data_for_ollama(test_image)
    print(f"Processed data length: {len(processed) if processed else 'None'}")
    
    print("=" * 60)
    print("Image functionality test completed!")

if __name__ == "__main__":
    # Run comprehensive tests
    test_image_functionality()