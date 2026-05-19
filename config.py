import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Model paths
MODEL_PATHS = {
    'normal_tc': r"D:\hadeer_FP\classifier_models\normal_tc.keras",
    'early_vs_late': r"D:\hadeer_FP\classifier_models\resnet_early_vs_late.keras"
}

# Flask configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True for HTTPS in production
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)