from config import config

def triage_ocr_confidence(record):
    errors = []
    confidence = record.get('ocr_confidence')

    if confidence is None:
        errors.append({
            'category':'OCR_CONFIDENCE',
            'severity': 'WARNING',
            'field': 'ocr_confidence',
            'message': 'OCR confidence score missing',
            'suggestion': 'Add confidence score from OCR engine output'
        })
        return errors 
    
    if confidence >= config.OCR_HIGH_CONFIDENCE:
        pass #high bucket - auto accept/no error generated
    elif confidence >= config.OCR_LOW_CONFIDENCE:
        errors.append({
            'category':'OCR_CONFIDENCE',
            'severity': 'INFO',
            'field': 'ocr_confidence',
            'message': f'Score {confidence} - MEDIUM bucket (review if other issues found)',
            'suggestion': 'Accept if no other validator flag this record'
        })
    else:
        errors.append({
            'category':'OCR_CONFIDENCE',
            'severity': 'WARNING',
            'field': 'ocr_confidence',
            'message': f'Score {confidence} - LOW bucket (mandatory manual review)',
            'suggestion': 'OCR was uncertain on too many characters. Verify against source document'
        })
    return errors