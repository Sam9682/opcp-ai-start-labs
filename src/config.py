"""Configuration settings for AI-StaticWebsite"""
import os

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

# User information from environment
USER_ID = os.environ.get('USER_ID', '1')
USER_NAME = os.environ.get('USER_NAME', 'User')
USER_EMAIL = os.environ.get('USER_EMAIL', 'user@example.com')
DESCRIPTION = os.environ.get('DESCRIPTION', 'Basic Information Display')
PORT = int(os.environ.get('PORT', '6001'))

