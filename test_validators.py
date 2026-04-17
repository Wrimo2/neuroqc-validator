#test_validators.py
from app import app
from validators import run_all_validators

test_record = {
        "patient_id": "NDAI-TEST-001",
        "dob_year": 1962,
        "gender": "F",
        "visit_date": "2024-03-15",
        "diagnosis_codes": ["G43.909", "G40.89", "ZZZZZ"],
        "medications": ["Topiramate 25mg"],
        "vitals": {
            "systolic_bp": 928,
            "diastolic_bp": 82,
            "heart_rate": 74,
            "weight_kg": None
        },
        "lab_results": {
            "sodium_meq_l": None,
            "creatinine_mg_dl": 0.9
        },
        "clinical_note": "Patient reports migraines.",
        "ocr_confidence": 0.72
    }

with app.app_context():
    result = run_all_validators(test_record)
    print(f"overall status {result['status']}")
    print(f'Total errors: {len(result['errors'])}')
    print('-----------------')
    for e in result["errors"]:
        print(f'[{e['severity']}] {e['category']}: {e["message"]}')
