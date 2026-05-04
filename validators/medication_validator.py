#validators/medication_validator.py
from rapidfuzz import fuzz, process
from models.db_models import ReferenceMedication

def validate_medication(record):
    errors = []
    medications = record.get('medications', [])

    #Guard clause: if medication is not a list, let the schema validator handle it
    if not isinstance(medications, list):
        return errors
    
    #load all drug name once
    all_drugs = []
    for m in ReferenceMedication.query.all():
        all_drugs.append(m.drug_name)
    
    for med_entry in medications:
        if med_entry:
            drug_name = med_entry.split()[0]
        else:
            drug_name = ''
        
        if not drug_name:
            continue

        #exact match first - fast path
        if drug_name in all_drugs:
            continue

        #fuzzy match - slow path when exact match failed
        best_match = process.extractOne(drug_name, all_drugs, scorer=fuzz.ratio)

        if best_match:
            match_name, score, _ = best_match

            if score >= 85:
                errors.append({
                    'category':'MEDICATION',
                    'severity':'WARNING',
                    'field':'medications',
                    'message':f'"{drug_name}" not found. Best Match: "{match_name}" (score: {int(score)}%)',
                    'suggestion':f'Likely OCR missspelling. Replace with "{match_name}".'
                })
            else:
                errors.append({
                    'category':'MEDICATION',
                    'severity':'WARNING',
                    'field':'medications',
                    'message':f'"{drug_name}" not found. Closest: "{match_name}" (score: {int(score)}%)',
                    'suggestion':f'Low confidence match. Manual verification required.'
                })
    return errors
