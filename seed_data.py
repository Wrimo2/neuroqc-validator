#seed_data.py
import os
from flask import Flask
from config import config
from models.db_models import db, ReferenceICD10, ReferenceMedication, ReferenceVitaRange

#-------------ReferenceICD10---------------

ICD_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'Data',
    'april-1-2026-code-descriptions-in-tabular-order',
    'Code Descriptions', 'icd10cm_order_2026.txt'
)


def parse_icd10_file(path):
    """Parse the CMS fixed-width ICD-10-CM order file.

    Columns (0-indexed):
      [6:13]  ICD code (7 chars, space-padded)
      [14]    flag: '0' = header/non-billable, '1' = billable
      [77:]   long description (rightmost, full text)
    """
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if len(line) < 78:
                continue
            code = line[6:13].strip()
            flag = line[14:15].strip()
            long_desc = line[77:].rstrip()
            if not code or flag not in ('0', '1'):
                continue
            entries.append((code, flag, long_desc))
    return entries


def filter_g_r_with_category(entries):
    """Keep only G* and R* codes. Category = description of the nearest
    flag=0 ancestor (a flag=0 code whose code is a prefix of the current
    code). A flag=0 row's category is its own description.
    """
    out = []
    stack = []  # list of (code, description) for flag=0 rows, in prefix order
    for code, flag, desc in entries:
        while stack and not code.startswith(stack[-1][0]):
            stack.pop()
        if flag == '0':
            category = desc
            stack.append((code, desc))
        else:
            category = stack[-1][1] if stack else desc
        if code.startswith('G') or code.startswith('R'):
            out.append((format_icd_code(code), desc, category))
    return out


def format_icd_code(code):
    """Insert a dot after the 3rd character for codes longer than 3 chars.
    Example: 'G0402' -> 'G04.02', 'G03' -> 'G03'.
    """
    return code if len(code) <= 3 else f"{code[:3]}.{code[3:]}"


