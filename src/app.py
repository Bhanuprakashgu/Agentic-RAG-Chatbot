import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import Config
from routes.chatbot import chatbot_bp 

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

# CORS enabled for all routes
CORS(app)

# ✅ Register chatbot route only
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

# ✅ Serve static files
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return "index.html not found", 404

# ✅ Run the app
if __name__ == '__main__':
    print("🚀 Starting RAG Chatbot Flask Application...")
    print("✅ Local LLM is active with optional RAG support")
    print("🌐 Visit: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
