#icd_validator.py
from models.db_models import ReferenceICD10
from Levenshtein import distance as levenshtein_distance

def validate_icd_codes(record):
    errors = []
    codes = record.get('diagnosis_codes', [])

    if not isinstance(codes, list):
        return errors #schema validator handles type issues
    for code in codes:
        #Step1: direct lookup, is the code valid?
        ref = ReferenceICD10.query.filter_by(code = code).first()
        if ref:
            continue #valid code nothing to flag
        #steo2: Code not found - find closest matches
        all_codes = ReferenceICD10.query.all()
        suggestions = []

        for ref_code in all_codes:
            dist = levenshtein_distance(code, ref_code.code)
            if dist <= 2: #within 2 edits
                suggestions.append((ref_code.code, ref_code.description, dist))
        suggestions.sort(key=lambda x:x[2])  #closest first

        if suggestions:
            best = suggestions[0]
            errors.append({
                'category': 'ICD',
                'severity': 'WARNING',
                'field': 'diagnosis_codes',
                'message': f'Code {code} not found in ICD-10',
                'suggestion': f'Did you mean "{best[0]}" '
                              f'({best[1]})? Edit distance: {best[2]}'
            })
        else:
            errors.append({
                'category': 'ICD',
                'severity': 'CRITICAL',
                'field': 'diagnosis_codes',
                'message': f'Code "{code}" not found, no close match',
                'suggestion': 'Verify source. May be ICD-9 format.'
            })
    return errors
