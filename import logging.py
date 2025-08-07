import logging
from flask import Flask, request, jsonify
from bot import TradingBot

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app and trading bot
app = Flask(__name__)
trading_bot = TradingBot()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Not found: {request.method} {request.path}")
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

# Log all requests
@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.path}")

# Routes
@app.route('/')
def home():
    return jsonify({
        "status": "online", 
        "message": "Crypto trading bot API is running"
    })

@app.route('/bot/start', methods=['POST'])
def start_bot():
    result = trading_bot.start()
    return jsonify({"status": "success", "message": result})

@app.route('/bot/stop', methods=['POST'])
def stop_bot():
    result = trading_bot.stop()
    return jsonify({"status": "success", "message": result})

@app.route('/bot/status', methods=['GET'])
def bot_status():
    status = trading_bot.get_status()
    return jsonify(status)

# Run the application
if __name__ == '__main__':
    logger.info("Starting the crypto trading bot API")
    app.run(host='0.0.0.0', port=8000, debug=False)
