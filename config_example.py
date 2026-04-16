#config.py

import os

class config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('mysql+pymysql://neuroqc_user:YOUR_PASSWORD_HERE@localhost/neuroqc_db')

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
    

