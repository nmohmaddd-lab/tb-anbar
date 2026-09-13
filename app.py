from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = 'anbar_tb_secret_2026'
DB = 'database.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL, age INTEGER, gender TEXT,
        address TEXT, phone TEXT, disease_type TEXT,
        treatment_start DATE, treatment_end DATE, last_visit DATE,
        status TEXT DEFAULT 'قيد العلاج', notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL, visit_date DATE, visit_type TEXT,
        weight REAL, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE)""")
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        patients = conn.execute("SELECT * FROM patients WHERE full_name LIKE ? OR phone LIKE ? OR address LIKE ? ORDER BY id DESC", (f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    else:
        patients = conn.execute('SELECT * FROM patients ORDER BY id DESC').fetchall()
    total = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    under_treatment = conn.execute("SELECT COUNT(*) FROM patients WHERE status='قيد العلاج'").fetchone()[0]
    recovered = conn.execute("SELECT COUNT(*) FROM patients WHERE status='متعافي'").fetchone()[0]
    conn.close()
    return render_template('index.html', patients=patients, q=q, total=total, under_treatment=under_treatment, recovered=recovered, is_admin=False)

@app.route('/admin')
def admin():
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        patients = conn.execute("SELECT * FROM patients WHERE full_name LIKE ? OR phone LIKE ? OR address LIKE ? ORDER BY id DESC", (f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    else:
        patients = conn.execute('SELECT * FROM patients ORDER BY id DESC').fetchall()
    total = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    under_treatment = conn.execute("SELECT COUNT(*) FROM patients WHERE status='قيد العلاج'").fetchone()[0]
    recovered = conn.execute("SELECT COUNT(*) FROM patients WHERE status='متعافي'").fetchone()[0]
    conn.close()
    return render_template('index.html', patients=patients, q=q, total=total, under_treatment=under_treatment, recovered=recovered, is_admin=True)

@app.route('/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        data = (request.form['full_name'], request.form.get('age') or None, request.form.get('gender'),
                request.form.get('address'), request.form.get('phone'), request.form.get('disease_type'),
                request.form.get('treatment_start') or None, request.form.get('treatment_end') or None,
                request.form.get('last_visit') or None, request.form.get('status'), request.form.get('notes'))
        conn = get_db()
        conn.execute("INSERT INTO patients (full_name, age, gender, address, phone, disease_type, treatment_start, treatment_end, last_visit, status, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data)
        conn.commit(); conn.close()
        flash('تمت إضافة المريض بنجاح', 'success')
        return redirect(url_for('admin'))
    return render_template('add_patient.html')

@app.route('/edit/<int:pid>', methods=['GET', 'POST'])
def edit_patient(pid):
    conn = get_db()
    patient = conn.execute('SELECT * FROM patients WHERE id=?', (pid,)).fetchone()
    if not patient:
        conn.close(); flash('المريض غير موجود', 'danger')
        return redirect(url_for('admin'))
    if request.method == 'POST':
        data = (request.form['full_name'], request.form.get('age') or None, request.form.get('gender'),
                request.form.get('address'), request.form.get('phone'), request.form.get('disease_type'),
                request.form.get('treatment_start') or None, request.form.get('treatment_end') or None,
                request.form.get('last_visit') or None, request.form.get('status'), request.form.get('notes'), pid)
        conn.execute("UPDATE patients SET full_name=?, age=?, gender=?, address=?, phone=?, disease_type=?, treatment_start=?, treatment_end=?, last_visit=?, status=?, notes=? WHERE id=?", data)
        conn.commit(); conn.close()
        flash('تم تعديل بيانات المريض', 'success')
        return redirect(url_for('admin'))
    conn.close()
    return render_template('edit_patient.html', patient=patient)

@app.route('/delete/<int:pid>')
def delete_patient(pid):
    conn = get_db()
    conn.execute('DELETE FROM patients WHERE id=?', (pid,))
    conn.commit(); conn.close()
    flash('تم حذف المريض', 'warning')
    return redirect(url_for('admin'))

@app.route('/patient/<int:pid>')
def patient_detail(pid):
    conn = get_db()
    patient = conn.execute('SELECT * FROM patients WHERE id=?', (pid,)).fetchone()
    if not patient:
        conn.close(); flash('المريض غير موجود', 'danger')
        return redirect(url_for('index'))
    visits = conn.execute('SELECT * FROM visits WHERE patient_id=? ORDER BY visit_date DESC', (pid,)).fetchall()
    conn.close()
    return render_template('patient_detail.html', patient=patient, visits=visits)

@app.route('/patient/<int:pid>/add_visit', methods=['GET', 'POST'])
def add_visit(pid):
    conn = get_db()
    patient = conn.execute('SELECT * FROM patients WHERE id=?', (pid,)).fetchone()
    if not patient:
        conn.close(); flash('المريض غير موجود', 'danger')
        return redirect(url_for('admin'))
    if request.method == 'POST':
        visit_date = request.form.get('visit_date')
        visit_type = request.form.get('visit_type')
        weight = request.form.get('weight') or None
        notes = request.form.get('notes')
        conn.execute('INSERT INTO visits (patient_id, visit_date, visit_type, weight, notes) VALUES (?,?,?,?,?)', (pid, visit_date, visit_type, weight, notes))
        conn.execute('UPDATE patients SET last_visit=? WHERE id=?', (visit_date, pid))
        conn.commit(); conn.close()
        flash('تمت إضافة الزيارة', 'success')
        return redirect(url_for('patient_detail', pid=pid))
    conn.close()
    return render_template('add_visit.html', patient=patient)

@app.route('/visit/delete/<int:vid>')
def delete_visit(vid):
    conn = get_db()
    visit = conn.execute('SELECT * FROM visits WHERE id=?', (vid,)).fetchone()
    if visit:
        pid = visit['patient_id']
        conn.execute('DELETE FROM visits WHERE id=?', (vid,))
        conn.commit(); conn.close()
        flash('تم حذف الزيارة', 'warning')
        return redirect(url_for('patient_detail', pid=pid))
    conn.close()
    return redirect(url_for('admin'))

@app.route('/backup')
def backup():
    return send_file(DB, as_attachment=True, download_name=f'backup_{date.today()}.db')


# ==================== تحميل مسارات استيراد Excel ====================
from import_excel_patch import register_import_routes
register_import_routes(app, get_db, render_template, request, redirect, url_for, flash, send_file)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
