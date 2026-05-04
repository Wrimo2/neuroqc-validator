from app import app
from validators import run_all_validators

test_record = {
    'patient_id': 'NDAI-TEST-001',
    'dob_year': 1962,
    'gender': 'F', 
    'visit_date': '2024-03-15',
    'diagnosis_codes': ['G43.909', 'G4O.89', 'ZZZZZ'], 
    'medications': ['Levtiracetam 500mg', 'Topiramate 25mg', 'Xyzabc 100mg'],
    'vitals': {
        'systolic_bp': 928, 
        'diastolic_bp': 82,
        'heart_rate': 74,
        'weight_kg': None 
    },
    'lab_results': {
        'sodium_meq_l': None, # missing
        'creatinine_mg_dl': 0.9
    },
    'clinical_note': (
        'Patient Jane Doe reports increased migraine frequency since Jan 2024. '
        'Referred by Dr. Patel from Atlanta Neurology Clinic. '
        'Phone: 770-555-0142. Email: jdoe@email.com. MRN: 12345678. '
        'Follow up in 3 months.'
    ),
    'ocr_confidence': 0.72
}

with app.app_context():
    result = run_all_validators(test_record)

    print(f'Overall Status: {result["status"]}')
    print(f'Total Errors: {len(result["errors"])}\n')
    # Group errors by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for e in result['errors']:
        by_category[e['category']].append(e)
    for category, errs in sorted(by_category.items()):
        print(f'=== {category} ({len(errs)} errors) ===')
        for e in errs:
            print(f' [{e["severity"]}] {e["field"]}: {e["message"]} {e['suggestion']}')
            print()
