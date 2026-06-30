"""Main Flask application"""
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from .config import SECRET_KEY, USER_ID, USER_NAME, USER_EMAIL, DESCRIPTION, PORT
from .database import init_db, log_page_visit, end_page_visit, get_user_usage
import uuid
import time

def create_app():
    """Application factory"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = SECRET_KEY
    
    # Initialize database
    init_db()
    
    # Configure CORS
    CORS(app, supports_credentials=True)
    
    @app.before_request
    def before_request():
        """Track page visits for billing"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        if request.endpoint and not request.path.startswith('/static'):
            session['visit_id'] = log_page_visit(USER_ID, session['session_id'], request.path)
            session['visit_start'] = time.time()
    
    @app.after_request
    def after_request(response):
        """End page visit tracking"""
        if 'visit_id' in session:
            end_page_visit(session['visit_id'])
        return response
    
    @app.route('/')
    def index():
        """Main page displaying user information"""
        from flask import request
        user_id_param = request.args.get('user_id')
        show_admin = user_id_param is not None
        
        user_info = {
            'id': USER_ID,
            'name': USER_NAME,
            'email': USER_EMAIL,
            'description': DESCRIPTION,
            'port': PORT
        }
        return render_template('index.html', user=user_info, show_admin=show_admin)
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'user_id': USER_ID})
    
    @app.route('/api/info')
    def api_info():
        """API endpoint returning user information"""
        return jsonify({
            'user_id': USER_ID,
            'name': USER_NAME,
            'email': USER_EMAIL,
            'description': DESCRIPTION,
            'port': PORT
        })
    
    @app.route('/admin')
    def admin():
        """Admin panel for website management"""
        return render_template('admin.html', user={'name': USER_NAME})
    
    @app.route('/admin/upload', methods=['POST'])
    def upload_website():
        """Handle website zip upload"""
        import os
        import zipfile
        from datetime import datetime
        from flask import request, flash, redirect, url_for
        
        if 'website' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['website']
        if file.filename == '' or not file.filename.endswith('.zip'):
            return jsonify({'error': 'Please upload a zip file'}), 400
        
        # Create timestamped directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        website_dir = f'/var/www/web_site_source_{timestamp}'
        os.makedirs(website_dir, exist_ok=True)
        
        # Extract zip file
        zip_path = f'/tmp/website_{timestamp}.zip'
        file.save(zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(website_dir)
        
        # Update symlink to point to new version
        html_link = '/var/www/html'
        if os.path.islink(html_link):
            os.unlink(html_link)
        elif os.path.exists(html_link):
            os.rename(html_link, f'/var/www/html_backup_{timestamp}')
        
        os.symlink(website_dir, html_link)
        os.remove(zip_path)
        
        return jsonify({'success': True, 'version': timestamp})
    
    @app.route('/billing')
    def billing():
        """Billing and usage page"""
        user_id_param = request.args.get('user_id', USER_ID)
        usage_data = get_user_usage(user_id_param)
        return render_template('billing.html', usage=usage_data, user_id=user_id_param)
    
    @app.route('/api/usage/<user_id>')
    def api_usage(user_id):
        """API endpoint for usage data"""
        days = request.args.get('days', 30, type=int)
        usage_data = get_user_usage(user_id, days)
        return jsonify(usage_data)
    
    return app
