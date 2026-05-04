#validators/__init__.py
from .schema_validator import validate_schema
from .range_validator import validate_ranges
from .icd_validator import validate_icd_codes
from .completeness_checker import check_completeness
from .medication_validator import validate_medication #added after phase 3
from .phi_detector import detect_phi #added after phase 3

def run_all_validators(record):
    all_errors = []

    #schema will run first
    schema_errors = validate_schema(record)
    all_errors.extend(schema_errors)

    #only run detailed validator is structure is ok
    critical_schema_fails = []
    for e in schema_errors:
        if e['severity'] == 'CRITICAL':
            critical_schema_fails.append(e)
    
    if len(critical_schema_fails) < 3:
        all_errors.extend(validate_ranges(record))
        all_errors.extend(validate_icd_codes(record))
        all_errors.extend(check_completeness(record))
        all_errors.extend(validate_medication(record)) #added after phase 3
        all_errors.extend(detect_phi(record)) #added after phase 3
    
    #determine overall status
    #has_critical
    has_critical = False
    for e in all_errors:
        if e['severity'] == 'CRITICAL':
            has_critical = True
            break #no need to check further
    
    #has_warning
    has_warning = False
    for e in all_errors:
        if e['severity'] == 'WARNING':
            has_warning = True
            break
    
    if has_critical:
        status = 'FAIL'
    elif has_warning:
        status = 'WARNING'
    else:
        status = 'PASS'
    
    return {'status': status, 'errors': all_errors}