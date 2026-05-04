#this file of code is written by claude model: opus 4.6
"""
NeuroQC Validator — Sample Data Generator
==========================================
Generates three test JSON files for Phase 4 end-to-end testing:
  1. clean_batch.json   — 10 records, all PASS
  2. dirty_batch.json   — 20 records, mixed errors across all 7 categories
  3. phi_leak_batch.json — 15 records, focused on PHI detection

Usage:
    python generate_samples.py

Output:
    Creates a sample_data/ directory with the three JSON files.

IMPORTANT:
    All data here is completely fabricated.
    Phone numbers use the 555- prefix (reserved for fiction).
    Email addresses use @example.com (reserved by RFC 2606).
    Names are generic placeholders — no real patient data.
"""

import json
import os
import copy
import random

# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------
OUTPUT_DIR = "sample_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Base record template — a perfectly clean record that passes all validators
# ---------------------------------------------------------------------------
BASE_RECORD = {
    "patient_id": "NDAI-TEMPLATE-000",
    "dob_year": 1975,
    "gender": "Female",
    "visit_date": "2024-03-15",
    "diagnosis_codes": ["G43.909"],
    "medications": ["Topiramate 50mg", "Sumatriptan 100mg"],
    "vitals": {
        "systolic_bp": 120,
        "diastolic_bp": 78,
        "heart_rate": 72,
        "weight_kg": 65.0
    },
    "lab_results": {
        "sodium_meq_l": 140,
        "creatinine_mg_dl": 0.9,
        "glucose_mg_dl": 95
    },
    "clinical_note": "Routine follow-up visit. Patient reports stable condition.",
    "ocr_confidence": 0.96
}


def deep_copy(record):
    """Return a fresh deep copy of a record so mutations don't leak."""
    return json.loads(json.dumps(record))


# ===========================================================================
# FILE 1 — clean_batch.json (10 records, all PASS)
# ===========================================================================
# Purpose: Prove the validators produce ZERO false positives on good data.

# Valid ICD-10 codes from neurology domain (use codes your seed data contains)
VALID_ICD_CODES = [
    "G43.909",   # Migraine, unspecified
    "G40.909",   # Epilepsy, unspecified
    "G47.00",    # Insomnia, unspecified
    "G30.9",     # Alzheimer's disease, unspecified
    "G20",       # Parkinson's disease
    "G35",       # Multiple sclerosis
    "G43.001",   # Migraine without aura, not intractable, with status migrainosus
    "G40.309",   # Generalized idiopathic epilepsy, not intractable
    "G47.33",    # Obstructive sleep apnea
    "G25.81",    # Restless legs syndrome
]

# Valid medication names (must match your medication seed data exactly)
VALID_MEDICATIONS = [
    "Topiramate 50mg",
    "Sumatriptan 100mg",
    "Levetiracetam 500mg",
    "Amitriptyline 25mg",
    "Gabapentin 300mg",
    "Valproic Acid 250mg",
    "Carbamazepine 200mg",
    "Lamotrigine 100mg",
    "Donepezil 10mg",
    "Memantine 10mg",
]

# Varied clinical notes — all clean, no PHI
CLEAN_NOTES = [
    "Routine follow-up visit. Patient reports stable condition.",
    "Patient presents for medication review. No new complaints.",
    "Quarterly check-up. Seizure frequency has decreased since last visit.",
    "Follow-up after dosage adjustment. Tolerating new regimen well.",
    "Annual neurological examination. No focal deficits noted.",
    "Patient reports improved sleep quality with current medication.",
    "Review of recent imaging results. No significant changes observed.",
    "Patient denies headache, dizziness, or visual disturbances.",
    "Medication compliance confirmed. No adverse effects reported.",
    "Post-treatment evaluation. Symptoms remain well controlled.",
]


