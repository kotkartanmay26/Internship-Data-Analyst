"""
Puja Fluid Seals Pvt Ltd - Professional Dark Theme Dashboard
With beautiful graphs, dark theme, and complete employee management
Run: python employee_dashboard.py
"""

import sqlite3
import io
import csv
import re
import os
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file
import pandas as pd
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'puja_fluid_seals_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Database Setup
def init_db():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT,
        name TEXT NOT NULL,
        doj TEXT,
        gender TEXT,
        department TEXT,
        designation TEXT,
        experience REAL,
        documents_in_file TEXT,
        pan TEXT,
        aadhar TEXT,
        dob TEXT,
        driving_license TEXT,
        voter_id TEXT,
        passport TEXT,
        light_bill TEXT,
        ration_card TEXT,
        educational_certificate TEXT,
        status TEXT DEFAULT 'Active'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS upload_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        upload_date TEXT,
        record_count INTEGER
    )''')
    
    conn.commit()
    conn.close()

init_db()

def parse_date(date_value):
    if pd.isna(date_value) or str(date_value).strip() == '':
        return None
    date_str = str(date_value).strip()
    if isinstance(date_value, (int, float)) and 30000 < date_value < 50000:
        try:
            return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date_value) - 2).strftime('%Y-%m-%d')
        except:
            pass
    
    if '/' in date_str and len(date_str.split('/')) > 3:
        date_str = date_str.split('/')[0]
    if '-' in date_str and len(date_str.split('-')) > 3:
        date_str = date_str.split('-')[0]
    
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%d.%m.%Y', '%d.%m.%y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except:
            continue
    return None

def calculate_experience(doj_str):
    if not doj_str:
        return 0
    try:
        doj = datetime.strptime(doj_str, '%Y-%m-%d')
        today = datetime.now()
        if doj > today:
            return 0
        years = today.year - doj.year
        if today.month < doj.month or (today.month == doj.month and today.day < doj.day):
            years -= 1
        return round(years + (today.month - doj.month) / 12, 1)
    except:
        return 0

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def clean_boolean(value):
    if pd.isna(value):
        return "No"
    v = str(value).strip().lower()
    return "Yes" if v in ['yes', 'y', 'true', '1', '✓'] else "No"

def clean_department(dept):
    if pd.isna(dept) or str(dept).strip() == '':
        return "Other"
    dept = str(dept).strip()
    mapping = {
        'ACCOUNTS': 'Accounts', 'FINANCE': 'Finance', 'HR': 'HR',
        'MARKETING': 'Marketing', 'PRODUCTION': 'Production',
        'QA': 'Quality', 'TOOLROOM': 'Toolroom', 'FINISHING': 'Finishing',
        'COMPOUNDING': 'Compounding', 'DESIGN': 'Design', 'PURCHASE': 'Purchase'
    }
    for k, v in mapping.items():
        if k in dept.upper():
            return v
    return dept[:20]

def process_excel(file_path):
    try:
        df = pd.read_excel(file_path, header=None)
        
        # Find headers
        start_row = 0
        for idx, row in df.iterrows():
            row_str = ' '.join(str(v) for v in row.values if pd.notna(v))
            if 'SR.NO.' in row_str and 'NAME' in row_str:
                start_row = idx + 1
                break
        
        if start_row == 0:
            for idx, row in df.iterrows():
                first = row[0]
                if pd.notna(first) and isinstance(first, (int, float)):
                    try:
                        if int(first) == 1:
                            start_row = idx
                            break
                    except:
                        pass
        
        employees = []
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            
            sr_no = row[0]
            if pd.isna(sr_no):
                continue
            try:
                sr_int = int(float(sr_no))
            except:
                continue
            
            name = clean_text(row[1])
            if not name or len(name) < 2:
                continue
            
            doj = parse_date(row[2]) if len(row) > 2 else None
            gender = clean_text(row[3]) if len(row) > 3 else "Not Specified"
            department = clean_department(row[4]) if len(row) > 4 else "Other"
            designation = clean_text(row[5]) if len(row) > 5 else ""
            
            exp_val = 0
            if len(row) > 6 and pd.notna(row[6]):
                try:
                    exp_val = float(row[6])
                except:
                    exp_val = calculate_experience(doj)
            else:
                exp_val = calculate_experience(doj)
            
            pan = clean_text(row[8]) if len(row) > 8 else ""
            aadhar = clean_text(row[9]) if len(row) > 9 else ""
            dob = parse_date(row[10]) if len(row) > 10 else None
            driving = clean_boolean(row[11]) if len(row) > 11 else "No"
            voter = clean_boolean(row[12]) if len(row) > 12 else "No"
            passport = clean_boolean(row[13]) if len(row) > 13 else "No"
            light = clean_boolean(row[14]) if len(row) > 14 else "No"
            ration = clean_boolean(row[15]) if len(row) > 15 else "No"
            edu = clean_boolean(row[16]) if len(row) > 16 else "No"
            
            employees.append({
                'emp_id': str(sr_int),
                'name': name,
                'doj': doj,
                'gender': gender.capitalize() if gender else "Not Specified",
                'department': department,
                'designation': designation,
                'experience': max(0, exp_val),
                'pan': pan,
                'aadhar': aadhar,
                'dob': dob,
                'documents': "Yes",
                'driving': driving,
                'voter': voter,
                'passport': passport,
                'light': light,
                'ration': ration,
                'edu': edu
            })
        
        conn = sqlite3.connect('employees.db')
        c = conn.cursor()
        c.execute('DELETE FROM employees')
        
        for emp in employees:
            c.execute('''INSERT INTO employees 
                (employee_id, name, doj, gender, department, designation, experience, 
                 documents_in_file, pan, aadhar, dob, driving_license, voter_id, 
                 passport, light_bill, ration_card, educational_certificate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (emp['emp_id'], emp['name'], emp['doj'], emp['gender'],
                 emp['department'], emp['designation'], emp['experience'],
                 emp['documents'], emp['pan'], emp['aadhar'], emp['dob'],
                 emp['driving'], emp['voter'], emp['passport'], emp['light'],
                 emp['ration'], emp['edu'], 'Active'))
        
        c.execute('INSERT INTO upload_history (filename, upload_date, record_count) VALUES (?, ?, ?)',
                  (os.path.basename(file_path), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(employees)))
        
        conn.commit()
        conn.close()
        return len(employees)
    
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def get_all_employees():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('SELECT * FROM employees ORDER BY employee_id')
    data = c.fetchall()
    conn.close()
    return data

