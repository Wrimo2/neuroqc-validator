#schema_validator.py

#------------Part A: The Configuration Dictionary-------------

REQUIRED_FIELDS = {
    'patient_id': str,
    'dob_year': int,
    'gender': str,
    'visit_date': str,
    'diagnosis_codes': list,
    'vitals': dict
}

ALLOWED_GENDERS = ['Male', 'Female', 'Other', 'Unknown']

#------------Part B: The Main Validation Function-------------

def validate_schema(record):
    errors = []

    #loop through every required field
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in record:
            errors.append({
                'category': 'SCHEMA',
                'severity': 'CRITICAL',
                'field': field,
                'message': f'Required field "{field}" is missing',
                'suggestion': f'Ensure OCR pipeline outputs "{field}"'
            })
        elif record[field] is None:
            errors.append({
                'category': 'SCHEMA',
                'severity': 'CRITICAL',
                'field': field,
                'message': f'Required field "{field}" is null',
                'suggestion': f'Check sourse document for this data"'
            })
        elif not isinstance(record[field], expected_type):
            errors.append({
                'category': 'SCHEMA',
                'severity': 'CRITICAL',
                'field': field,
                'message': f'"{field}" should be '
                           f'{expected_type.__name__}, got '
                           f'{type(record[field]).__name__}',
                'suggestion': f'Convert "{field}" to '
                              f'{expected_type.__name__} in pipeline'
            })

    # Validate gender values
    if record.get('gender') and record['gender'] not in ALLOWED_GENDERS:
        errors.append({
            'category': 'SCHEMA',
            'severity': 'WARNING',
            'field': 'gender',
            'message': f'Gender "{record["gender"]}" not in allowed values',
            'suggestion': f'Expected one of: {ALLOWED_GENDERS}'
        })
    return errors