def make_clean_record(idx):
    """Generate a single clean record that should PASS all validators."""
    r = deep_copy(BASE_RECORD)
    r["patient_id"] = f"NDAI-CLEAN-{idx:03d}"
    r["dob_year"] = random.randint(1950, 2000)
    r["gender"] = random.choice(["Male", "Female"])
    r["visit_date"] = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

    # Pick 1-2 valid ICD codes
    r["diagnosis_codes"] = random.sample(VALID_ICD_CODES, k=random.randint(1, 2))

    # Pick 1-3 valid medications
    r["medications"] = random.sample(VALID_MEDICATIONS, k=random.randint(1, 3))

    # Generate in-range vitals
    r["vitals"] = {
        "systolic_bp": random.randint(100, 140),
        "diastolic_bp": random.randint(60, 90),
        "heart_rate": random.randint(55, 95),
        "weight_kg": round(random.uniform(50.0, 100.0), 1)
    }

    # Generate in-range lab results
    r["lab_results"] = {
        "sodium_meq_l": random.randint(136, 145),
        "creatinine_mg_dl": round(random.uniform(0.6, 1.2), 1),
        "glucose_mg_dl": random.randint(70, 110)
    }

    r["clinical_note"] = CLEAN_NOTES[(idx - 1) % len(CLEAN_NOTES)]
    r["ocr_confidence"] = round(random.uniform(0.93, 0.99), 2)

    return r


def generate_clean_batch():
    """Generate clean_batch.json — 10 records, all should PASS."""
    records = [make_clean_record(i) for i in range(1, 11)]
    path = os.path.join(OUTPUT_DIR, "clean_batch.json")
    with open(path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"  Created {path} — {len(records)} clean records")


# ===========================================================================
# FILE 2 — dirty_batch.json (20 records, deliberately broken)
# ===========================================================================
# Purpose: Demonstrate all 7 validator categories catching real errors.
#
# Distribution (per the guide):
#   3 records — out-of-range vitals          (RANGE category)
#   2 records — invalid/misspelled ICD codes (ICD category)
#   4 records — misspelled drug names        (MEDICATION category)
#   3 records — missing required fields      (COMPLETENESS category)
#   3 records — wrong data types             (SCHEMA category)
#   5 records — clean (interleaved)


def make_range_error_record(idx, variant):
    """Records with out-of-range vitals — simulating OCR misreads."""
    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-DIRTY-{idx:03d}"

    if variant == 0:
        # Systolic BP OCR error: 128 misread as 928
        r["vitals"]["systolic_bp"] = 928
        r["clinical_note"] = "Patient reports no change in symptoms."
    elif variant == 1:
        # Heart rate impossibly high: 72 misread as 720
        r["vitals"]["heart_rate"] = 720
        r["clinical_note"] = "Stable presentation at follow-up."
    else:
        # Diastolic BP impossibly low: likely OCR dropped a digit
        r["vitals"]["diastolic_bp"] = 8
        r["clinical_note"] = "Regular check-up, vitals recorded."

    return r


def make_icd_error_record(idx, variant):
    """Records with invalid or misspelled ICD-10 codes."""
    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-DIRTY-{idx:03d}"

    if variant == 0:
        # Completely invalid code
        r["diagnosis_codes"] = ["Z99.999", "G43.909"]
        r["clinical_note"] = "Reviewing diagnosis coding for accuracy."
    else:
        # Misspelled/malformed code (missing dot, wrong format)
        r["diagnosis_codes"] = ["G43909"]  # missing the dot
        r["clinical_note"] = "Assessment of current diagnosis codes."

    return r


def make_medication_error_record(idx, variant):
    """Records with misspelled medication names — fuzzy matching territory."""
    misspelled_drugs = [
        "Levtiracetam 500mg",     # missing 'e' — Levetiracetam
        "Topiramat 50mg",         # missing 'e' — Topiramate
        "Gabapntin 300mg",        # missing 'e' — Gabapentin
        "Summatriptan 100mg",     # extra 'm' — Sumatriptan
    ]

    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-DIRTY-{idx:03d}"
    r["medications"] = [misspelled_drugs[variant]]
    r["clinical_note"] = "Medication names transcribed from handwritten prescription."
    # Lower OCR confidence to reinforce the OCR-error story
    r["ocr_confidence"] = round(random.uniform(0.72, 0.82), 2)

    return r


