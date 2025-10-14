# main.py
from flask import Flask, render_template, request, jsonify
import uuid
import logging
import os
from dotenv import load_dotenv

# Import our custom modules
from enhanced_chatbot import EnhancedChatbot

# Load environment variables
load_dotenv()

# --------------------------
# Setup Flask & Logging
# --------------------------
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = 'dev-key-for-chatbot-session'

conversations = {}

# ============================================================
#                   FLASK ROUTES
# ============================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        msg = data.get("message", "").strip()
        img = data.get("image", "")
        pdf = data.get("pdf", "")
        cid = data.get("conversation_id", "")
        
        if not msg and not img and not pdf:
            return jsonify({"error": "Please provide a message or upload a file."}), 400
        
        if not cid:
            cid = str(uuid.uuid4())
            
        if cid not in conversations:
            conversations[cid] = {"chatbot": EnhancedChatbot(), "history": []}

        bot = conversations[cid]["chatbot"]
        reply = bot.send_message_with_image_and_pdf(msg, img, pdf)

        conversations[cid]["history"].append({
            "user": msg or ("[PDF Upload]" if pdf else "[Image Uploaded]"), 
            "assistant": reply
        })
        
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
        
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
            
        if not smtp_username or not smtp_password:
            return jsonify({"error": "SMTP credentials required."}), 400
            
        bot = conversations[cid]["chatbot"]
        
        # Extract email info from the original message
        email_info = bot.email_agent.extract_email_info(user_message)
        email_data = bot.email_agent.compose_email(email_info)
        
        # Send the email
        success, result = bot.email_agent.send_email(email_data, smtp_username, smtp_password)
        
        if success:
            # Update conversation history
            email_sent_message = f"✅ **Email Sent**\n\nTo: {email_data['recipient_email']}\nSubject: {email_data['subject']}\n\nMessage delivered successfully."
            
            conversations[cid]["history"].append({
                "user": user_message,
                "assistant": email_sent_message
            })
            
            return jsonify({
                "status": "success",
                "message": email_sent_message,
                "conversation_id": cid
            })
        else:
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
        
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
            
        if not user_message:
            return jsonify({"error": "User message required."}), 400
            
        bot = conversations[cid]["chatbot"]
        
        # Use the auto-send method
        result = bot.handle_email_auto_send(user_message)

        # Update conversation history
        conversations[cid]["history"].append({
            "user": user_message,
            "assistant": result
        })
        
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
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = {"chatbot": EnhancedChatbot(), "history": []}
    return jsonify({"conversation_id": conversation_id})

@app.route("/test_tools")
def test_tools():
    """Test all MCP tools"""
    try:
        test_bot = EnhancedChatbot()
        
        tests = [
            ("weather", "What's the weather in London?"),
            ("news_search", "latest technology news"),
            ("calculator", "Calculate 15 * 25 + 8"),
            ("time", "Current time in Tokyo"),
            ("email", "Send email to test@example.com")
        ]
        
        results = {}
        for tool_name, query in tests:
            tool_name_detected = test_bot.detect_tool_usage(query)
            if tool_name_detected == tool_name:
                if tool_name == 'email':
                    preview = test_bot.handle_email_request(query)
                    results[tool_name] = f"✅ Email detected\n{preview[:150]}..."
                else:
                    results[tool_name] = f"✅ {tool_name} tool available"
            else:
                results[tool_name] = f"❌ Tool detection failed"
        
        return jsonify({
            "status": "Tools test completed",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "status": "Tools test failed",
            "error": str(e)
        }), 500

@app.route("/test_ollama")
def test_ollama():
    """Test Ollama connection"""
    try:
        import requests
        res = requests.get("http://localhost:11434/api/tags", timeout=10)
        if res.status_code == 200:
            models = [m['name'] for m in res.json().get('models', [])]
            return jsonify({
                "status": "Ollama running", 
                "models": models
            })
        return jsonify({"status": "Ollama error"}), 500
    except Exception as e:
        return jsonify({
            "status": "Ollama unavailable", 
            "error": str(e)
        }), 500

@app.route("/test_email")
def test_email():
    """Test email functionality"""
    try:
        test_bot = EnhancedChatbot()
        
        test_messages = [
            "send email to test@example.com about meeting",
            "write a mail to friend@gmail.com invite for birthday"
        ]
        
        results = {}
        for i, message in enumerate(test_messages):
            tool_detected = test_bot.detect_tool_usage(message)
            preview = test_bot.handle_email_request(message)
            results[f"test_{i+1}"] = f"Tool: {tool_detected}\n{preview[:200]}..."
        
        return jsonify({
            "status": "Email test completed",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "status": "Email test failed",
            "error": str(e)
        }), 500

@app.route("/system_status")
def system_status():
    """Comprehensive system status check"""
    try:
        test_bot = EnhancedChatbot()
        
        status_report = {
            "ollama_connection": len(test_bot.available_models) > 0,
            "email_service": True,
            "pdf_processing": True,
            "image_analysis": test_bot.get_multimodal_model() is not None,
            "active_conversations": len(conversations)
        }
        
        return jsonify({
            "status": "System status report",
            "components": status_report,
            "active_models": test_bot.available_models
        })
    except Exception as e:
        return jsonify({
            "status": "Status check failed",
            "error": str(e)
        }), 500

# ============================================================
#                   START SERVER
# ============================================================
if __name__ == "__main__":
    print("🚀 AI Assistant Server Starting...")
    print("📍 Web Interface: http://localhost:5000")
    print("🔧 Test Endpoints:")
    print("   /test_tools - Test all tools")
    print("   /test_ollama - Check models")
    print("   /test_email - Test email system")
    print("   /system_status - System health")
    print("")
    print("🛠️ Available Services:")
    print("• Chat & information")
    print("• PDF analysis")
    print("• Email composition")
    print("• Image analysis")
    print("• Weather, news, calculations")
    print("")
    app.run(debug=True, host="0.0.0.0", port=5000)