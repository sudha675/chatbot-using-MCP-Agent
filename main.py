from flask import Flask, render_template, request, jsonify
import uuid
import logging
from enhanced_chatbot import EnhancedChatbot

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
        cid = data.get("conversation_id", "")
        
        if not msg and not img:
            return jsonify({"error": "Please enter a message or upload an image"}), 400
        
        if not cid:
            cid = str(uuid.uuid4())
            
        if cid not in conversations:
            conversations[cid] = {"chatbot": EnhancedChatbot(), "history": []}

        bot = conversations[cid]["chatbot"]
        reply = bot.send_message_with_image(msg, img)

        conversations[cid]["history"].append({
            "user": msg or "[Image Uploaded]", 
            "assistant": reply
        })
        
        return jsonify({
            "response": reply, 
            "conversation_id": cid
        })
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({"error": "Internal server error"}), 500

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
            ("time", "Current time in Tokyo")
        ]
        
        results = {}
        for tool_name, query in tests:
            tool_name_detected = test_bot.detect_tool_usage(query)
            if tool_name_detected == tool_name:
                parameters = test_bot.extract_tool_parameters(tool_name, query)
                result = test_bot.mcp_client.call_tool(tool_name, parameters)
                results[tool_name] = result[:200] + "..." if len(result) > 200 else result
            else:
                results[tool_name] = f"❌ Tool detection failed for {tool_name}"
        
        return jsonify({
            "status": "✅ MCP Tools Test",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "status": "❌ Tools test failed",
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
                "status": "✅ Ollama is running", 
                "models": models
            })
        return jsonify({"status": "❌ Ollama error"}), 500
    except Exception as e:
        return jsonify({
            "status": "❌ Cannot connect to Ollama", 
            "error": str(e)
        }), 500

# ============================================================
#                   START SERVER
# ============================================================
if __name__ == "__main__":
    print("🚀 Starting ENHANCED AI Chatbot with MCP Tools...")
    print("📍 Access at: http://localhost:5000")
    print("🔧 Test Tools: http://localhost:5000/test_tools")
    print("🤖 Test Ollama: http://localhost:5000/test_ollama")
    print("")
    print("🛠️  AVAILABLE MCP TOOLS:")
    print("• 🌤️  Real-time weather data")
    print("• 📰 Live news search (NewsAPI + Google RSS)")
    print("• 🔢 Calculator and math solver")
    print("• 🕒 Timezone-aware time")
    print("• 🖼️ Image analysis")
    print("• 📐 Unit converter")
    print("")
    app.run(debug=True, host="0.0.0.0", port=5000)