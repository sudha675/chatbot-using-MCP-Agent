# enhanced_chatbot.py
import requests
import base64
import io
import re
import json
import time
import random
from PIL import Image
import pytesseract

# Import our custom modules
from email_agent import EmailAgent
from langchain_memory import LangChainConversationMemory
from pdf_processor import PDFProcessor
from mcp_tools import MCPClient
from live_news import fetch_live_news, fetch_breaking_news, fetch_newsapi_country_news  # Import news functions

class EnhancedChatbot:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.multimodal_models = ["llava:7b", "llava:13b", "bakllava:7b", "llava:1.6"]
        self.text_models = ["gemma2:2b"]
        self.available_models = self.get_available_models()
        self.ocr_available = self.check_ocr_availability()
        
        # Initialize components
        self.mcp_client = MCPClient()
        self.memory = LangChainConversationMemory()
        self.email_agent = EmailAgent()
        self.pdf_processor = PDFProcessor()
        
        # Store current PDF data for email attachments
        self.current_pdf_data = None
        
        print("Enhanced Chatbot with Live News & MCP Tools initialized successfully!")

    def check_ocr_availability(self):
        """Check if OCR (Tesseract) is available."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

    def get_available_models(self):
        """Check available models in Ollama."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            return []
        except Exception:
            return []

    def get_text_model(self):
        """Choose a text model"""
        if not self.available_models:
            return None
        for model in self.text_models:
            for available_model in self.available_models:
                if model in available_model:
                    return available_model
        return self.available_models[0]

    def get_multimodal_model(self):
        """Get available multimodal model for image analysis"""
        if not self.available_models:
            return None
        for model_pattern in self.multimodal_models:
            for available_model in self.available_models:
                if model_pattern in available_model.lower():
                    return available_model
        return None

    def detect_email_request(self, message):
        """Detect if user wants to send an email"""
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
        """Detect if user wants to process a PDF"""
        if not message:
            return False
            
        message_lower = message.lower()
        pdf_keywords = [
            'pdf', 'document', 'read pdf', 'analyze pdf', 'pdf summary',
            'extract from pdf', 'pdf main points', 'summarize pdf'
        ]
        
        return any(keyword in message_lower for keyword in pdf_keywords)

    def detect_code_request(self, message):
        """Detect if user is asking for code examples"""
        if not message:
            return False
            
        message_lower = message.lower()
        code_keywords = [
            'program', 'code', 'example', 'write a program', 'how to code',
            'implementation', 'function', 'class', 'script', 'algorithm',
            'switch case', 'if else', 'loop', 'function', 'method',
            'example code', 'sample code', 'code snippet', 'programming'
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
        """Detect if user is asking for news - ENHANCED WITH LIVE NEWS"""
        if not message:
            return False
            
        message_lower = message.lower()
        
        # News keywords
        news_keywords = [
            'news', 'headlines', 'breaking', 'current events', 'latest update',
            'today news', 'recent news', 'what\'s happening', 'current affairs',
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
        """Simplified and more reliable tool detection - ENHANCED WITH NEWS"""
        if not message:
            return None
            
        message_lower = message.lower().strip()
        
        # Priority-based detection
        if self.detect_email_request(message):
            return 'email'
        
        if self.detect_pdf_request(message):
            return 'pdf_analysis'
        
        # NEWS DETECTION - HIGH PRIORITY
        if self.detect_news_request(message):
            return 'news_search'
        
        # WEATHER - with more comprehensive patterns
        weather_keywords = [
            'weather', 'temperature', 'forecast', 'humid', 'wind', 
            'degrees', 'celcius', 'fahrenheit'
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
            r'calculate\s+\d+',
            r'compute\s+\d+', 
            r'what is \d+\s*[\+\-\*\/]\s*\d+',
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
        """Extract parameters for different tools - ENHANCED WITH NEWS"""
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
            math_match = re.search(r'(\d+[\+\-\*\/\d\.\(\) ]+)', message)
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
            # Basic unit conversion parameters
            return {'value': '1', 'from_unit': 'celsius', 'to_unit': 'fahrenheit'}
        
        return {}

    def handle_news_request(self, parameters):
        """Handle news requests using live_news.py"""
        try:
            query = parameters.get('query', 'latest news')
            country = parameters.get('country', 'india')
            
            print(f"📰 Fetching news for: {query} (country: {country})")
            
            # Use the live_news module
            if query == 'breaking news':
                news_result = fetch_breaking_news()
            else:
                news_result = fetch_live_news(query)
            
            # Format the response
            if news_result.startswith("❌"):
                return f"📰 **News Update**\n\n{news_result}\n\n*Please try again later or check your internet connection.*"
            else:
                return f"📰 **Live News Update**\n\n{news_result}\n\n*Stay informed with the latest developments from reliable news sources.*"
                
        except Exception as e:
            return f"📰 **News Service**\n\nUnable to fetch news at the moment. Error: {str(e)}\n\nPlease try again later."

    def handle_email_request(self, user_message):
        """Handle email composition and sending"""
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
        """Handle email composition and automatic sending with default credentials"""
        try:
            # Try to send automatically
            send_result = self.email_agent.send_email_auto(user_message)
            
            if "SUCCESS" in send_result:
                return f"Email Sent Successfully\n\n{send_result}"
            else:
                return f"Action Required\n\n{send_result}"
            
        except Exception as e:
            return f"Email processing error: {str(e)}"

    def process_pdf_content(self, pdf_data, user_message=""):
        """Process PDF and extract detailed content"""
        try:
            # Extract text from PDF
            extraction_result = self.pdf_processor.extract_text_from_pdf(pdf_data)
            
            if not extraction_result['success']:
                return f"PDF Error\n\n{extraction_result['error']}"
            
            # Analyze PDF structure with more detail
            structure = self.pdf_processor.analyze_pdf_structure(extraction_result['text'])
            extraction_result['structure'] = structure
            
            # Generate comprehensive report
            detailed_report = self.generate_detailed_pdf_summary(extraction_result, user_message)
            
            # Store PDF data for potential email sending
            self.current_pdf_data = extraction_result
            
            return detailed_report
            
        except Exception as e:
            return f"PDF Processing Error\n\n{str(e)}"

    def generate_detailed_pdf_summary(self, extraction_result, user_message):
        """Generate comprehensive PDF summary (100+ words)"""
        model = self.get_text_model()
        if not model:
            return self.pdf_processor.format_pdf_report(extraction_result)
        
        prompt = f"""
        Based on the following PDF content, provide a COMPREHENSIVE summary (100-200 words):

        PDF STRUCTURE:
        - Pages: {extraction_result.get('page_count', 'N/A')}
        - Sections: {len(extraction_result.get('structure', {}).get('sections', []))}
        - Key Topics: {extraction_result.get('structure', {}).get('key_topics', [])[:5]}

        CONTENT EXCERPT (first 1000 characters):
        {extraction_result['text'][:1000]}...

        User's specific interest: {user_message}

        Please provide a detailed summary covering:
        1. MAIN PURPOSE AND SCOPE (40-60 words)
        2. KEY FINDINGS OR ARGUMENTS (50-70 words) 
        3. IMPORTANT DETAILS AND EXAMPLES (40-60 words)
        4. OVERALL SIGNIFICANCE OR IMPLICATIONS (30-50 words)

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
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            if response.status_code == 200:
                detailed_summary = response.json().get('response', '')
                return f"Comprehensive PDF Analysis\n\n{detailed_summary}\n\n{self.pdf_processor.format_pdf_report(extraction_result)}"
            else:
                return self.pdf_processor.format_pdf_report(extraction_result)
        except:
            return self.pdf_processor.format_pdf_report(extraction_result)

    def handle_pdf_email_request(self, user_message, pdf_data):
        """Handle PDF analysis and email sending request"""
        try:
            # First process the PDF
            pdf_analysis = self.process_pdf_content(pdf_data, user_message)
            
            if pdf_analysis.startswith("PDF Error"):
                return pdf_analysis
            
            # Try to send email automatically
            send_result = self.email_agent.send_email_auto(user_message)
            
            if "SUCCESS" in send_result:
                return f"{pdf_analysis}\n\n{send_result}"
            else:
                return f"{pdf_analysis}\n\n{send_result}"
            
        except Exception as e:
            return f"Processing Error\n\n{str(e)}"

    def analyze_image_content(self, image_data, prompt="Describe this image in detail:"):
        """Analyze image content using multimodal model with detailed responses"""
        try:
            model = self.get_multimodal_model()
            if not model:
                return "Image analysis requires LLaVA model. Install with: ollama pull llava:7b"

            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Enhanced prompt for detailed image analysis
            detailed_prompt = """
            Provide a comprehensive and detailed description of this image (100-150 words). Include:

            1. MAIN SUBJECT AND SETTING (40-50 words):
            - Primary objects, people, or scenes
            - Environment and background details
            - Overall composition and framing

            2. VISUAL CHARACTERISTICS (30-40 words):
            - Colors, lighting, and mood
            - Style and artistic elements
            - Notable visual features

            3. CONTEXT AND INTERPRETATION (30-40 words):
            - Possible meaning or story
            - Cultural or historical context if apparent
            - Emotional impact or atmosphere

            4. DETAILED OBSERVATIONS (20-30 words):
            - Specific elements worth noting
            - Technical aspects if relevant
            - Unique or distinctive features

            Be thorough and descriptive in your analysis.
            """
            
            if prompt != "Describe this image in detail:":
                detailed_prompt = prompt + " " + detailed_prompt
            
            payload = {
                "model": model,
                "prompt": detailed_prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "num_predict": 500,  # Increased for detailed descriptions
                    "temperature": 0.4,
                    "top_k": 40
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', 'No detailed analysis received.')
                
                # Ensure sufficient detail
                if len(analysis.split()) < 80:
                    analysis = self.enhance_image_description(analysis, image_data, model)
                    
                return f"Detailed Image Analysis\n\n{analysis}"
            else:
                return "Unable to provide detailed image analysis at this time."
                
        except Exception as e:
            return f"Image analysis error: {str(e)}"

    def enhance_image_description(self, initial_description, image_data, model):
        """Enhance image description with more detail"""
        try:
            enhancement_prompt = f"""
            The following image description is too brief. Please expand it into a comprehensive analysis (100-150 words):

            Initial Description: {initial_description}

            Please provide more detail about:
            - Specific visual elements and their arrangement
            - Colors, textures, and lighting effects  
            - Composition and artistic techniques
            - Mood, atmosphere, and potential meaning
            - Notable details that make the image distinctive

            Expanded Detailed Analysis:
            """
            
            payload = {
                "model": model,
                "prompt": enhancement_prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "num_predict": 400,
                    "temperature": 0.5,
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get('response', initial_description)
            return initial_description
        except:
            return initial_description

    def create_contextual_response(self, user_message, tool_name, tool_result):
        """Create contextual responses for tools"""
        contextual_responses = {
            'weather': f"🌤️ **Weather Information**\n\n{tool_result}",
            'news_search': f"📰 **Live News Update**\n\n{tool_result}",
            'calculator': f"🧮 **Calculation Result**\n\n{tool_result}",
            'time': f"🕒 **Current Time**\n\n{tool_result}",
            'unit_converter': f"📏 **Unit Conversion**\n\n{tool_result}",
            'web_search': f"🔍 **Search Results**\n\n{tool_result}"
        }
        
        return contextual_responses.get(tool_name, tool_result)

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
            return image_data

    def generate_code_response(self, user_message):
        """Generate responses with actual code examples"""
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
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json().get('response', "I'll provide you with a complete code example.")
                return self.ensure_code_formatting(result)
            else:
                return "I can help with coding questions. Let me provide you with a complete code example."
        except:
            return "I understand you need code. Let me provide you with a working example."

    def ensure_code_formatting(self, text):
        """Ensure the response has proper code formatting"""
        # If no code blocks are present, try to add them
        if '```' not in text:
            # Look for code-like patterns and wrap them
            lines = text.split('\n')
            in_code_block = False
            code_lines = []
            formatted_lines = []
            
            for line in lines:
                # Detect start of code (indentation, keywords, etc.)
                if (re.match(r'^\s*(def |class |import |from |if |for |while |\w+\s*=)', line) and 
                    not in_code_block and len(line.strip()) > 10):
                    in_code_block = True
                    formatted_lines.append('```python')
                    code_lines = [line]
                elif in_code_block:
                    if line.strip() == '' or re.match(r'^\s', line) or re.match(r'^[#\w]', line.strip()):
                        code_lines.append(line)
                    else:
                        # End of code block
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
        """Generate detailed, comprehensive responses with memory context (100+ words)"""
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

        Provide a COMPREHENSIVE and DETAILED answer (minimum 100 words, ideally 150-200 words). Structure your response with:

        MAIN EXPLANATION (60-80 words):
        - Clear, thorough definition/explanation of the topic
        - Cover fundamental concepts and principles
        - Provide context and background information

        KEY ASPECTS (40-60 words):
        - 3-5 important characteristics or components
        - Practical implications or real-world applications
        - Current relevance or modern context

        PRACTICAL CONSIDERATIONS (30-50 words):
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
                "num_predict": 800,  # Increased for longer responses
                "temperature": 0.7,
                "top_k": 50,
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=45)
            if response.status_code == 200:
                result = response.json().get('response', "I understand your question. Let me provide detailed information about this topic.")
                
                # Ensure response is sufficiently detailed
                word_count = len(result.split())
                if word_count < 80:
                    # If response is too short, enhance it
                    enhancement_prompt = f"""
                    The following answer is too brief. Please expand it to be more comprehensive (100-200 words) while maintaining accuracy:

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
                    
                    enhancement_response = requests.post(self.ollama_url, json=enhancement_payload, timeout=30)
                    if enhancement_response.status_code == 200:
                        result = enhancement_response.json().get('response', result)
                
                return result
            else:
                return "I'd like to provide you with a comprehensive explanation. Let me share detailed information about this topic covering the key concepts, practical applications, and important considerations that will help you understand it thoroughly."
        except Exception as e:
            return f"I want to give you a detailed response about this topic. Let me explain the fundamental concepts, key aspects, and practical applications in a comprehensive manner that will help you gain a thorough understanding of the subject matter."

    def send_message_with_image_and_pdf(self, message, image_data=None, pdf_data=None):
        """Main message processing with detailed responses and proper tool integration"""
        try:
            final_response = ""
            tool_used = None
            
            # Case 1: PDF processing
            if pdf_data:
                if self.detect_email_request(message):
                    final_response = self.handle_pdf_email_request(message, pdf_data)
                    tool_used = "pdf_email"
                else:
                    final_response = self.process_pdf_content(pdf_data, message)
                    tool_used = "pdf_analysis"

            # Case 2: Image processing
            elif image_data:
                multimodal_model = self.get_multimodal_model()
                
                if multimodal_model:
                    optimized_image = self.optimize_image(image_data)
                    
                    if message and message.strip():
                        analysis_prompt = message
                    else:
                        analysis_prompt = "Describe this image in detail:"
                    
                    analysis_result = self.analyze_image_content(optimized_image, analysis_prompt)
                    final_response = analysis_result
                    tool_used = "image_analysis"
                else:
                    final_response = "Image analysis requires LLaVA model. Install with: ollama pull llava:7b"
                    tool_used = "image_analysis"

            # Case 3: Tool detection and usage - ENHANCED WITH LIVE NEWS
            elif message and message.strip():
                tool_name = self.detect_tool_usage(message)
                print(f"🔧 Detected tool: {tool_name} for message: '{message}'")
                
                if tool_name:
                    if tool_name == 'email':
                        final_response = self.handle_email_auto_send(message)
                        tool_used = "email"
                    elif tool_name == 'pdf_analysis':
                        final_response = "I can analyze PDF documents. Please upload a PDF file."
                        tool_used = "pdf_analysis"
                    elif tool_name == 'news_search':
                        # USE LIVE NEWS MODULE
                        parameters = self.extract_tool_parameters(tool_name, message)
                        print(f"📰 Calling Live News with params: {parameters}")
                        final_response = self.handle_news_request(parameters)
                        tool_used = "news_search"
                    else:
                        # EXTRACT PARAMETERS AND CALL MCP TOOL
                        parameters = self.extract_tool_parameters(tool_name, message)
                        print(f"📋 Calling MCP tool {tool_name} with params: {parameters}")
                        
                        # THIS IS WHERE MCP TOOL IS CALLED
                        tool_result = self.mcp_client.call_tool(tool_name, parameters)
                        final_response = self.create_contextual_response(message, tool_name, tool_result)
                        tool_used = tool_name
                        
                        print(f"✅ MCP tool response received: {tool_name}")
                else:
                    # Generate detailed response for general queries
                    final_response = self.generate_concise_response(message)
                    tool_used = "conversation"

            # Case 4: No message
            else:
                if len(self.memory.conversation_metadata) > 0:
                    final_response = "What would you like to know more about? I'm ready to provide you with detailed explanations and comprehensive information on any topic you're interested in exploring further."
                else:
                    final_response = """🤖 **AI Assistant - Your Comprehensive Knowledge Partner**

I'm designed to provide you with detailed, comprehensive responses (100+ words) and can also help with:

📰 **LIVE NEWS UPDATES:**
- Breaking news and global headlines
- Country-specific news (India, USA, UK, etc.)
- Real-time news from reliable sources
- Current events and developments

🌤️ **REAL-TIME TOOLS:**
- Weather forecasts for any location
- Mathematical calculations
- Time zone information
- Unit conversions

📚 **INFORMATION & ANALYSIS:**
- Detailed explanations of complex concepts
- PDF document analysis and summarization
- Image analysis and description
- Code examples and programming help
- Email composition and sending

💡 **Just ask me anything!** I'll provide thorough, well-structured answers with plenty of detail and context.

What would you like to explore today?"""
                tool_used = "greeting"

            # Store in LangChain memory
            user_input = message or "[File Upload]" 
            if pdf_data:
                user_input += " (PDF)"
            elif image_data:
                user_input += " (Image)"
                
            self.memory.add_interaction(user_input, final_response, tool_used)
            
            return final_response
                
        except Exception as e:
            error_msg = f"Service temporarily unavailable. Error: {str(e)}"
            print(f"❌ Error in send_message: {str(e)}")
            self.memory.add_interaction(message, error_msg, "error")
            return error_msg

    # Backward compatibility method
    def send_message_with_image(self, message, image_data=None):
        return self.send_message_with_image_and_pdf(message, image_data, None)
    
    # New methods for memory management
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

# Test function to verify Live News integration
def test_live_news_integration():
    """Test that Live News is properly integrated"""
    bot = EnhancedChatbot()
    
    test_messages = [
        "latest news from India",
        "breaking news",
        "what's happening in USA",
        "UK news today",
        "weather in London",
        "calculate 25 * 4 + 15"
    ]
    
    print("🧪 Testing Live News Integration...")
    print("=" * 70)
    
    for message in test_messages:
        print(f"💬 User: {message}")
        tool = bot.detect_tool_usage(message)
        print(f"🔧 Detected Tool: {tool}")
        
        if tool == 'news_search':
            params = bot.extract_tool_parameters(tool, message)
            print(f"📰 News Parameters: {params}")
            
            # Test news request
            try:
                result = bot.handle_news_request(params)
                print(f"✅ News Result Preview: {result[:200]}...")
            except Exception as e:
                print(f"❌ News Error: {e}")
        elif tool and tool not in ['email', 'pdf_analysis']:
            params = bot.extract_tool_parameters(tool, message)
            print(f"📋 Parameters: {params}")
        else:
            print("ℹ️  No special tool detected")
        
        print("-" * 70)

if __name__ == "__main__":
    test_live_news_integration()