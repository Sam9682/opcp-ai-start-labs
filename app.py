"""Flask application entry point for AI Store Labs."""

from flask import Flask, jsonify, send_from_directory
from src.api import lab_routes

app = Flask(__name__, static_folder='skillhub')


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/')
@app.route('/<path:path>')
def serve_skillhub(path='index.html'):
    """Serve SkillHub static files."""
    return send_from_directory(app.static_folder, path)


# Register API blueprint
app.register_blueprint(lab_routes, url_prefix='/api')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