def make_completeness_error_record(idx, variant):
    """Records with missing required fields."""
    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-DIRTY-{idx:03d}"

    if variant == 0:
        # Missing vitals entirely
        r["vitals"] = None
        r["clinical_note"] = "Vitals not recorded during this visit."
    elif variant == 1:
        # Missing lab_results entirely
        del r["lab_results"]
        r["clinical_note"] = "Lab results pending from external facility."
    else:
        # Missing medications list
        r["medications"] = []
        r["clinical_note"] = "Patient currently not on any medications."

    return r


def make_schema_error_record(idx, variant):
    """Records with wrong data types — e.g., abbreviated gender."""
    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-DIRTY-{idx:03d}"

    if variant == 0:
        # Gender as abbreviation instead of full word
        r["gender"] = "F"
        r["clinical_note"] = "Demographic data imported from legacy system."
    elif variant == 1:
        # dob_year as string instead of integer
        r["dob_year"] = "nineteen eighty"
        r["clinical_note"] = "Year of birth OCR extracted from handwritten form."
    else:
        # diagnosis_codes as a single string instead of a list
        r["diagnosis_codes"] = "G43.909"
        r["clinical_note"] = "Single diagnosis recorded for this encounter."

    return r


def generate_dirty_batch():
    """Generate dirty_batch.json — 20 records with interleaved errors."""
    records = []
    idx = 1

    # We'll interleave error records with clean ones.
    # Order: clean, range, clean, icd, medication, clean, completeness,
    #         medication, range, clean, schema, medication, clean,
    #         completeness, range, schema, icd, medication, completeness, schema

    # 3 range errors
    range_records = [make_range_error_record(idx + i, i) for i in range(3)]
    # 2 ICD errors
    icd_records = [make_icd_error_record(idx + 3 + i, i) for i in range(2)]
    # 4 medication errors
    med_records = [make_medication_error_record(idx + 5 + i, i) for i in range(4)]
    # 3 completeness errors
    comp_records = [make_completeness_error_record(idx + 9 + i, i) for i in range(3)]
    # 3 schema errors
    schema_records = [make_schema_error_record(idx + 12 + i, i) for i in range(3)]
    # 5 clean records
    clean_records = [make_clean_record(idx + 15 + i) for i in range(5)]
    # Rename clean record patient IDs to dirty series for consistency
    for c in clean_records:
        c["patient_id"] = c["patient_id"].replace("CLEAN", "DIRTY")

    # Interleave: don't cluster all errors at the start
    all_error_records = range_records + icd_records + med_records + comp_records + schema_records
    random.shuffle(all_error_records)

    # Insert clean records at positions 0, 4, 8, 12, 16
    combined = []
    error_iter = iter(all_error_records)
    clean_iter = iter(clean_records)

    for i in range(20):
        if i in [0, 4, 8, 12, 16]:
            combined.append(next(clean_iter))
        else:
            combined.append(next(error_iter))

    # Re-number patient IDs sequentially for a clean look
    for i, rec in enumerate(combined, start=1):
        rec["patient_id"] = f"NDAI-DIRTY-{i:03d}"

    path = os.path.join(OUTPUT_DIR, "dirty_batch.json")
    with open(path, "w") as f:
        json.dump(combined, f, indent=2)
    print(f"  Created {path} — {len(combined)} records (15 with errors, 5 clean)")


# ===========================================================================
# FILE 3 — phi_leak_batch.json (15 records, focused on PHI detection)
# ===========================================================================
# Purpose: Demonstrate HIPAA-relevant PHI detection in clinical notes.
#
# Distribution (per the guide):
#   5 records — phone numbers in notes
#   3 records — patient names in notes
#   2 records — email addresses in notes
#   2 records — full dates in notes (specific dates that could identify a patient)
#   3 records — clean (no PHI)
#
# ALL identifiers are completely fake:
#   - Phone numbers use 555- prefix (reserved for fiction)
#   - Emails use @example.com (reserved by RFC 2606)
#   - Names are generic placeholders


