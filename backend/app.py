# backend/app.py
# Add these imports
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import os
from api.chat_routes import chat_bp
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
app.config.from_object(Config)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/api')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Add a global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({
        "error": "An unexpected error occurred",
        "message": str(e)
    }), 500

if __name__ == '__main__':
    logger.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
