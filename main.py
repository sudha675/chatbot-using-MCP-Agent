# main.py
from flask import Flask, render_template, request, jsonify
import uuid
import logging
import os
import base64
import io
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules
from enhanced_chatbot import EnhancedChatbot

# Load environment variables
load_dotenv()

# Setup Flask & Logging
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-for-chatbot-session')

# Store conversations
conversations = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint with enhanced image and PDF support"""
    try:
        data = request.json
        msg = data.get("message", "").strip()
        img = data.get("image", "")
        pdf = data.get("pdf", "")
        cid = data.get("conversation_id", "")
        
        logging.info(f"Chat request - Message: {msg[:100]}, Image: {'Yes' if img else 'No'}, PDF: {'Yes' if pdf else 'No'}")
        
        if not msg and not img and not pdf:
            return jsonify({"error": "Please provide a message or upload a file."}), 400
        
        if not cid:
            cid = str(uuid.uuid4())
            
        if cid not in conversations:
            conversations[cid] = {
                "chatbot": EnhancedChatbot(), 
                "history": [],
                "created_at": datetime.now().isoformat()
            }

        bot = conversations[cid]["chatbot"]
        
        # Process the message with enhanced chatbot
        reply = bot.send_message_with_image_and_pdf(msg, img, pdf)

        # Store in conversation history
        conversation_entry = {
            "user": msg or ("[PDF Upload]" if pdf else "[Image Upload]" if img else "[Empty]"),
            "assistant": reply,
            "timestamp": datetime.now().isoformat(),
            "has_image": bool(img),
            "has_pdf": bool(pdf)
        }
        
        conversations[cid]["history"].append(conversation_entry)
        
        logging.info("Response generated successfully")
        
        return jsonify({
            "response": reply, 
            "conversation_id": cid
        })
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({"error": "Service error. Please try again."}), 500

@app.route("/send_email", methods=["POST"])
def send_email():
    """Send email with SMTP credentials"""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        smtp_username = data.get("smtp_username", "")
        smtp_password = data.get("smtp_password", "")
        user_message = data.get("user_message", "")
        
        logging.info(f"Sending email with custom credentials for conversation: {cid}")
        
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
            
        if not smtp_username or not smtp_password:
            return jsonify({"error": "SMTP credentials required."}), 400
            
        if not user_message:
            return jsonify({"error": "User message required."}), 400
            
        bot = conversations[cid]["chatbot"]
        
        # Send the email
        success, result = bot.email_agent.send_email({
            'recipient_email': smtp_username,  # Using username as recipient for demo
            'subject': 'Email from AI Assistant',
            'body': user_message
        }, smtp_username, smtp_password)
        
        if success:
            email_sent_message = f"EMAIL SENT SUCCESSFULLY!\n\nTo: {smtp_username}\n\nYour email has been delivered successfully."
            
            conversations[cid]["history"].append({
                "user": user_message,
                "assistant": email_sent_message,
                "timestamp": datetime.now().isoformat(),
                "is_email": True
            })
            
            logging.info(f"Email sent successfully to {smtp_username}")
            
            return jsonify({
                "status": "success",
                "message": email_sent_message,
                "conversation_id": cid
            })
        else:
            logging.error(f"Email sending failed: {result}")
            return jsonify({
                "status": "error",
                "error": result
            }), 500
            
    except Exception as e:
        logging.error(f"Email sending error: {e}")
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

@app.route("/send_email_auto", methods=["POST"])
def send_email_auto():
    """Send email automatically using default credentials"""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        user_message = data.get("user_message", "")
        
        logging.info(f"Auto-sending email for conversation: {cid}")
        
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
            
        if not user_message:
            return jsonify({"error": "User message required."}), 400
            
        bot = conversations[cid]["chatbot"]
        
        # Use the enhanced auto-send method
        result = bot.email_agent.send_email_auto(user_message)

        # Update conversation history
        conversations[cid]["history"].append({
            "user": user_message,
            "assistant": result,
            "timestamp": datetime.now().isoformat(),
            "is_email": True
        })
        
        logging.info(f"Auto-email result: {result[:100]}...")
        
        return jsonify({
            "status": "success",
            "message": result,
            "conversation_id": cid
        })
            
    except Exception as e:
        logging.error(f"Auto email sending error: {e}")
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

@app.route("/new_chat", methods=["POST"])
def new_chat():
    """Start a new conversation."""
    try:
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = {
            "chatbot": EnhancedChatbot(), 
            "history": [],
            "created_at": datetime.now().isoformat()
        }
        
        logging.info(f"New conversation started: {conversation_id}")
        
        return jsonify({
            "conversation_id": conversation_id,
            "message": "New conversation started successfully"
        })
    except Exception as e:
        logging.error(f"New chat error: {e}")
        return jsonify({"error": "Failed to start new conversation"}), 500

@app.route("/conversation_history", methods=["POST"])
def conversation_history():
    """Get conversation history"""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
            
        history = conversations[cid]["history"]
        
        return jsonify({
            "status": "success",
            "history": history,
            "conversation_id": cid,
            "total_messages": len(history)
        })
            
    except Exception as e:
        logging.error(f"Get history error: {e}")
        return jsonify({"error": f"Failed to get history: {str(e)}"}), 500

@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    """Clear conversation memory"""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
            
        bot = conversations[cid]["chatbot"]
        result = bot.clear_memory()
        
        # Also clear local history
        conversations[cid]["history"] = []
        
        logging.info(f"Memory cleared for conversation: {cid}")
        
        return jsonify({
            "status": "success",
            "message": result,
            "conversation_id": cid
        })
            
    except Exception as e:
        logging.error(f"Clear memory error: {e}")
        return jsonify({"error": f"Failed to clear memory: {str(e)}"}), 500

@app.route("/system_status", methods=["GET"])
def system_status():
    """Comprehensive system status check"""
    try:
        test_bot = EnhancedChatbot()
        
        # Get detailed Ollama status
        ollama_status = test_bot.diagnose_ollama_status()
        
        status_report = {
            "ollama_connection": ollama_status.get('ollama_running', False),
            "available_models": len(test_bot.available_models),
            "multimodal_available": ollama_status.get('multimodal_available', False),
            "vision_model": test_bot.get_multimodal_model(),
            "text_model": test_bot.get_text_model(),
            "image_analysis": test_bot.get_multimodal_model() is not None,
            "ocr_available": test_bot.ocr_available,
            "active_conversations": len(conversations),
            "server_time": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "System status report",
            "components": status_report,
            "ollama_details": ollama_status
        })
    except Exception as e:
        return jsonify({
            "status": "Status check failed",
            "error": str(e)
        }), 500

@app.route("/test_ollama", methods=["GET"])
def test_ollama():
    """Test Ollama connection"""
    try:
        import requests
        res = requests.get("http://localhost:11434/api/tags", timeout=10)
        if res.status_code == 200:
            models = [m['name'] for m in res.json().get('models', [])]
            return jsonify({
                "status": "Ollama running", 
                "models": models,
                "total_models": len(models)
            })
        return jsonify({"status": "Ollama error"}), 500
    except Exception as e:
        return jsonify({
            "status": "Ollama unavailable", 
            "error": str(e)
        }), 500

if __name__ == "__main__":
    print("AI Assistant Server Starting...")
    print("Web Interface: http://localhost:5000")
    print("")
    
    # Initialize a test bot to check system status
    try:
        test_bot = EnhancedChatbot()
        status = test_bot.diagnose_ollama_status()
        
        print("Initial System Check:")
        print(f"  Ollama Running: {status.get('ollama_running', False)}")
        print(f"  Available Models: {status.get('total_models', 0)}")
        print(f"  Vision Model Available: {status.get('multimodal_available', False)}")
        print(f"  OCR Available: {test_bot.ocr_available}")
        
        if status.get('multimodal_available'):
            vision_model = test_bot.get_multimodal_model()
            print(f"  Vision Model: {vision_model}")
        else:
            print("  Image Analysis: Install vision model with: ollama pull granite3.2-vision:latest")
            
        if test_bot.ocr_available:
            print("  OCR Text Extraction: Ready")
        else:
            print("  OCR Text Extraction: Install Tesseract OCR")
            
    except Exception as e:
        print(f"  System check failed: {e}")
    
    print("")
    print("Starting Flask server...")
    
    # Get host and port from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(debug=True, host=host, port=port)