def seed_icd10(app):
    with app.app_context():
        db.create_all()
        # Ensure category column can hold long descriptions (widened from 100).
        from sqlalchemy import text
        try:
            db.session.execute(text(
                "ALTER TABLE reference_icd10_codes "
                "MODIFY COLUMN category VARCHAR(255)"
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
        entries = parse_icd10_file(ICD_FILE)
        rows = filter_g_r_with_category(entries)

        # Remove any legacy un-dotted G*/R* rows (codes >3 chars without a dot).
        from sqlalchemy import or_, and_, not_
        ReferenceICD10.query.filter(
            and_(
                or_(ReferenceICD10.code.like('G%'), ReferenceICD10.code.like('R%')),
                db.func.length(ReferenceICD10.code) > 3,
                not_(ReferenceICD10.code.like('_%.%')),
            )
        ).delete(synchronize_session=False)
        db.session.commit()

        existing = {c for (c,) in db.session.query(ReferenceICD10.code).all()}
        to_add = [
            ReferenceICD10(code=code, description=desc, category=category)
            for code, desc, category in rows
            if code not in existing
        ]
        if to_add:
            db.session.bulk_save_objects(to_add)
            db.session.commit()
        print(f"ICD-10 seed: parsed {len(entries)} rows, "
              f"{len(rows)} G/R codes, inserted {len(to_add)} new "
              f"(skipped {len(rows) - len(to_add)} existing).")

#-------------ReferenceMedication---------------

def seed_medications(app):
    MEDICATIONS = [
        # ── ANTIEPILEPTICS ──────────────────────────────────────────────────
        {"drug_name": "Levetiracetam",     "drug_class": "Antiepileptic",            "common_dosages": "250mg,500mg,750mg,1000mg"},
        {"drug_name": "Carbamazepine",     "drug_class": "Antiepileptic",            "common_dosages": "100mg,200mg,400mg"},
        {"drug_name": "Valproic Acid",     "drug_class": "Antiepileptic",            "common_dosages": "250mg,500mg"},
        {"drug_name": "Valproate Sodium",  "drug_class": "Antiepileptic",            "common_dosages": "250mg,500mg"},
        {"drug_name": "Lamotrigine",       "drug_class": "Antiepileptic",            "common_dosages": "25mg,50mg,100mg,150mg,200mg"},
        {"drug_name": "Topiramate",        "drug_class": "Antiepileptic/Antimigraine","common_dosages": "25mg,50mg,100mg,200mg"},
        {"drug_name": "Oxcarbazepine",     "drug_class": "Antiepileptic",            "common_dosages": "150mg,300mg,600mg"},
        {"drug_name": "Phenytoin",         "drug_class": "Antiepileptic",            "common_dosages": "100mg,200mg,300mg"},
        {"drug_name": "Phenobarbital",     "drug_class": "Antiepileptic",            "common_dosages": "15mg,30mg,60mg,100mg"},
        {"drug_name": "Zonisamide",        "drug_class": "Antiepileptic",            "common_dosages": "25mg,50mg,100mg"},
        {"drug_name": "Gabapentin",        "drug_class": "Antiepileptic/Neuropathic","common_dosages": "100mg,300mg,400mg,600mg,800mg"},
        {"drug_name": "Pregabalin",        "drug_class": "Antiepileptic/Neuropathic","common_dosages": "25mg,50mg,75mg,100mg,150mg,200mg,300mg"},
        {"drug_name": "Lacosamide",        "drug_class": "Antiepileptic",            "common_dosages": "50mg,100mg,150mg,200mg"},
        {"drug_name": "Perampanel",        "drug_class": "Antiepileptic",            "common_dosages": "2mg,4mg,6mg,8mg,10mg,12mg"},
        {"drug_name": "Brivaracetam",      "drug_class": "Antiepileptic",            "common_dosages": "10mg,25mg,50mg,75mg,100mg"},
        {"drug_name": "Eslicarbazepine",   "drug_class": "Antiepileptic",            "common_dosages": "200mg,400mg,600mg,800mg"},
        {"drug_name": "Clobazam",          "drug_class": "Antiepileptic/Benzodiazepine","common_dosages": "5mg,10mg,20mg"},
        {"drug_name": "Clonazepam",        "drug_class": "Antiepileptic/Benzodiazepine","common_dosages": "0.5mg,1mg,2mg"},
        {"drug_name": "Felbamate",         "drug_class": "Antiepileptic",            "common_dosages": "400mg,600mg"},
        {"drug_name": "Vigabatrin",        "drug_class": "Antiepileptic",            "common_dosages": "500mg"},
        {"drug_name": "Rufinamide",        "drug_class": "Antiepileptic",            "common_dosages": "200mg,400mg"},
        {"drug_name": "Tiagabine",         "drug_class": "Antiepileptic",            "common_dosages": "2mg,4mg,12mg,16mg"},
        {"drug_name": "Cannabidiol",       "drug_class": "Antiepileptic",            "common_dosages": "100mg/mL"},
        {"drug_name": "Fenfluramine",      "drug_class": "Antiepileptic",            "common_dosages": "2.5mg/mL"},

        # ── SEIZURE RESCUE ───────────────────────────────────────────────────
        {"drug_name": "Diazepam",          "drug_class": "Seizure Rescue/Benzodiazepine","common_dosages": "2mg,5mg,10mg"},
        {"drug_name": "Lorazepam",         "drug_class": "Seizure Rescue/Benzodiazepine","common_dosages": "0.5mg,1mg,2mg"},
        {"drug_name": "Midazolam",         "drug_class": "Seizure Rescue/Benzodiazepine","common_dosages": "5mg/mL"},
        {"drug_name": "Acetazolamide",     "drug_class": "Antiepileptic/Carbonic Anhydrase Inhibitor","common_dosages": "125mg,250mg"},

        # ── MIGRAINE – ACUTE ─────────────────────────────────────────────────
        {"drug_name": "Sumatriptan",       "drug_class": "Triptan/Antimigraine",     "common_dosages": "25mg,50mg,100mg"},
        {"drug_name": "Rizatriptan",       "drug_class": "Triptan/Antimigraine",     "common_dosages": "5mg,10mg"},
        {"drug_name": "Zolmitriptan",      "drug_class": "Triptan/Antimigraine",     "common_dosages": "2.5mg,5mg"},
        {"drug_name": "Eletriptan",        "drug_class": "Triptan/Antimigraine",     "common_dosages": "20mg,40mg"},
        {"drug_name": "Almotriptan",       "drug_class": "Triptan/Antimigraine",     "common_dosages": "6.25mg,12.5mg"},
        {"drug_name": "Frovatriptan",      "drug_class": "Triptan/Antimigraine",     "common_dosages": "2.5mg"},
        {"drug_name": "Naratriptan",       "drug_class": "Triptan/Antimigraine",     "common_dosages": "1mg,2.5mg"},
        {"drug_name": "Lasmiditan",        "drug_class": "Dittan/Antimigraine",      "common_dosages": "50mg,100mg"},
        {"drug_name": "Rimegepant",        "drug_class": "CGRP Antagonist/Antimigraine","common_dosages": "75mg"},
        {"drug_name": "Ubrogepant",        "drug_class": "CGRP Antagonist/Antimigraine","common_dosages": "50mg,100mg"},
        {"drug_name": "Ergotamine",        "drug_class": "Ergot/Antimigraine",       "common_dosages": "1mg,2mg"},
        {"drug_name": "Dihydroergotamine", "drug_class": "Ergot/Antimigraine",       "common_dosages": "1mg/mL"},

        # ── MIGRAINE – PREVENTIVE ────────────────────────────────────────────
        {"drug_name": "Erenumab",          "drug_class": "CGRP mAb/Migraine Prevention","common_dosages": "70mg,140mg"},
        {"drug_name": "Fremanezumab",      "drug_class": "CGRP mAb/Migraine Prevention","common_dosages": "225mg"},
        {"drug_name": "Galcanezumab",      "drug_class": "CGRP mAb/Migraine Prevention","common_dosages": "120mg"},
        {"drug_name": "Eptinezumab",       "drug_class": "CGRP mAb/Migraine Prevention","common_dosages": "100mg,300mg"},
        {"drug_name": "Atogepant",         "drug_class": "CGRP Antagonist/Migraine Prevention","common_dosages": "10mg,30mg,60mg"},
        {"drug_name": "Propranolol",       "drug_class": "Beta Blocker/Migraine Prevention","common_dosages": "10mg,20mg,40mg,60mg,80mg"},
        {"drug_name": "Amitriptyline",     "drug_class": "TCA/Migraine Prevention",  "common_dosages": "10mg,25mg,50mg,75mg,100mg"},
        {"drug_name": "Venlafaxine",       "drug_class": "SNRI/Migraine Prevention", "common_dosages": "37.5mg,75mg,150mg"},

        # ── PARKINSON'S DISEASE ──────────────────────────────────────────────
        {"drug_name": "Levodopa",          "drug_class": "Dopaminergic/Parkinson",   "common_dosages": "100mg,250mg"},
        {"drug_name": "Carbidopa",         "drug_class": "Dopaminergic/Parkinson",   "common_dosages": "25mg"},
        {"drug_name": "Levodopa/Carbidopa","drug_class": "Dopaminergic/Parkinson",   "common_dosages": "10/100mg,25/100mg,25/250mg"},
        {"drug_name": "Pramipexole",       "drug_class": "Dopamine Agonist/Parkinson","common_dosages": "0.125mg,0.25mg,0.5mg,0.75mg,1mg,1.5mg"},
        {"drug_name": "Ropinirole",        "drug_class": "Dopamine Agonist/Parkinson","common_dosages": "0.25mg,0.5mg,1mg,2mg,3mg,4mg,5mg"},
        {"drug_name": "Rotigotine",        "drug_class": "Dopamine Agonist/Parkinson","common_dosages": "1mg/24h,2mg/24h,4mg/24h,6mg/24h,8mg/24h"},
        {"drug_name": "Apomorphine",       "drug_class": "Dopamine Agonist/Parkinson","common_dosages": "2mg/mL,10mg/mL"},
        {"drug_name": "Selegiline",        "drug_class": "MAO-B Inhibitor/Parkinson","common_dosages": "5mg"},
        {"drug_name": "Rasagiline",        "drug_class": "MAO-B Inhibitor/Parkinson","common_dosages": "0.5mg,1mg"},
        {"drug_name": "Safinamide",        "drug_class": "MAO-B Inhibitor/Parkinson","common_dosages": "50mg,100mg"},
        {"drug_name": "Entacapone",        "drug_class": "COMT Inhibitor/Parkinson", "common_dosages": "200mg"},
        {"drug_name": "Tolcapone",         "drug_class": "COMT Inhibitor/Parkinson", "common_dosages": "100mg,200mg"},
        {"drug_name": "Opicapone",         "drug_class": "COMT Inhibitor/Parkinson", "common_dosages": "25mg,50mg"},
        {"drug_name": "Amantadine",        "drug_class": "NMDA Antagonist/Parkinson","common_dosages": "100mg"},
        {"drug_name": "Trihexyphenidyl",   "drug_class": "Anticholinergic/Parkinson","common_dosages": "2mg,5mg"},
        {"drug_name": "Benztropine",       "drug_class": "Anticholinergic/Parkinson","common_dosages": "0.5mg,1mg,2mg"},

        # ── MULTIPLE SCLEROSIS ───────────────────────────────────────────────
        {"drug_name": "Ocrelizumab",       "drug_class": "Anti-CD20 mAb/MS",         "common_dosages": "300mg/10mL"},
        {"drug_name": "Fingolimod",        "drug_class": "S1P Modulator/MS",         "common_dosages": "0.5mg"},
        {"drug_name": "Natalizumab",       "drug_class": "Anti-integrin mAb/MS",     "common_dosages": "300mg/15mL"},
        {"drug_name": "Dimethyl Fumarate", "drug_class": "Immunomodulator/MS",       "common_dosages": "120mg,240mg"},
        {"drug_name": "Teriflunomide",     "drug_class": "Immunomodulator/MS",       "common_dosages": "7mg,14mg"},
        {"drug_name": "Glatiramer Acetate","drug_class": "Immunomodulator/MS",       "common_dosages": "20mg/mL,40mg/mL"},
        {"drug_name": "Alemtuzumab",       "drug_class": "Anti-CD52 mAb/MS",         "common_dosages": "12mg/1.2mL"},
        {"drug_name": "Cladribine",        "drug_class": "Purine Antimetabolite/MS", "common_dosages": "10mg"},
        {"drug_name": "Ofatumumab",        "drug_class": "Anti-CD20 mAb/MS",         "common_dosages": "20mg/0.4mL"},
        {"drug_name": "Ozanimod",          "drug_class": "S1P Modulator/MS",         "common_dosages": "0.23mg,0.46mg,0.92mg"},
        {"drug_name": "Siponimod",         "drug_class": "S1P Modulator/MS",         "common_dosages": "0.25mg,2mg"},
        {"drug_name": "Interferon Beta-1a","drug_class": "Immunomodulator/MS",       "common_dosages": "30mcg/0.5mL"},
        {"drug_name": "Interferon Beta-1b","drug_class": "Immunomodulator/MS",       "common_dosages": "0.25mg"},

        # ── DEMENTIA / ALZHEIMER'S ───────────────────────────────────────────
        {"drug_name": "Donepezil",         "drug_class": "Cholinesterase Inhibitor/Dementia","common_dosages": "5mg,10mg,23mg"},
        {"drug_name": "Rivastigmine",      "drug_class": "Cholinesterase Inhibitor/Dementia","common_dosages": "1.5mg,3mg,4.5mg,6mg"},
        {"drug_name": "Galantamine",       "drug_class": "Cholinesterase Inhibitor/Dementia","common_dosages": "4mg,8mg,12mg"},
        {"drug_name": "Memantine",         "drug_class": "NMDA Antagonist/Dementia", "common_dosages": "5mg,10mg"},
        {"drug_name": "Lecanemab",         "drug_class": "Anti-amyloid mAb/Alzheimer","common_dosages": "500mg/10mL"},
        {"drug_name": "Aducanumab",        "drug_class": "Anti-amyloid mAb/Alzheimer","common_dosages": "170mg,300mg"},

        # ── SMA / ALS ────────────────────────────────────────────────────────
        {"drug_name": "Nusinersen",        "drug_class": "Antisense Oligonucleotide/SMA","common_dosages": "12mg/5mL"},
        {"drug_name": "Risdiplam",         "drug_class": "SMN2 Splicing Modifier/SMA","common_dosages": "0.75mg/mL"},
        {"drug_name": "Riluzole",          "drug_class": "Glutamate Inhibitor/ALS",  "common_dosages": "50mg"},
        {"drug_name": "Edaravone",         "drug_class": "Free Radical Scavenger/ALS","common_dosages": "60mg/100mL"},

        # ── SPASTICITY ───────────────────────────────────────────────────────
        {"drug_name": "Baclofen",          "drug_class": "GABA-B Agonist/Spasticity","common_dosages": "5mg,10mg,20mg"},
        {"drug_name": "Tizanidine",        "drug_class": "Alpha-2 Agonist/Spasticity","common_dosages": "2mg,4mg"},
        {"drug_name": "Dantrolene",        "drug_class": "Muscle Relaxant/Spasticity","common_dosages": "25mg,50mg,100mg"},
        {"drug_name": "Botulinum Toxin A", "drug_class": "Neurotoxin/Spasticity/Dystonia","common_dosages": "50units,100units,200units"},

        # ── MYASTHENIA GRAVIS ────────────────────────────────────────────────
        {"drug_name": "Pyridostigmine",    "drug_class": "Cholinesterase Inhibitor/MG","common_dosages": "30mg,60mg"},
        {"drug_name": "Eculizumab",        "drug_class": "Complement Inhibitor/MG",  "common_dosages": "300mg/30mL"},
        {"drug_name": "Efgartigimod",      "drug_class": "FcRn Antagonist/MG",       "common_dosages": "1g/20mL"},

        # ── HUNTINGTON'S / TARDIVE DYSKINESIA ───────────────────────────────
        {"drug_name": "Tetrabenazine",     "drug_class": "VMAT2 Inhibitor/Huntington","common_dosages": "12.5mg,25mg"},
        {"drug_name": "Deutetrabenazine",  "drug_class": "VMAT2 Inhibitor/Huntington","common_dosages": "6mg,9mg,12mg"},
        {"drug_name": "Valbenazine",       "drug_class": "VMAT2 Inhibitor/Tardive Dyskinesia","common_dosages": "40mg,80mg"},

        # ── SLEEP / NARCOLEPSY ───────────────────────────────────────────────
        {"drug_name": "Modafinil",         "drug_class": "Wakefulness Promoter/Narcolepsy","common_dosages": "100mg,200mg"},
        {"drug_name": "Armodafinil",       "drug_class": "Wakefulness Promoter/Narcolepsy","common_dosages": "50mg,150mg,200mg,250mg"},
        {"drug_name": "Sodium Oxybate",    "drug_class": "CNS Depressant/Narcolepsy","common_dosages": "500mg/mL"},
        {"drug_name": "Pitolisant",        "drug_class": "H3 Antagonist/Narcolepsy", "common_dosages": "4.45mg,17.8mg"},

        # ── CORTICOSTEROIDS (MS relapse + neuro-inflammation) ────────────────
        {"drug_name": "Methylprednisolone","drug_class": "Corticosteroid/MS Relapse","common_dosages": "4mg,8mg,16mg,32mg"},
        {"drug_name": "Prednisone",        "drug_class": "Corticosteroid/Neuroinflammation","common_dosages": "1mg,5mg,10mg,20mg,50mg"},

        # ── NEUROPATHIC PAIN ─────────────────────────────────────────────────
        {"drug_name": "Duloxetine",        "drug_class": "SNRI/Neuropathic Pain",    "common_dosages": "20mg,30mg,60mg"},
        {"drug_name": "Tramadol",          "drug_class": "Opioid/Neuropathic Pain",  "common_dosages": "50mg,100mg"},
        {"drug_name": "Capsaicin",         "drug_class": "Topical/Neuropathic Pain", "common_dosages": "0.025%,0.075%,8%"},
        {"drug_name": "Lidocaine",         "drug_class": "Local Anesthetic/Neuropathic Pain","common_dosages": "5% patch"},
    ]

    with app.app_context():
        added = 0
        for m in MEDICATIONS:
            exists = ReferenceMedication.query.filter_by(
                drug_name=m["drug_name"]
            ).first()
            if not exists:
                db.session.add(ReferenceMedication(**m))
                added += 1
        db.session.commit()
        print(f"Medication seed: {len(MEDICATIONS)} in list, "
              f"inserted {added} new "
              f"(skipped {len(MEDICATIONS) - added} existing).")
        
#--------------ReferenceVitalRange---------------

def seed_vital_ranges(app):
    VITAL_RANGES = [
        {"vital_name": "systolic_bp",       "min_value": 70,  "max_value": 250,  "unit": "mmHg"},
        {"vital_name": "diastolic_bp",      "min_value": 40,  "max_value": 150,  "unit": "mmHg"},
        {"vital_name": "heart_rate",        "min_value": 30,  "max_value": 200,  "unit": "bpm"},
        {"vital_name": "weight_kg",         "min_value": 2,   "max_value": 300,  "unit": "kg"},
        {"vital_name": "temperature_f",     "min_value": 90,  "max_value": 108,  "unit": "°F"},
        {"vital_name": "respiratory_rate",  "min_value": 8,   "max_value": 40,   "unit": "br/min"},
        {"vital_name": "oxygen_saturation", "min_value": 70,  "max_value": 100,  "unit": "%"},
        {"vital_name": "sodium_meq_l",      "min_value": 120, "max_value": 160,  "unit": "mEq/L"},
        {"vital_name": "potassium_meq_l",   "min_value": 2.5, "max_value": 6.5,  "unit": "mEq/L"},
        {"vital_name": "creatinine_mg_dl",  "min_value": 0.3, "max_value": 10.0, "unit": "mg/dL"},
        {"vital_name": "glucose_mg_dl",     "min_value": 40,  "max_value": 500,  "unit": "mg/dL"},
        {"vital_name": "hemoglobin_g_dl",   "min_value": 4.0, "max_value": 20.0, "unit": "g/dL"},
        {"vital_name": "wbc_k_ul",          "min_value": 1.0, "max_value": 30.0, "unit": "K/uL"},
        {"vital_name": "platelet_k_ul",     "min_value": 50,  "max_value": 600,  "unit": "K/uL"},
    ]

    with app.app_context():
        added = 0
        for v in VITAL_RANGES:
            exists = ReferenceVitaRange.query.filter_by(
                vital_name=v["vital_name"]
            ).first()
            if not exists:
                db.session.add(ReferenceVitaRange(**v))
                added += 1
        db.session.commit()
        print(f"Vital ranges seed: {len(VITAL_RANGES)} in list, "
              f"inserted {added} new "
              f"(skipped {len(VITAL_RANGES) - added} existing).")

def build_app():
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    return app

if __name__ == '__main__':
    app = build_app()
    seed_icd10(app)
    seed_medications(app)
    seed_vital_ranges(app)
