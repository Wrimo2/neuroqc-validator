from app import app
from validators.phi_detector import detect_phi

test_record = {
    'clinical_note': (
        'Patient Jane Doe reports increased migraine frequency since March 15, 2024. '
        'Referred by Dr. Patel from Emory Hospital in Atlanta. '
        'Contact: jdoe@email.com, phone 770-555-0142. '
        'SSN 123-45-6789, MRN: 12345678. Follow up in 3 months.'
    )
}

with app.app_context():
    errors = detect_phi(test_record)
    print(f'Total PHI issues found: {len(errors)}\n')
    for e in errors:
        print(f'[{e['severity']}] {e['message']}')