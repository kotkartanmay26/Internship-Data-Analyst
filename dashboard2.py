"""
Puja Fluid Seals Pvt Ltd - Employee Dashboard
Complete working version with proper employee display and search
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
        emp_id TEXT,
        name TEXT NOT NULL,
        doj TEXT,
        gender TEXT,
        department TEXT,
        designation TEXT,
        experience REAL,
        pan TEXT,
        aadhar TEXT,
        dob TEXT,
        status TEXT DEFAULT 'Active'
    )''')
    conn.commit()
    conn.close()

init_db()

def parse_date(date_value):
    if pd.isna(date_value) or str(date_value).strip() == '':
        return None
    date_str = str(date_value).strip()
    
    # Handle multiple dates
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
        
        # Find where data starts
        start_row = 0
        for idx, row in df.iterrows():
            first_cell = str(row[0]) if pd.notna(row[0]) else ""
            if first_cell.isdigit() and int(first_cell) == 1:
                start_row = idx
                break
        
        employees = []
        
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            
            # Get SR.NO
            sr_no = row[0]
            if pd.isna(sr_no):
                continue
            
            try:
                sr_no_int = int(float(sr_no))
            except:
                continue
            
            # Get name
            name = clean_text(row[1])
            if not name or len(name) < 2:
                continue
            
            # Get other fields
            doj = parse_date(row[2]) if len(row) > 2 else None
            gender = clean_text(row[3]) if len(row) > 3 else "Not Specified"
            department = clean_department(row[4]) if len(row) > 4 else "Other"
            designation = clean_text(row[5]) if len(row) > 5 else ""
            
            # Experience
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
            
            employees.append({
                'emp_id': str(sr_no_int),
                'name': name,
                'doj': doj,
                'gender': gender.capitalize() if gender else "Not Specified",
                'department': department,
                'designation': designation,
                'experience': max(0, exp_val),
                'pan': pan,
                'aadhar': aadhar,
                'dob': dob
            })
        
        # Save to database
        conn = sqlite3.connect('employees.db')
        c = conn.cursor()
        c.execute('DELETE FROM employees')
        
        for emp in employees:
            c.execute('''INSERT INTO employees 
                (emp_id, name, doj, gender, department, designation, experience, pan, aadhar, dob, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (emp['emp_id'], emp['name'], emp['doj'], emp['gender'],
                 emp['department'], emp['designation'], emp['experience'],
                 emp['pan'], emp['aadhar'], emp['dob'], 'Active'))
        
        conn.commit()
        conn.close()
        
        return len(employees)
    
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def get_all_employees():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('SELECT * FROM employees ORDER BY emp_id')
    data = c.fetchall()
    conn.close()
    return data

def search_employees(term):
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    pattern = f'%{term}%'
    c.execute('''SELECT * FROM employees 
                 WHERE name LIKE ? OR department LIKE ? OR designation LIKE ? 
                 OR pan LIKE ? OR aadhar LIKE ? OR emp_id LIKE ?
                 ORDER BY emp_id''',
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
    has_pan = sum(1 for e in employees if e[8] and e[8] != '')
    has_aadhar = sum(1 for e in employees if e[9] and e[9] != '')
    return {'total': total, 'departments': depts, 'avgExp': avg_exp, 'pan': has_pan, 'aadhar': has_aadhar}

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

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Puja Fluid Seals | Employee Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0f0f1a;
            color: #ffffff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .upload-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 24px;
            padding: 50px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .upload-area {
            border: 3px dashed #2d2d44;
            border-radius: 20px;
            padding: 60px 40px;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-area:hover { border-color: #6366f1; background: rgba(99,102,241,0.05); }
        .upload-icon { font-size: 64px; color: #6366f1; margin-bottom: 20px; }
        .upload-title { font-size: 26px; font-weight: 700; margin-bottom: 10px; }
        .upload-subtitle { color: #94a3b8; margin-bottom: 25px; }
        .upload-btn {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            padding: 12px 30px;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            font-size: 15px;
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 20px;
            padding: 25px 30px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: #1a1a2e;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }
        .stat-value { font-size: 36px; font-weight: 800; color: #6366f1; }
        .stat-label { font-size: 13px; color: #94a3b8; margin-top: 5px; }
        
        .search-card {
            background: #1a1a2e;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .search-wrapper { position: relative; }
        .search-icon {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #94a3b8;
        }
        .search-input {
            width: 100%;
            padding: 14px 20px 14px 48px;
            background: #0f0f1a;
            border: 1px solid #2d2d44;
            border-radius: 12px;
            font-size: 14px;
            color: white;
        }
        .search-input:focus { outline: none; border-color: #6366f1; }
        .search-input::placeholder { color: #4a4a6a; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        .chart-card {
            background: #1a1a2e;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #2d2d44;
        }
        canvas { max-height: 250px; width: 100% !important; }
        
        .table-card {
            background: #1a1a2e;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .table-header {
            padding: 18px 20px;
            border-bottom: 1px solid #2d2d44;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .export-btn {
            padding: 6px 14px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            margin-left: 8px;
        }
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
            background: #0f0f1a;
            padding: 14px 15px;
            text-align: left;
            font-weight: 600;
            color: #94a3b8;
            border-bottom: 1px solid #2d2d44;
            position: sticky;
            top: 0;
        }
        .employee-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #2d2d44;
        }
        .employee-table tr:hover { background: rgba(99,102,241,0.1); }
        .view-btn {
            background: #6366f1;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
        }
        .view-btn:hover { background: #8b5cf6; }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: #1a1a2e;
            border-radius: 20px;
            max-width: 650px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .modal-header {
            padding: 20px 25px;
            border-bottom: 1px solid #2d2d44;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .close-modal { font-size: 24px; cursor: pointer; color: #94a3b8; }
        .modal-body { padding: 25px; }
        .detail-section { margin-bottom: 20px; }
        .detail-section h3 {
            font-size: 15px;
            color: #6366f1;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid #2d2d44;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .detail-label { font-weight: 600; color: #94a3b8; width: 110px; }
        .detail-item { display: flex; }
        .badge {
            background: #22c55e20;
            color: #22c55e;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
        }
        .loading { text-align: center; padding: 40px; color: #94a3b8; }
        .total-badge {
            background: #6366f1;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        @media (max-width: 768px) {
            .detail-grid { grid-template-columns: 1fr; }
            .charts-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <div id="uploadSection" class="upload-card">
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon"><i class="fas fa-cloud-upload-alt"></i></div>
            <div class="upload-title">Upload Employee Data</div>
            <div class="upload-subtitle">Click or drag & drop to upload Excel file (.xlsx, .xls)</div>
            <input type="file" id="fileInput" accept=".xlsx,.xls" style="display:none">
            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                <i class="fas fa-folder-open"></i> Browse Files
            </button>
            <div id="uploadProgress" style="margin-top: 20px; display:none">
                <div style="width:100%; background:#2d2d44; border-radius:8px; overflow:hidden">
                    <div id="progressBar" style="width:0%; height:3px; background:#6366f1"></div>
                </div>
                <p style="margin-top:10px; color:#94a3b8">Processing...</p>
            </div>
        </div>
        <div id="uploadStatus" style="margin-top: 15px"></div>
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
                <h3><i class="fas fa-users"></i> Employee Directory <span id="totalEmployeesBadge" class="total-badge" style="margin-left:10px"></span></h3>
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
        uploadArea.style.borderColor = '#6366f1';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#2d2d44';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#2d2d44';
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
        const colors = { success: '#22c55e', error: '#ef4444', info: '#6366f1' };
        statusDiv.innerHTML = '<div style="padding:12px; background:' + colors[type] + '20; border-radius:10px; color:' + colors[type] + '">' +
            '<i class="fas ' + (type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle') + '"></i> ' + message + '</div>';
        if (type !== 'error') {
            setTimeout(() => { if (statusDiv.innerHTML.includes(message)) statusDiv.innerHTML = ''; }, 5000);
        }
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
                    '<td>' + (emp[8] || '-') + '</td>' +
                    '<td><button class="view-btn" onclick="viewDetails(' + emp[0] + ')"><i class="fas fa-eye"></i> View</button></td>' +
                    '</tr>';
            }
            tbody.innerHTML = html;
        } catch (error) {
            console.error(error);
        }
    }

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('statsGrid').innerHTML = 
                '<div class="stat-card"><div class="stat-value">' + stats.total + '</div><div class="stat-label">Total Employees</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + stats.departments + '</div><div class="stat-label">Departments</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + stats.avgExp + '</div><div class="stat-label">Avg Experience (yrs)</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + stats.pan + '</div><div class="stat-label">With PAN</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + stats.aadhar + '</div><div class="stat-label">With Aadhar</div></div>';
        } catch (error) { console.error(error); }
    }

    async function loadCharts() {
        try {
            const response = await fetch('/api/charts');
            const data = await response.json();
            
            if (deptChart) deptChart.destroy();
            deptChart = new Chart(document.getElementById('deptChart'), {
                type: 'bar',
                data: { labels: data.departments.map(d => d[0]), datasets: [{ label: 'Employees', data: data.departments.map(d => d[1]), backgroundColor: '#6366f1' }] },
                options: { responsive: true, maintainAspectRatio: true }
            });
            
            if (expChart) expChart.destroy();
            expChart = new Chart(document.getElementById('expChart'), {
                type: 'doughnut',
                data: { labels: data.experience.map(e => e[0]), datasets: [{ data: data.experience.map(e => e[1]), backgroundColor: ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'] }] },
                options: { responsive: true, maintainAspectRatio: true }
            });
            
            if (docChart) docChart.destroy();
            docChart = new Chart(document.getElementById('docChart'), {
                type: 'bar',
                data: { labels: ['PAN Card', 'Aadhar Card'], datasets: [{ label: 'Available', data: [data.hasPAN, data.hasAadhar], backgroundColor: '#22c55e' }] },
                options: { responsive: true, maintainAspectRatio: true }
            });
            
            if (deptPieChart) deptPieChart.destroy();
            deptPieChart = new Chart(document.getElementById('deptPieChart'), {
                type: 'pie',
                data: { labels: data.departments.slice(0,6).map(d => d[0]), datasets: [{ data: data.departments.slice(0,6).map(d => d[1]), backgroundColor: ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'] }] },
                options: { responsive: true, maintainAspectRatio: true }
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
                '<div class="detail-item"><span class="detail-label">Date of Birth:</span><span>' + (emp[10] || '-') + '</span></div>' +
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
                '<div class="detail-item"><span class="detail-label">PAN Number:</span><span>' + (emp[8] || 'Not Available') + '</span></div>' +
                '<div class="detail-item"><span class="detail-label">Aadhar Number:</span><span>' + (emp[9] || 'Not Available') + '</span></div>' +
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
        w.writerow([e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11]])
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')), mimetype='text/csv', as_attachment=True, download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/export/excel')
def export_excel():
    employees = get_all_employees()
    data = [{'ID': e[1], 'Name': e[2], 'DOJ': e[3], 'Gender': e[4], 'Department': e[5], 'Designation': e[6], 'Experience': e[7], 'PAN': e[8], 'Aadhar': e[9], 'DOB': e[10], 'Status': e[11]} for e in employees]
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
        pdf.cell(widths[5], 6, e[8] or '', 1, 1, 'C')
    return send_file(io.BytesIO(pdf.output(dest='S').encode('latin1')), mimetype='application/pdf', as_attachment=True, download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')

if __name__ == '__main__':
    if os.path.exists('employees.db'):
        os.remove('employees.db')
    init_db()
    print("=" * 60)
    print("🏢 Puja Fluid Seals - Employee Dashboard")
    print("=" * 60)
    print("🌐 Open: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)