def search_employees(term):
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    pattern = f'%{term}%'
    c.execute('''SELECT * FROM employees 
                 WHERE name LIKE ? OR department LIKE ? OR designation LIKE ? 
                 OR pan LIKE ? OR aadhar LIKE ? OR employee_id LIKE ?
                 ORDER BY employee_id''',
              (pattern, pattern, pattern, pattern, pattern, pattern))
    data = c.fetchall()
    conn.close()
    return data

def get_employee_by_id(eid):
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('SELECT * FROM employees WHERE id = ?', (eid,))
    data = c.fetchone()
    conn.close()
    return data

def get_stats():
    employees = get_all_employees()
    total = len(employees)
    depts = len(set(e[5] for e in employees if e[5]))
    avg_exp = round(sum(e[7] or 0 for e in employees) / total, 1) if total > 0 else 0
    has_pan = sum(1 for e in employees if e[9] and e[9] != '')
    has_aadhar = sum(1 for e in employees if e[10] and e[10] != '')
    male = sum(1 for e in employees if e[4] == 'Male')
    female = sum(1 for e in employees if e[4] == 'Female')
    return {'total': total, 'departments': depts, 'avgExp': avg_exp, 'pan': has_pan, 'aadhar': has_aadhar, 'male': male, 'female': female}

def get_dept_stats():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('''SELECT department, COUNT(*) FROM employees 
                 WHERE department IS NOT NULL AND department != ''
                 GROUP BY department ORDER BY COUNT(*) DESC LIMIT 8''')
    data = c.fetchall()
    conn.close()
    return data

def get_exp_stats():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('''SELECT 
        CASE 
            WHEN experience < 1 THEN '< 1 Year'
            WHEN experience < 3 THEN '1-3 Years'
            WHEN experience < 5 THEN '3-5 Years'
            WHEN experience < 10 THEN '5-10 Years'
            ELSE '10+ Years'
        END as range,
        COUNT(*) FROM employees GROUP BY range''')
    data = c.fetchall()
    conn.close()
    return data

