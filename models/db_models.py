#db_models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#-----------REFERENCE TABLES------------
class ReferenceICD10(db.Model):
    __tablename__ = 'reference_icd10_codes'
    id = db.Column(db.Integer, primary_key= True)
    code = db.Column(db.String(10), unique = True, nullable = False, index = True)
    description = db.Column(db.Text)
    category = db.Column(db.String(255))

class ReferenceMedication(db.Model):
    __tablename__ = 'reference_medications'
    id = db.Column(db.Integer, primary_key = True)
    drug_name = db.Column(db.String(200), nullable = False, index = True)
    drug_class = db.Column(db.String(100))
    common_dosages = db.Column(db.String(500))


class ReferenceVitaRange(db.Model):
    __tablename__ = 'reference_vital_ranges'
    id = db.Column(db.Integer, primary_key = True)
    vital_name = db.Column(db.String(20), unique = True, nullable = False)
    min_value = db.Column(db.Float, nullable = False)
    max_value = db.Column(db.Float, nullable = False)
    unit = db.Column(db.String(20))

#-------------OPERATIONAL TABLES----------------

class QCBatch(db.Model):
    __tablename__ = 'qc_batches'
    id = db.Column(db.Integer, primary_key = True)  
    filename = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default = datetime.utcnow)
    total_records = db.Column(db.Integer, default = 0)
    pass_count = db.Column(db.Integer, default = 0)
    warning_count = db.Column(db.Integer, default = 0)
    fail_count = db.Column(db.Integer, default = 0)
    results = db.relationship('QCResult', backref ='batch', lazy = True, cascade = 'all, delete-orphan')

class QCResult(db.Model):
    __tablename__ = 'qc_results'
    id = db.Column(db.Integer, primary_key = True)
    batch_id = db.Column(db.Integer, db.ForeignKey('qc_batches.id'))
    patient_id = db.Column(db.String(50))
    overall_status = db.Column(db.String(10))
    ocr_confidence = db.Column(db.Float)
    error_summary = db.Column(db.JSON)
    errors = db.relationship('QCErrorDetail', backref = 'result', lazy = True, cascade = 'all, delete-orphan')
    
class QCErrorDetail(db.Model):
    __tablename__ = 'qc_error_details'
    id = db.Column(db.Integer, primary_key = True)
    result_id = db.Column(db.Integer, db.ForeignKey('qc_results.id'))
    error_category = db.Column(db.String(20))
    severity = db.Column(db.String(10))
    field_name = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    suggestion = db.Column(db.Text)
