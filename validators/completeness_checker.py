#completeness_checker.py

CRITICAL_FIELDS = ['patient_id', 'diagnosis_code', 'visit_date']
IMPORTANT_FIELDS = ['medications', 'vitals', 'clinical_note']

def check_completeness(record):
    errors = []

    #check all top level fields
    for field, value in record.items():
        if value is None or value == '' or value == []:
            if field in CRITICAL_FIELDS:
                severity = 'CRITICAL'
            else:
                severity = 'WARNING'
            errors.append({
                'category': 'COMPLETENESS',
                'severity': severity,
                'field': field,
                'message': f'Field "{field}" is empty or null',
                'suggestion': f'Check if source document has this data'
            })
    #check nested fields (vitals/lab results)
    for nested_key in ['vitals','lab_results']:
        nested = record.get(nested_key, {})
        if isinstance(nested, dict):
            for k, v in nested.items():
                if k is None:
                    errors.append({
                        'category': 'COMPLETENESS',
                        'severity': 'WARNING',
                        'field': f'{nested_key}.{k}',
                        'message': f'Nested field '
                                   f'"{nested_key}.{k}" is null',
                        'suggestion': 'value may not have been captured in source'
                    })
    
    return errors