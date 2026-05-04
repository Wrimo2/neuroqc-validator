from app import app
from validators.medication_validator import validate_medication

test_record = {
 'medications': [
 'Levetiracetam 500mg', 
 'Levtiracetam 500mg', 
 'Topiramte 25mg', 
 'Gabapentn 300mg', 
 'Xyzabc 100mg', 
 ]
}

with app.app_context():
    errors = validate_medication(test_record)
    print(f"total errors: {len(errors)}\n")
    for e in errors:
        print(f'[{e["severity"]}] {e["message"]}')
        print(f'   -> {e["suggestion"]}\n')

