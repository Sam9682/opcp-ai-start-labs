"""Application entry point"""
import os
from src.app import create_app
from src.config import PORT

def main():
    """Main entry point"""
    # Create Flask app
    app = create_app()
    
    # Run application
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=os.environ.get('FLASK_ENV') == 'development'
    )

if __name__ == '__main__':
    main()
