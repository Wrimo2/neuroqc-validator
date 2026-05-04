from flask import Flask, render_template, request, flash, redirect, url_for
from config import config
from validators import run_all_validators
from models.db_models import db, QCBatch, QCResult, QCErrorDetail
import json
from datetime import datetime

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

with app.app_context():
    db.create_all() #creates all tables if they don't exist

@app.route("/")
def index():
    return render_template('upload.html')

@app.route("/dashboard")
def dashboard():
    return 'Dashboard coming soon'

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('No file was selected','error')
        return redirect(url_for('index'))
    
    #check extension
    if not file.filename.lower().endswith('.json'):
        flash('Please upload a file with a .json extension.','error')
        return redirect(url_for('index'))

    try:
        records= json.load(file)
    except json.JSONDecodeError as e:
        flash(f'Invalid JSON: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    #accept either a list of records or a single record object
    if isinstance(records, dict):
        records = [records]
    elif not isinstance(records, list):
        flash('JSON must be a list of records or a single record object.', 'error')
        return redirect(url_for('index'))
    
    if len(records) == 0:
        flash('The JSON file contained no records', 'error')
        return redirect(url_for('index'))

    #Create the batch record
    existing = QCBatch.query.filter_by(filename=file.filename).first()
    if existing:
        for r in existing.results:
            db.session.delete(r)
        existing.total_records = len(records)   
        existing.uploaded_at = datetime.utcnow()
        existing.pass_count = 0
        existing.warning_count = 0
        existing.fail_count = 0
        db.session.flush()
        batch = existing
    else:
        batch = QCBatch(
        filename = file.filename,
        total_records = len(records)
        )
        db.session.add(batch)
        db.session.flush()

    #counters for the batch summary
    pass_count = 0
    warn_count = 0
    fail_count = 0

    for record in records:
        result = run_all_validators(record)

        #track status count
        if result['status'] == 'PASS':
            pass_count += 1
        elif result['status'] == 'WARNING':
            warn_count += 1
        else: #fail
            fail_count += 1
        
        qc_result = QCResult(
            batch_id = batch.id,
            patient_id = record.get('patient_id', 'UNKNOWN'),
            overall_status = result['status'],
            ocr_confidence = record.get('ocr_confidence'),
            error_summary = {
                'total': len(result['errors']),
                'critical': sum(1 for e in result['errors'] if e['severity'] == 'CRITICAL'),
                'warning': sum(1 for e in result['errors'] if e['severity'] == 'WARNING'),
                'info': sum(1 for e in result['errors'] if e['severity'] == 'INFO'),
            }
        )
        db.session.add(qc_result)
        db.session.flush() #get the qc_result.id for the error_details rows
        
        for error in result['errors']:
            detail = QCErrorDetail(
                result_id = qc_result.id,
                error_category = error['category'],
                severity = error['severity'],
                field_name = error['field'],
                error_message = error['message'],
                suggestion = error.get('suggestion', '')
            )
            db.session.add(detail)

    #finalising batch, commit, redirect -------
    batch.pass_count = pass_count
    batch.warning_count = warn_count
    batch.fail_count = fail_count

    db.session.commit()
    flash(f'Successfully validated {len(records)} records.', 'success')
    return redirect(url_for('batch_detail', batch_id=batch.id))

@app.route('/batch/<int:batch_id>')
def batch_detail(batch_id):
    batch = QCBatch.query.get_or_404(batch_id)
    results = QCResult.query.filter_by(batch_id=batch_id).order_by(QCResult.id).all()
    return render_template('batch_detail.html', batch=batch, results=results)

@app.route('/record/<int:result_id>')
def record_details(result_id):
    result = QCResult.query.get_or_404(result_id)
    errors = QCErrorDetail.query.filter_by(result_id=result_id).all()

    #group errors by category for cleaner display
    errors_by_category = {}
    for e in errors:
        if e.error_category not in errors_by_category:
            errors_by_category[e.error_category] = []
        errors_by_category[e.error_category].append(e)
    return render_template('record_detail.html', result=result, errors_by_category=errors_by_category)

if __name__ == '__main__':
    app.run(debug = True)