def make_phi_phone_record(idx, variant):
    """Records with phone numbers embedded in clinical notes."""
    phone_notes = [
        "Patient called from 555-012-3456 to confirm appointment.",
        "Emergency contact reached at (555) 098-7654 for consent.",
        "Pharmacy callback number recorded as 555.321.6789 in chart.",
        "Patient provided new contact number 555-444-2233 during visit.",
        "Caregiver phone 555-876-5432 noted for follow-up coordination.",
    ]

    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-PHI-{idx:03d}"
    r["clinical_note"] = phone_notes[variant]
    return r


def make_phi_name_record(idx, variant):
    """Records with patient names embedded in clinical notes."""
    name_notes = [
        "John Smith reports worsening headaches over the past two weeks.",
        "Discussed treatment plan with Jane Doe and her family.",
        "Robert Johnson was referred from primary care for evaluation.",
    ]

    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-PHI-{idx:03d}"
    r["clinical_note"] = name_notes[variant]
    return r


def make_phi_email_record(idx, variant):
    """Records with email addresses embedded in clinical notes."""
    email_notes = [
        "Patient requested results be sent to jsmith@example.com.",
        "Follow-up instructions emailed to patient.jane@example.com per request.",
    ]

    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-PHI-{idx:03d}"
    r["clinical_note"] = email_notes[variant]
    return r


def make_phi_date_record(idx, variant):
    """Records with full specific dates in clinical notes (PHI risk)."""
    date_notes = [
        "Patient was admitted on March 15, 2024 and discharged two days later.",
        "Symptoms first appeared on January 3rd, 2024 according to patient report.",
    ]

    r = make_clean_record(idx)
    r["patient_id"] = f"NDAI-PHI-{idx:03d}"
    r["clinical_note"] = date_notes[variant]
    return r


def generate_phi_batch():
    """Generate phi_leak_batch.json — 15 records testing PHI detection."""
    records = []
    idx = 1

    # 5 phone number records
    for v in range(5):
        records.append(make_phi_phone_record(idx, v))
        idx += 1

    # 3 name records
    for v in range(3):
        records.append(make_phi_name_record(idx, v))
        idx += 1

    # 2 email records
    for v in range(2):
        records.append(make_phi_email_record(idx, v))
        idx += 1

    # 2 date records
    for v in range(2):
        records.append(make_phi_date_record(idx, v))
        idx += 1

    # 3 clean records (no PHI)
    for i in range(3):
        r = make_clean_record(idx)
        r["patient_id"] = f"NDAI-PHI-{idx:03d}"
        records.append(r)
        idx += 1

    # Shuffle to interleave PHI and clean records
    random.shuffle(records)

    # Re-number sequentially
    for i, rec in enumerate(records, start=1):
        rec["patient_id"] = f"NDAI-PHI-{i:03d}"

    path = os.path.join(OUTPUT_DIR, "phi_leak_batch.json")
    with open(path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"  Created {path} — {len(records)} records (12 with PHI, 3 clean)")


# ===========================================================================
# Main
# ===========================================================================
if __name__ == "__main__":
    # Set seed for reproducibility — remove this line if you want
    # different data each run
    random.seed(42)

    print("Generating NeuroQC sample data files...")
    print()

    generate_clean_batch()
    generate_dirty_batch()
    generate_phi_batch()

    print()
    print(f"All files saved to {OUTPUT_DIR}/")
    print()
    print("Next steps:")
    print("  1. Start your Flask server:  python app.py")
    print("  2. Upload clean_batch.json   — expect 10 PASS, 0 WARNING, 0 FAIL")
    print("  3. Upload dirty_batch.json   — expect a mix of PASS/WARNING/FAIL")
    print("  4. Upload phi_leak_batch.json — expect PHI_LEAK errors on 12 records")
    print("  5. Run the error-path tests (no file, wrong extension, broken JSON, empty array)")
    print("  6. Verify database counts match page counts")