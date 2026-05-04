#range_validator.py
from models.db_models import ReferenceVitaRange

def validate_ranges(record):
    errors = []

    # Process vitals (nurse-collected at check-in)
    vitals = record.get('vitals') or {}
    for vital_name, value in vitals.items():
        if value is None:
            continue #completeness checker will handle nulls
        ref = ReferenceVitaRange.query.filter_by(vital_name = vital_name).first()

        if ref is None:
            errors.append({
                'category': 'RANGE',
                'severity': 'INFO',
                'field': f'vitals.{vital_name}',
                'message': f'No reference range for "{vital_name}"',
                'suggestion': 'Add to reference_vital_ranges table'
            })
        elif not (ref.min_value <= value <= ref.max_value):
            errors.append({
                'category': 'RANGE',
                'severity': 'CRITICAL',
                'field': f'vitals.{vital_name}',
                'message': f'Value {value} outside range '
                           f'[{ref.min_value}-{ref.max_value}] '
                           f'{ref.unit}',
                'suggestion': 'Likely OCR error. Verify source.'
            })
    # Process lab results (laboratory-collected)
    labs = record.get('lab_results') or {}
    for lab_name, value in labs.items():
        if value is None:
            continue #completeness checker will handle nulls
        ref = ReferenceVitaRange.query.filter_by(vital_name = lab_name).first()
        if ref and not (ref.min_value <= value <= ref.max_value):
            errors.append({
                'category':'RANGE',
                'severity': 'CRITICAL',
                'field': f'vitals.{lab_name}',
                'message': f'Value {value} outside range '
                           f'[{ref.min_value}-{ref.max_value}] '
                           f'{ref.unit}',
                'suggestion': 'Likely OCR error or unit mismatch.'
            })
            
    return errors