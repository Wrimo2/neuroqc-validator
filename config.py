#config.py

import os

class config:   
    #read database url from environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') #changed at phase 6
    
    if not SQLALCHEMY_DATABASE_URI: #created at phase 6
        raise RecursionError(
            "DATABASE_URL environment variable is not set. Copy .env.example to .env (locally) or set it in your PythonAnywhere environment (production)"
        )
    #SQLALCHEMY SETTING
    SQLALCHEMY_TRACK_MODIFICATION = False

    #FILE UPLOAD SETTING
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  #16MB max upload limit

    #VALIDATION THRESHOLD
    OCR_HIGH_CONFIDENCE = 0.95
    OCR_LOW_CONFIDENCE = 0.85
    FUZZY_MATCH_THRESHOLD = 85
    ICD_EDIT_DISTANCE_MAX = 2

    #a secret key for Flask sessions. Also from environment. 
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-only-change-me') #changed at phase 6
    