# HTML Template - Professional Dark Theme
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Puja Fluid Seals | HR Analytics Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0c10;
            color: #e4e6eb;
        }
        
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #1a1d24; border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #60a5fa; }
        
        .container { max-width: 1600px; margin: 0 auto; padding: 24px; }
        
        /* Upload Card */
        .upload-card {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 32px;
            padding: 60px 40px;
            text-align: center;
            border: 1px solid rgba(59,130,246,0.2);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }
        .upload-area {
            border: 3px dashed rgba(59,130,246,0.3);
            border-radius: 28px;
            padding: 70px 40px;
            transition: all 0.3s;
            cursor: pointer;
            background: rgba(59,130,246,0.02);
        }
        .upload-area:hover { border-color: #3b82f6; background: rgba(59,130,246,0.05); transform: scale(1.01); }
        .upload-icon { font-size: 80px; color: #3b82f6; margin-bottom: 24px; }
        .upload-title { font-size: 28px; font-weight: 700; background: linear-gradient(135deg, #fff, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }
        .upload-subtitle { color: #6b7280; margin-bottom: 28px; }
        .upload-btn {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            padding: 14px 36px;
            border-radius: 40px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        .upload-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px -5px #3b82f6; }
        
        /* Dashboard Header */
        .dashboard-header {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 24px;
            padding: 28px 32px;
            margin-bottom: 28px;
            border: 1px solid rgba(59,130,246,0.15);
            backdrop-filter: blur(10px);
        }
        .dashboard-header h1 { font-size: 28px; font-weight: 700; background: linear-gradient(135deg, #fff, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .dashboard-header p { color: #6b7280; margin-top: 6px; font-size: 14px; }
        
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 22px;
            margin-bottom: 28px;
        }
        .stat-card {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 20px;
            padding: 22px;
            border: 1px solid rgba(59,130,246,0.15);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(59,130,246,0.1), transparent);
            transition: left 0.5s;
        }
        .stat-card:hover::before { left: 100%; }
        .stat-card:hover { transform: translateY(-4px); border-color: #3b82f6; }
        .stat-icon {
            width: 52px;
            height: 52px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            margin-bottom: 16px;
            background: rgba(59,130,246,0.15);
        }
        .stat-value { font-size: 36px; font-weight: 800; color: #fff; }
        .stat-label { font-size: 13px; color: #6b7280; margin-top: 6px; font-weight: 500; letter-spacing: 0.5px; }
        
        /* Search Card */
        .search-card {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 20px;
            padding: 20px 24px;
            margin-bottom: 28px;
            border: 1px solid rgba(59,130,246,0.15);
        }
        .search-wrapper { position: relative; }
        .search-icon {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: #6b7280;
        }
        .search-input {
            width: 100%;
            padding: 14px 20px 14px 52px;
            background: #0e1117;
            border: 1px solid #2d3748;
            border-radius: 40px;
            font-size: 14px;
            color: #e4e6eb;
            transition: all 0.3s;
        }
        .search-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.2); }
        .search-input::placeholder { color: #4a5568; }
        
        /* Charts Grid */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 24px;
            margin-bottom: 28px;
        }
        .chart-card {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 20px;
            padding: 22px;
            border: 1px solid rgba(59,130,246,0.15);
            transition: transform 0.3s;
        }
        .chart-card:hover { transform: translateY(-2px); border-color: #3b82f6; }
        .chart-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid #2d3748;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .chart-title i { color: #3b82f6; font-size: 18px; }
        canvas { max-height: 280px; width: 100% !important; }
        
        /* Table Card */
        .table-card {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(59,130,246,0.15);
        }
        .table-header {
            padding: 20px 24px;
            border-bottom: 1px solid #2d3748;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .table-header h3 { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 10px; }
        .export-btn {
            padding: 8px 18px;
            border-radius: 30px;
            border: none;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .export-btn:hover { transform: translateY(-1px); }
        .btn-csv { background: #22c55e; color: white; }
        .btn-excel { background: #10b981; color: white; }
        .btn-pdf { background: #ef4444; color: white; }
        
        .table-wrapper {
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
        }
        .employee-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        .employee-table th {
            background: #0e1117;
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: #9ca3af;
            border-bottom: 1px solid #2d3748;
            position: sticky;
            top: 0;
        }
        .employee-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #1f2937;
        }
        .employee-table tr:hover { background: rgba(59,130,246,0.05); }
        .view-btn {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .view-btn:hover { transform: scale(1.05); }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(8px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: linear-gradient(145deg, #12151c, #0e1117);
            border-radius: 28px;
            max-width: 700px;
            width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            border: 1px solid rgba(59,130,246,0.3);
        }
        .modal-header {
            padding: 22px 28px;
            border-bottom: 1px solid #2d3748;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            background: #12151c;
        }
        .modal-header h2 { font-size: 22px; color: #fff; }
        .close-modal { font-size: 28px; cursor: pointer; color: #6b7280; transition: color 0.2s; }
        .close-modal:hover { color: #ef4444; }
        .modal-body { padding: 28px; }
        .detail-section { margin-bottom: 28px; }
        .detail-section h3 {
            font-size: 16px;
            color: #3b82f6;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #2d3748;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }
        .detail-item { display: flex; }
        .detail-label { width: 110px; font-weight: 600; color: #9ca3af; }
        .detail-value { flex: 1; color: #e4e6eb; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(34,197,94,0.2);
            color: #22c55e;
        }
        .loading { text-align: center; padding: 50px; color: #6b7280; }
        .total-badge {
            background: #3b82f6;
            color: white;
            padding: 4px 12px;
            border-radius: 30px;
            font-size: 12px;
            margin-left: 12px;
        }
        
        @media (max-width: 768px) {
            .detail-grid { grid-template-columns: 1fr; }
            .charts-grid { grid-template-columns: 1fr; }
            .container { padding: 16px; }
        }
    </style>
</head>
<body>
<div class="container">
    <div id="uploadSection" class="upload-card">
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon"><i class="fas fa-cloud-upload-alt"></i></div>
            <div class="upload-title">Upload Employee Data</div>
            <div class="upload-subtitle">Drag & drop or click to upload Excel file (.xlsx, .xls)</div>
            <input type="file" id="fileInput" accept=".xlsx,.xls" style="display:none">
            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                <i class="fas fa-folder-open"></i> Browse Files
            </button>
            <div id="uploadProgress" style="margin-top: 24px; display:none">
                <div style="width:100%; background:#2d3748; border-radius:30px; overflow:hidden">
                    <div id="progressBar" style="width:0%; height:4px; background:#3b82f6; transition:width 0.3s; border-radius:30px"></div>
                </div>
                <p style="margin-top:12px; color:#6b7280">Processing...</p>
            </div>
        </div>
        <div id="uploadStatus" style="margin-top: 20px"></div>
    </div>

    <div id="dashboardSection" style="display:none">
        <div class="dashboard-header">
            <h1><i class="fas fa-chart-line"></i> HR Analytics Dashboard</h1>
            <p>Puja Fluid Seals Pvt Ltd - Complete Workforce Analytics</p>
        </div>

        <div class="stats-grid" id="statsGrid"></div>

        <div class="search-card">
            <div class="search-wrapper">
                <i class="fas fa-search search-icon"></i>
                <input type="text" id="searchInput" class="search-input" 
                       placeholder="Search by Name, Department, Designation, PAN, Aadhar, or Employee ID...">
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title"><i class="fas fa-building"></i> Department Distribution</div>
                <canvas id="deptChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title"><i class="fas fa-chart-line"></i> Experience Distribution</div>
                <canvas id="expChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title"><i class="fas fa-id-card"></i> Document Status</div>
                <canvas id="docChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title"><i class="fas fa-chart-pie"></i> Department Share</div>
                <canvas id="deptPieChart"></canvas>
            </div>
        </div>

        <div class="table-card">
            <div class="table-header">
                <h3><i class="fas fa-users"></i> Employee Directory <span id="totalEmployeesBadge" class="total-badge"></span></h3>
                <div>
                    <button class="export-btn btn-csv" onclick="exportCSV()"><i class="fas fa-file-csv"></i> CSV</button>
                    <button class="export-btn btn-excel" onclick="exportExcel()"><i class="fas fa-file-excel"></i> Excel</button>
                    <button class="export-btn btn-pdf" onclick="exportPDF()"><i class="fas fa-file-pdf"></i> PDF</button>
                </div>
            </div>
            <div class="table-wrapper">
                <table class="employee-table">
                    <thead>
                        <tr><th>ID</th><th>Name</th><th>Department</th><th>Designation</th><th>Experience</th><th>PAN</th><th>Action</th></tr>
                    </thead>
                    <tbody id="employeeTableBody">
                        <tr><td colspan="7" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<div id="employeeModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2><i class="fas fa-user-circle"></i> Employee Details</h2>
            <span class="close-modal" onclick="closeModal()">&times;</span>
        </div>
        <div class="modal-body" id="modalBody"></div>
    </div>
</div>

<script>
    let currentEmployees = [];
    let deptChart, expChart, docChart, deptPieChart;

    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#3b82f6';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'rgba(59,130,246,0.3)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'rgba(59,130,246,0.3)';
        const file = e.dataTransfer.files[0];
        if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
            uploadFile(file);
        } else {
            showStatus('Please upload a valid Excel file', 'error');
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) uploadFile(e.target.files[0]);
    });

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        document.getElementById('uploadProgress').style.display = 'block';
        showStatus('Processing file...', 'info');

        try {
            const response = await fetch('/api/upload', { method: 'POST', body: formData });
            const result = await response.json();

            if (response.ok && result.success) {
                showStatus('✓ Successfully imported ' + result.count + ' employees!', 'success');
                setTimeout(() => {
                    document.getElementById('uploadSection').style.display = 'none';
                    document.getElementById('dashboardSection').style.display = 'block';
                    loadDashboard();
                }, 1500);
            } else {
                showStatus('✗ Error: ' + (result.error || 'Unknown error'), 'error');
                document.getElementById('uploadProgress').style.display = 'none';
            }
        } catch (error) {
            showStatus('✗ Upload failed: ' + error.message, 'error');
            document.getElementById('uploadProgress').style.display = 'none';
        }
    }

    function showStatus(message, type) {
        const statusDiv = document.getElementById('uploadStatus');
        const colors = { success: '#22c55e', error: '#ef4444', info: '#3b82f6' };
        statusDiv.innerHTML = '<div style="padding:14px; background:' + colors[type] + '20; border-radius:12px; color:' + colors[type] + '">' +
            '<i class="fas ' + (type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle') + '"></i> ' + message + '</div>';
        if (type !== 'error') setTimeout(() => { if (statusDiv.innerHTML.includes(message)) statusDiv.innerHTML = ''; }, 5000);
    }

    async function loadDashboard() {
        await loadEmployees();
        await loadStats();
        await loadCharts();
    }

    async function loadEmployees(searchTerm) {
        try {
            let url = '/api/employees';
            if (searchTerm) url = '/api/search?q=' + encodeURIComponent(searchTerm);
            const response = await fetch(url);
            currentEmployees = await response.json();
            
            const tbody = document.getElementById('employeeTableBody');
            if (!currentEmployees || currentEmployees.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="loading">No employees found</td></tr>';
                document.getElementById('totalEmployeesBadge').innerText = '0 Total';
                return;
            }
            
            document.getElementById('totalEmployeesBadge').innerText = currentEmployees.length + ' Total';
            
            let html = '';
            for (const emp of currentEmployees) {
                html += '<tr>' +
                    '<td>' + (emp[1] || '-') + '</td>' +
                    '<td><strong>' + escapeHtml(emp[2] || '') + '</strong></td>' +
                    '<td>' + escapeHtml(emp[5] || '-') + '</td>' +
                    '<td>' + escapeHtml(emp[6] || '-') + '</td>' +
                    '<td>' + (emp[7] ? emp[7] + ' yrs' : '-') + '</td>' +
                    '<td>' + (emp[9] || '-') + '</td>' +
                    '<td><button class="view-btn" onclick="viewDetails(' + emp[0] + ')"><i class="fas fa-eye"></i> View</button></td>' +
                    '</tr>';
            }
            tbody.innerHTML = html;
        } catch (error) { console.error(error); }
    }

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('statsGrid').innerHTML = 
                '<div class="stat-card"><div class="stat-icon" style="background:rgba(59,130,246,0.15); color:#3b82f6"><i class="fas fa-users"></i></div><div class="stat-value">' + stats.total + '</div><div class="stat-label">Total Employees</div></div>' +
                '<div class="stat-card"><div class="stat-icon" style="background:rgba(34,197,94,0.15); color:#22c55e"><i class="fas fa-venus-mars"></i></div><div class="stat-value">' + stats.male + 'M / ' + stats.female + 'F</div><div class="stat-label">Gender Ratio</div></div>' +
                '<div class="stat-card"><div class="stat-icon" style="background:rgba(245,158,11,0.15); color:#f59e0b"><i class="fas fa-building"></i></div><div class="stat-value">' + stats.departments + '</div><div class="stat-label">Departments</div></div>' +
                '<div class="stat-card"><div class="stat-icon" style="background:rgba(139,92,246,0.15); color:#8b5cf6"><i class="fas fa-chart-line"></i></div><div class="stat-value">' + stats.avgExp + '</div><div class="stat-label">Avg Experience (yrs)</div></div>' +
                '<div class="stat-card"><div class="stat-icon" style="background:rgba(59,130,246,0.15); color:#3b82f6"><i class="fas fa-id-card"></i></div><div class="stat-value">' + stats.pan + '</div><div class="stat-label">With PAN</div></div>' +
                '<div class="stat-card"><div class="stat-icon" style="background:rgba(59,130,246,0.15); color:#3b82f6"><i class="fas fa-fingerprint"></i></div><div class="stat-value">' + stats.aadhar + '</div><div class="stat-label">With Aadhar</div></div>';
        } catch (error) { console.error(error); }
    }

    async function loadCharts() {
        try {
            const response = await fetch('/api/charts');
            const data = await response.json();
            
            if (deptChart) deptChart.destroy();
            deptChart = new Chart(document.getElementById('deptChart'), {
                type: 'bar',
                data: { labels: data.departments.map(d => d[0]), datasets: [{ label: 'Employees', data: data.departments.map(d => d[1]), backgroundColor: '#3b82f6', borderRadius: 8, barPercentage: 0.7 }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e4e6eb' } } } }
            });
            
            if (expChart) expChart.destroy();
            expChart = new Chart(document.getElementById('expChart'), {
                type: 'doughnut',
                data: { labels: data.experience.map(e => e[0]), datasets: [{ data: data.experience.map(e => e[1]), backgroundColor: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'], borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e4e6eb' } } } }
            });
            
            if (docChart) docChart.destroy();
            docChart = new Chart(document.getElementById('docChart'), {
                type: 'bar',
                data: { labels: ['PAN Card', 'Aadhar Card'], datasets: [{ label: 'Documents Available', data: [data.hasPAN, data.hasAadhar], backgroundColor: ['#22c55e', '#3b82f6'], borderRadius: 8 }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e4e6eb' } } } }
            });
            
            if (deptPieChart) deptPieChart.destroy();
            deptPieChart = new Chart(document.getElementById('deptPieChart'), {
                type: 'pie',
                data: { labels: data.departments.slice(0,6).map(d => d[0]), datasets: [{ data: data.departments.slice(0,6).map(d => d[1]), backgroundColor: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'], borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e4e6eb' } } } }
            });
        } catch (error) { console.error(error); }
    }

    async function viewDetails(empId) {
        try {
            const response = await fetch('/api/employee/' + empId);
            const emp = await response.json();
            
            document.getElementById('modalBody').innerHTML = 
                '<div class="detail-section"><h3>Personal Information</h3>' +
                '<div class="detail-grid">' +
                '<div class="detail-item"><span class="detail-label">Employee ID:</span><span>' + (emp[1] || '-') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Full Name:</span><span><strong>' + escapeHtml(emp[2] || '') + '</strong></span></div>' +
                '<div class="detail-item"><span class="detail-label">Gender:</span><span>' + (emp[4] || '-') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Date of Birth:</span><span>' + (emp[11] || '-') + '</span></div>' +
                '</div></div>' +
                '<div class="detail-section"><h3>Employment Details</h3>' +
                '<div class="detail-grid">' +
                '<div class="detail-item"><span class="detail-label">Date of Joining:</span><span>' + (emp[3] || '-') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Department:</span><span>' + escapeHtml(emp[5] || '-') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Designation:</span><span>' + escapeHtml(emp[6] || '-') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Experience:</span><span>' + (emp[7] ? emp[7] + ' years' : '-') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Status:</span><span><span class="badge">Active</span></span></div>' +
                '</div></div>' +
                '<div class="detail-section"><h3>Documents</h3>' +
                '<div class="detail-grid">' +
                '<div class="detail-item"><span class="detail-label">PAN Number:</span><span>' + (emp[9] || 'Not Available') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Aadhar Number:</span><span>' + (emp[10] || 'Not Available') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Driving License:</span><span>' + (emp[12] || 'No') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Voter ID:</span><span>' + (emp[13] || 'No') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Passport:</span><span>' + (emp[14] || 'No') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Light Bill:</span><span>' + (emp[15] || 'No') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Ration Card:</span><span>' + (emp[16] || 'No') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Education Certificate:</span><span>' + (emp[17] || 'No') + '</span></div>' +
                '</div></div>';
            
            document.getElementById('employeeModal').style.display = 'flex';
        } catch (error) { alert('Could not load details'); }
    }

    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadEmployees(e.target.value.trim()), 300);
    });

    function exportCSV() { window.location.href = '/export/csv'; }
    function exportExcel() { window.location.href = '/export/excel'; }
    function exportPDF() { window.location.href = '/export/pdf'; }
    function closeModal() { document.getElementById('employeeModal').style.display = 'none'; }
    
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            return m === '&' ? '&amp;' : m === '<' ? '&lt;' : '&gt;';
        });
    }

    window.onclick = function(event) {
        if (event.target === document.getElementById('employeeModal')) closeModal();
    }
</script>
</body>
</html>
'''

# Flask Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            return jsonify({'success': False, 'error': 'Please upload an Excel file'}), 400
        
        temp_path = f'temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file.save(temp_path)
        
        count = process_excel(temp_path)
        os.remove(temp_path)
        
        return jsonify({'success': True, 'message': f'Imported {count} employees', 'count': count})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees', methods=['GET'])
def api_employees():
    return jsonify(get_all_employees())

@app.route('/api/search', methods=['GET'])
def api_search():
    q = request.args.get('q', '')
    return jsonify(search_employees(q))

@app.route('/api/employee/<int:eid>', methods=['GET'])
def api_employee(eid):
    emp = get_employee_by_id(eid)
    return jsonify(emp) if emp else jsonify({'error': 'Not found'}), 404

@app.route('/api/stats', methods=['GET'])
def api_stats():
    return jsonify(get_stats())

@app.route('/api/charts', methods=['GET'])
def api_charts():
    return jsonify({
        'departments': get_dept_stats(),
        'experience': get_exp_stats(),
        'hasPAN': get_stats()['pan'],
        'hasAadhar': get_stats()['aadhar']
    })

@app.route('/export/csv')
def export_csv():
    employees = get_all_employees()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['ID', 'Name', 'DOJ', 'Gender', 'Department', 'Designation', 'Experience', 'PAN', 'Aadhar', 'DOB', 'Status'])
    for e in employees:
        w.writerow([e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[9], e[10], e[11], e[18]])
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')), mimetype='text/csv', as_attachment=True, download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/export/excel')
def export_excel():
    employees = get_all_employees()
    data = [{'ID': e[1], 'Name': e[2], 'DOJ': e[3], 'Gender': e[4], 'Department': e[5], 'Designation': e[6], 'Experience': e[7], 'PAN': e[9], 'Aadhar': e[10], 'DOB': e[11], 'Status': e[18]} for e in employees]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Employees', index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

@app.route('/export/pdf')
def export_pdf():
    employees = get_all_employees()
    pdf = FPDF('L', 'mm', 'A3')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Puja Fluid Seals - Employee Report', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 8)
    headers = ['ID', 'Name', 'Department', 'Designation', 'Exp', 'PAN']
    widths = [20, 55, 45, 55, 25, 40]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, 1, 0, 'C', 1)
    pdf.ln()
    pdf.set_font('Arial', '', 7)
    for e in employees:
        pdf.cell(widths[0], 6, str(e[1] or ''), 1, 0, 'C')
        pdf.cell(widths[1], 6, e[2][:25] if e[2] else '', 1, 0, 'L')
        pdf.cell(widths[2], 6, e[5][:20] if e[5] else '', 1, 0, 'L')
        pdf.cell(widths[3], 6, e[6][:25] if e[6] else '', 1, 0, 'L')
        pdf.cell(widths[4], 6, str(e[7]) if e[7] else '', 1, 0, 'C')
        pdf.cell(widths[5], 6, e[9] or '', 1, 1, 'C')
    return send_file(io.BytesIO(pdf.output(dest='S').encode('latin1')), mimetype='application/pdf', as_attachment=True, download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')

if __name__ == '__main__':
    if os.path.exists('employees.db'):
        os.remove('employees.db')
    init_db()
    print("=" * 60)
    print("🏢 Puja Fluid Seals - Professional HR Dashboard")
    print("=" * 60)
    print("✨ Professional Dark Theme with Beautiful Charts")
    print("📊 Real-time Analytics Dashboard")
    print("🔍 Search by Name, Dept, PAN, Aadhar")
    print("📥 Export to CSV, Excel, PDF")
    print("=" * 60)
    print("🌐 http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)