#validators/phi_detector.py
import re
import spacy

#loading spaCy model once at module level
nlp = spacy.load('en_core_web_sm')

PHI_PATTERNS = [
    {
        'name':'Phone Number',
        'pattern':r'\b\d{3}[-.]\d{3}[-.]\d{4}\b',
        'severity':'CRITICAL'
    },
    {
        'name':'SSN',
        'pattern':r'\b\d{3}-\d{2}-\d{4}\b',
        'severity':'CRITICAL'
    },
    {
        'name':'Email Address',
        'pattern':r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'severity':'CRITICAL'
    },
    {
        'name':'Full Date (Month)',
        'pattern':r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
        'severity':'WARNING'
    },
    {
        'name':'Date (MM/DD/YYYY)',
        'pattern':r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        'severity':'WARNING'
    },
    {
        'name':'MRN',
        'pattern':r'\bMRN[:\s]*\d{6,10}\b',
        'severity':'CRITICAL'   
    }
]

# The Main Detection Function
def detect_phi(record):
    errors = []

    #scan these free-text fields for PHI
    text_fields = ['clinical_note']
    # In Future: we can extend it to ['clinical_note', 'discharge_summary', 'imaging_impression']

    for field in text_fields:
        text = record.get(field, '')
        if not text or not isinstance(text, str):
            continue

        #Layer1:----------Regex Patterns-----------
        for phi in PHI_PATTERNS:
            matches = re.findall(phi['pattern'], text, re.IGNORECASE)
            for match in matches:
                masked = match[:3] + '*' * (len(match)-3)
                errors.append({
                    'category':'PHI_LEAK',
                    'severity':phi['severity'],
                    'field':field,
                    'message':f'{phi['name']} detected: "{masked}"',
                    'suggestion':f'Remove or musk this {phi['name'].lower()} before data ingestion.'
                })
        #Layer2:---------spaCy: NER---------------
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                masked = ent.text[:2] + '*' * (len(ent.text) - 2)
                errors.append({
                    'category': 'PHI_LEAK',
                    'severity': 'CRITICAL',
                    'field': field,
                    'message': f'Person name detected: "{masked}"',
                    'suggestion': 'Deidentification may have failed. Remove patient/provider name'
                })
            elif ent.label_ == 'GPE':
                errors.append({
                    'category': 'PHI_LEAK',
                    'severity': 'WARNING',
                    'field': field,
                    'message': f'Geographic location detected: "{ent.text}"',
                    'suggestion': 'Location may identify patient. Consider removal.'
                })
            elif ent.label_ == 'ORG':
                errors.append({
                    'category': 'PHI_LEAK',
                    'severity': 'WARNING',
                    'field': field,
                    'message': f'Organisation detected: "{ent.text}"',
                    'suggestion': 'Provider/facility name may identify patient.'
                })
    return errors

