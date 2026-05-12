from flask import Flask, render_template, request, flash, redirect, url_for
from config import config
from validators import run_all_validators
from models.db_models import db, QCBatch, QCResult, QCErrorDetail
import json
from datetime import datetime
from sqlalchemy import func

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
    #all batches, newest first, for the trend chart
    batches = QCBatch.query.order_by(QCBatch.uploaded_at.desc()).limit(10).all()

    #aggregation 1: error count per category (for the pie chart)
    error_dist = db.session.query(QCErrorDetail.error_category,func.count(QCErrorDetail.id)).group_by(QCErrorDetail.error_category).all()

    #aggregation 2: error count per severity (for the doughnut chart)
    severity_dist = db.session.query(QCErrorDetail.severity,func.count(QCErrorDetail.id)).group_by(QCErrorDetail.severity).all()

    #reshape data for chart.js - separate levels and counts
    error_labels = [row[0] for row in error_dist]
    error_counts = [row[1] for row in error_dist]
    severity_labels = [row[0] for row in severity_dist]
    severity_counts = [row[1] for row in severity_dist]

    #reshape batch data for stacked bar chart
    batch_labels = [b.filename[:20] for b in reversed(batches)]
    batch_pass = [b.pass_count for b in reversed(batches)]
    batch_warning = [b.warning_count for b in reversed(batches)]
    batch_fail = [b.fail_count for b in reversed(batches)]

    #top level summary stats for the cards at the top of the dashboard
    total_batches = QCBatch.query.count()
    total_records = db.session.query(func.sum(QCBatch.total_records)).scalar() or 0
    total_errors = QCErrorDetail.query.count()
    total_critical = QCErrorDetail.query.filter_by(severity='CRITICAL').count()

    return render_template('dashboard.html',
                           batches = batches,
                           error_labels = error_labels,
                           error_counts = error_counts,
                           severity_labels = severity_labels,
                           severity_counts = severity_counts,
                           batch_labels = batch_labels,
                           batch_pass = batch_pass,
                           batch_warning = batch_warning,
                           batch_fail = batch_fail,
                           total_batches = total_batches,
                           total_records = total_records,
                           total_errors = total_errors,
                           total_critical = total_critical)

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

    existing_batch = QCBatch.query.filter_by(filename=file.filename).first()

    # --- Run validation on all records (ALWAYS happens) ---
    all_results = []
    pass_count = warn_count = fail_count = 0

    for record in records:
        result = run_all_validators(record)
        if result['status'] == 'PASS':
            pass_count += 1
        elif result['status'] == 'WARNING':
            warn_count += 1
        else:
            fail_count += 1
        all_results.append({'record': record, 'result': result})

    if existing_batch:
        # RE-UPLOAD → show results, do NOT touch DB
        flash('This file was already uploaded. Showing validation preview (not saved).', 'info')
        preview_results = []
        for item in all_results:
            rec, res = item['record'], item['result']
            preview_results.append({
                'patient_id': rec.get('patient_id', 'UNKNOWN'),
                'overall_status': res['status'],
                'ocr_confidence': rec.get('ocr_confidence'),
                'error_summary': {
                    'total': len(res['errors']),
                    'critical': sum(1 for e in res['errors'] if e['severity'] == 'CRITICAL'),
                    'warning': sum(1 for e in res['errors'] if e['severity'] == 'WARNING'),
                    'info': sum(1 for e in res['errors'] if e['severity'] == 'INFO'),
                },
                'errors': res['errors']
            })
        preview_batch = {
            'filename': file.filename,
            'total_records': len(records),
            'pass_count': pass_count,
            'warning_count': warn_count,
            'fail_count': fail_count,
        }
        return render_template('batch_detail.html', batch=preview_batch, results=preview_results, is_preview=True)

    else:
        # FIRST UPLOAD → save to DB (existing logic, unchanged)
        batch = QCBatch(filename=file.filename, total_records=len(records))
        db.session.add(batch)
        db.session.flush()
        for item in all_results:
            rec, res = item['record'], item['result']
            qc_result = QCResult(
                batch_id=batch.id,
                patient_id=rec.get('patient_id', 'UNKNOWN'),
                overall_status=res['status'],
                ocr_confidence=rec.get('ocr_confidence'),
                error_summary={ 'total': len(result['errors']),
                'critical': sum(1 for e in result['errors'] if e['severity'] == 'CRITICAL'),
                'warning': sum(1 for e in result['errors'] if e['severity'] == 'WARNING'),
                'info': sum(1 for e in result['errors'] if e['severity'] == 'INFO') }  
            )
            db.session.add(qc_result)
            db.session.flush()
            for error in res['errors']:
                detail = QCErrorDetail(
                result_id=qc_result.id, 
                error_category = error['category'],
                severity = error['severity'],
                field_name = error['field'],
                error_message = error['message'],
                suggestion = error.get('suggestion', '')) 
                db.session.add(detail)
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
