from flask import Flask, render_template, request, jsonify
import uuid
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from enhanced_chatbot import EnhancedChatbot

load_dotenv()

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-for-chatbot-session')

conversations = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint with image support."""
    try:
        data = request.json
        msg = data.get("message", "").strip()
        img = data.get("image", "")
        cid = data.get("conversation_id", "")

        logging.info(f"Chat request - Message: {msg[:100]}, Image: {'Yes' if img else 'No'}")

        if not msg and not img:
            return jsonify({"error": "Please provide a message or upload an image."}), 400

        if not cid:
            cid = str(uuid.uuid4())

        if cid not in conversations:
            conversations[cid] = {
                "chatbot": EnhancedChatbot(),
                "history": [],
                "created_at": datetime.now().isoformat()
            }

        bot = conversations[cid]["chatbot"]
        reply = bot.send_message_with_image(msg, img)

        conversations[cid]["history"].append({
            "user": msg or "[Image Upload]",
            "assistant": reply,
            "timestamp": datetime.now().isoformat(),
            "has_image": bool(img)
        })

        return jsonify({"response": reply, "conversation_id": cid})
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({"error": "Service error. Please try again."}), 500

@app.route("/send_email_auto", methods=["POST"])
def send_email_auto():
    """Send email automatically using default credentials."""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        user_message = data.get("user_message", "")

        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
        if not user_message:
            return jsonify({"error": "User message required."}), 400

        bot = conversations[cid]["chatbot"]
        result = bot.email_agent.send_email_auto(user_message)

        conversations[cid]["history"].append({
            "user": user_message,
            "assistant": result,
            "timestamp": datetime.now().isoformat(),
            "is_email": True
        })

        return jsonify({"status": "success", "message": result, "conversation_id": cid})
    except Exception as e:
        logging.error(f"Auto email error: {e}")
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

@app.route("/new_chat", methods=["POST"])
def new_chat():
    """Start a new conversation."""
    try:
        cid = str(uuid.uuid4())
        conversations[cid] = {
            "chatbot": EnhancedChatbot(),
            "history": [],
            "created_at": datetime.now().isoformat()
        }
        return jsonify({"conversation_id": cid, "message": "New conversation started"})
    except Exception as e:
        logging.error(f"New chat error: {e}")
        return jsonify({"error": "Failed to start new conversation"}), 500

@app.route("/conversation_history", methods=["POST"])
def conversation_history():
    """Get conversation history."""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
        return jsonify({
            "status": "success",
            "history": conversations[cid]["history"],
            "conversation_id": cid
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    """Clear conversation memory."""
    try:
        data = request.json
        cid = data.get("conversation_id", "")
        if not cid or cid not in conversations:
            return jsonify({"error": "Invalid conversation ID."}), 400
        bot = conversations[cid]["chatbot"]
        result = bot.clear_memory()
        conversations[cid]["history"] = []
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/system_status", methods=["GET"])
def system_status():
    """System status check."""
    try:
        test_bot = EnhancedChatbot()
        ollama_status = test_bot.diagnose_ollama_status()
        return jsonify({
            "ollama_connection": ollama_status.get('ollama_running', False),
            "available_models": len(test_bot.available_models),
            "multimodal_available": ollama_status.get('multimodal_available', False),
            "vision_model": test_bot.get_multimodal_model(),
            "text_model": test_bot.get_text_model(),
            "ocr_available": test_bot.ocr_available,
            "active_conversations": len(conversations)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test_ollama", methods=["GET"])
def test_ollama():
    """Test Ollama connection."""
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=10)
        if res.status_code == 200:
            models = [m['name'] for m in res.json().get('models', [])]
            return jsonify({"status": "Ollama running", "models": models})
        return jsonify({"status": "Ollama error"}), 500
    except Exception as e:
        return jsonify({"status": "Ollama unavailable", "error": str(e)}), 500

if __name__ == "__main__":
    print("AI Assistant Server Starting...")
    print("Web Interface: http://localhost:5000")
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=True, host=host, port=port)