"""
Professional Employee Dashboard - Single File Application
With Export Features: PDF, CSV, Excel & Import from Excel
Run: python employee_dashboard.py
"""

import sqlite3
import io
import csv
from flask import Flask, render_template_string, request, jsonify, send_file
import pandas as pd
from fpdf import FPDF
import os

# ---------- Flask App Initialization ----------
app = Flask(__name__)

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        experience REAL NOT NULL,
        education TEXT NOT NULL,
        gender TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Left'))
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------- Helper Functions ----------
def get_all_employees():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('SELECT * FROM employees ORDER BY id')
    employees = c.fetchall()
    conn.close()
    return employees

def get_employees_as_dict():
    employees = get_all_employees()
    return [{'id': e[0], 'name': e[1], 'age': e[2], 'experience': e[3], 
             'education': e[4], 'gender': e[5], 'status': e[6]} for e in employees]

def add_employee_to_db(name, age, experience, education, gender, status):
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('''INSERT INTO employees (name, age, experience, education, gender, status)
                 VALUES (?, ?, ?, ?, ?, ?)''', (name, age, experience, education, gender, status))
    conn.commit()
    conn.close()

def delete_all_employees():
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('DELETE FROM employees')
    conn.commit()
    conn.close()

def delete_employee_by_id(emp_id):
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()

def import_employees_from_dataframe(df):
    """Import employees from DataFrame to database"""
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    
    # Expected columns: name, age, experience, education, gender, status
    required_columns = ['name', 'age', 'experience', 'education', 'gender', 'status']
    
    # Check if required columns exist
    for col in required_columns:
        if col not in df.columns:
            conn.close()
            raise ValueError(f"Missing required column: {col}")
    
    # Insert each row
    inserted_count = 0
    for _, row in df.iterrows():
        try:
            c.execute('''INSERT INTO employees (name, age, experience, education, gender, status)
                         VALUES (?, ?, ?, ?, ?, ?)''', 
                         (str(row['name']), 
                          int(row['age']), 
                          float(row['experience']), 
                          str(row['education']), 
                          str(row['gender']), 
                          str(row['status'])))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting row: {e}")
            continue
    
    conn.commit()
    conn.close()
    return inserted_count

# ---------- PDF Export Class ----------
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Employee Report - Workforce Dashboard', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f'Generated on: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def add_table_header(self):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(44, 95, 138)
        self.set_text_color(255, 255, 255)
        self.cell(15, 10, 'SR No', 1, 0, 'C', 1)
        self.cell(50, 10, 'Name', 1, 0, 'C', 1)
        self.cell(20, 10, 'Age', 1, 0, 'C', 1)
        self.cell(30, 10, 'Experience', 1, 0, 'C', 1)
        self.cell(40, 10, 'Education', 1, 0, 'C', 1)
        self.cell(30, 10, 'Gender', 1, 0, 'C', 1)
        self.cell(30, 10, 'Status', 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)

def export_to_pdf():
    employees = get_employees_as_dict()
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.add_table_header()
    
    pdf.set_font('Arial', '', 9)
    for idx, emp in enumerate(employees, start=1):
        pdf.cell(15, 8, str(idx), 1, 0, 'C')
        pdf.cell(50, 8, emp['name'][:25], 1, 0, 'L')
        pdf.cell(20, 8, str(emp['age']), 1, 0, 'C')
        pdf.cell(30, 8, f"{emp['experience']} yrs", 1, 0, 'C')
        pdf.cell(40, 8, emp['education'][:20], 1, 0, 'L')
        pdf.cell(30, 8, emp['gender'], 1, 0, 'C')
        pdf.cell(30, 8, emp['status'], 1, 1, 'C')
    
    # Add summary
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    total = len(employees)
    present = sum(1 for e in employees if e['status'] == 'Present')
    left = total - present
    pdf.cell(0, 8, f'Summary: Total: {total} | Present: {present} | Left: {left}', 0, 1, 'L')
    
    return pdf.output(dest='S').encode('latin1')

# ---------- Frontend HTML/CSS/JS ----------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stratus HR | Employee Dashboard Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #f5f7fc 0%, #eef2f6 100%);
            color: #1a2c3e;
            padding: 32px 24px;
        }

        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .title-section h1 {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            letter-spacing: -0.3px;
        }
        .title-section p {
            color: #5a6874;
            font-size: 14px;
            margin-top: 6px;
        }
        .action-buttons {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 14px;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: 'Inter', sans-serif;
        }
        .btn-primary {
            background: #2c5f8a;
            color: white;
            box-shadow: 0 2px 6px rgba(44,95,138,0.2);
        }
        .btn-primary:hover {
            background: #1e4668;
            transform: translateY(-2px);
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background: #b02a37;
            transform: translateY(-2px);
        }
        .btn-outline {
            background: white;
            border: 1px solid #cbd5e1;
            color: #334155;
        }
        .btn-outline:hover {
            background: #f8fafc;
            border-color: #94a3b8;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #1e7e34;
            transform: translateY(-2px);
        }
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        .btn-info:hover {
            background: #138496;
            transform: translateY(-2px);
        }
        .btn-warning {
            background: #ffc107;
            color: #1a2c3e;
        }
        .btn-warning:hover {
            background: #e0a800;
            transform: translateY(-2px);
        }
        .btn-purple {
            background: #6f42c1;
            color: white;
        }
        .btn-purple:hover {
            background: #5a32a3;
            transform: translateY(-2px);
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }
        .stat-card {
            background: white;
            border-radius: 24px;
            padding: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.02), 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid rgba(0,0,0,0.05);
            transition: all 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 20px 25px -12px rgba(0,0,0,0.1);
        }
        .stat-title {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            color: #6c7a8a;
            margin-bottom: 12px;
        }
        .stat-value {
            font-size: 36px;
            font-weight: 800;
            color: #1e2f3e;
        }
        .stat-sub {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 8px;
        }

        /* Export Section */
        .export-section {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 20px;
            padding: 16px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .export-title {
            font-weight: 600;
            color: #2c3e50;
        }
        .export-buttons {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        /* Import Section */
        .import-section {
            background: linear-gradient(135deg, #e8eaf6, #e3f2fd);
            border-radius: 20px;
            padding: 16px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            border: 1px solid #c5cae9;
        }
        .import-title {
            font-weight: 600;
            color: #3949ab;
        }
        .file-input-wrapper {
            position: relative;
            display: inline-block;
        }
        .file-input-wrapper input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }
        .upload-status {
            font-size: 12px;
            margin-top: 8px;
            color: #2c5f8a;
        }

        /* Form Card */
        .form-card {
            background: white;
            border-radius: 28px;
            padding: 28px;
            margin-bottom: 32px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.05);
            border: 1px solid #e9edf2;
        }
        .form-card h3 {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #0f2b3d;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 18px;
            margin-bottom: 20px;
        }
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .input-group label {
            font-size: 13px;
            font-weight: 600;
            color: #2c3e4e;
        }
        .input-group input, .input-group select {
            padding: 12px 14px;
            border-radius: 14px;
            border: 1px solid #cfdfed;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            transition: 0.2s;
            background: #fefefe;
        }
        .input-group input:focus, .input-group select:focus {
            outline: none;
            border-color: #2c5f8a;
            box-shadow: 0 0 0 3px rgba(44,95,138,0.1);
        }
        .radio-group {
            display: flex;
            gap: 20px;
            align-items: center;
            margin-top: 6px;
        }
        .radio-group label {
            font-weight: normal;
            flex-direction: row;
            gap: 6px;
            display: inline-flex;
            align-items: center;
        }

        /* Table */
        .table-wrapper {
            background: white;
            border-radius: 28px;
            padding: 0;
            overflow-x: auto;
            box-shadow: 0 12px 30px rgba(0,0,0,0.05);
            border: 1px solid #e9edf2;
        }
        .employee-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        .employee-table th {
            text-align: left;
            padding: 18px 16px;
            background-color: #f9fbfd;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 1px solid #e2e8f0;
        }
        .employee-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #edf2f7;
            vertical-align: middle;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 40px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-present {
            background: #e0f2e9;
            color: #1e6f3f;
        }
        .status-left {
            background: #ffe6e5;
            color: #bc1c2e;
        }
        .delete-icon {
            color: #e53e3e;
            cursor: pointer;
            font-size: 18px;
            transition: 0.1s;
            background: none;
            border: none;
        }
        .delete-icon:hover {
            color: #9b2c2c;
            transform: scale(1.1);
        }
        .action-cell {
            text-align: center;
            width: 50px;
        }
        .empty-row td {
            text-align: center;
            padding: 48px;
            color: #7f8c8d;
            font-style: italic;
        }
        footer {
            margin-top: 32px;
            text-align: center;
            font-size: 12px;
            color: #7f8e9e;
        }
        .toast-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2c5f8a;
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 14px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @media (max-width: 700px) {
            body { padding: 16px; }
            .stat-value { font-size: 28px; }
        }
    </style>
</head>
<body>
<div class="dashboard-container">
    <div class="header">
        <div class="title-section">
            <h1><i class="fas fa-users" style="color:#2c5f8a;"></i>Puja Fluid Seals PVT LTD Dashboard</h1>
            <p>Manage employee records • Export & Import data in multiple formats</p>
        </div>
        <div class="action-buttons">
            <button class="btn btn-outline" id="refreshBtn"><i class="fas fa-sync-alt"></i> Refresh</button>
            <button class="btn btn-danger" id="deleteAllBtn"><i class="fas fa-trash-alt"></i> Delete All</button>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-title"><i class="fas fa-user-friends"></i> Total Employees</div>
            <div class="stat-value" id="totalCount">0</div>
            <div class="stat-sub">All records</div>
        </div>
        <div class="stat-card">
            <div class="stat-title"><i class="fas fa-user-check"></i> Present</div>
            <div class="stat-value" id="presentCount">0</div>
            <div class="stat-sub">Active workforce</div>
        </div>
        <div class="stat-card">
            <div class="stat-title"><i class="fas fa-user-graduate"></i> Left</div>
            <div class="stat-value" id="leftCount">0</div>
            <div class="stat-sub">Inactive</div>
        </div>
        <div class="stat-card">
            <div class="stat-title"><i class="fas fa-chalkboard-user"></i> Avg Experience</div>
            <div class="stat-value" id="avgExp">0</div>
            <div class="stat-sub">Years</div>
        </div>
    </div>

    <!-- Import Section -->
    <div class="import-section">
        <div class="import-title">
            <i class="fas fa-upload"></i> <strong>Import Data</strong> — Upload Excel file (.xlsx)
        </div>
        <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <input type="file" id="excelUpload" accept=".xlsx, .xls" style="display: none;">
            <button class="btn btn-purple" id="uploadBtn"><i class="fas fa-file-excel"></i> Choose Excel File</button>
            <span id="fileName" style="font-size: 13px; color: #555;"></span>
            <button class="btn btn-primary" id="importBtn" style="display: none;"><i class="fas fa-database"></i> Import Data</button>
        </div>
        <div id="uploadStatus" class="upload-status"></div>
    </div>

    <!-- Export Section -->
    <div class="export-section">
        <div class="export-title">
            <i class="fas fa-download"></i> <strong>Export Data</strong> — Download all employee records
        </div>
        <div class="export-buttons">
            <button class="btn btn-success" id="exportCsvBtn"><i class="fas fa-file-csv"></i> CSV</button>
            <button class="btn btn-info" id="exportExcelBtn"><i class="fas fa-file-excel"></i> Excel</button>
            <button class="btn btn-danger" id="exportPdfBtn"><i class="fas fa-file-pdf"></i> PDF</button>
        </div>
    </div>

    <!-- Add Employee Form -->
    <div class="form-card">
        <h3><i class="fas fa-plus-circle"></i> Register New Employee</h3>
        <div class="form-grid">
            <div class="input-group">
                <label>Full Name</label>
                <input type="text" id="empName" placeholder="e.g. Sarah Johnson" autocomplete="off">
            </div>
            <div class="input-group">
                <label>Age</label>
                <input type="number" id="empAge" placeholder="25" min="18" max="100">
            </div>
            <div class="input-group">
                <label>Experience (years)</label>
                <input type="number" id="empExp" step="0.5" placeholder="3.5" min="0">
            </div>
            <div class="input-group">
                <label>Education</label>
                <select id="empEdu">
                    <option value="High School">High School</option>
                    <option value="Bachelor's">Bachelor's</option>
                    <option value="Master's">Master's</option>
                    <option value="PhD">PhD</option>
                    <option value="Diploma">Diploma</option>
                </select>
            </div>
            <div class="input-group">
                <label>Gender</label>
                <div class="radio-group">
                    <label><input type="radio" name="gender" value="Male"> Male</label>
                    <label><input type="radio" name="gender" value="Female"> Female</label>
                    <label><input type="radio" name="gender" value="Other"> Other</label>
                </div>
            </div>
            <div class="input-group">
                <label>Employment Status</label>
                <div class="radio-group">
                    <label><input type="radio" name="status" value="Present" checked> Present</label>
                    <label><input type="radio" name="status" value="Left"> Left</label>
                </div>
            </div>
        </div>
        <div style="display: flex; justify-content: flex-end;">
            <button class="btn btn-primary" id="addBtn"><i class="fas fa-save"></i> Add Employee</button>
        </div>
    </div>

    <!-- Employees Table -->
    <div class="table-wrapper">
        <table class="employee-table">
            <thead>
                <tr><th>SR No.</th><th>Name</th><th>Age</th><th>Exp (yrs)</th><th>Education</th><th>Gender</th><th>Status</th><th style="width:50px"></th></tr>
            </thead>
            <tbody id="employeeTableBody">
                <tr class="empty-row"><td colspan="8">Loading employees...</td></tr>
            </tbody>
         </table>
    </div>
    <footer>© Stratus HR Pro — SQLite Database | Export to CSV, Excel, PDF | Import from Excel</footer>
</div>

<script>
    let selectedFile = null;

    async function loadDashboard() {
        try {
            const response = await fetch('/api/employees');
            const employees = await response.json();
            renderTable(employees);
            updateStats(employees);
        } catch(err) {
            console.error(err);
            document.getElementById('employeeTableBody').innerHTML = '<tr class="empty-row"><td colspan="8">Failed to load data</td></tr>';
        }
    }

    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.style.background = isError ? '#dc3545' : '#28a745';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    function renderTable(employees) {
        const tbody = document.getElementById('employeeTableBody');
        if (!employees.length) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No employees found. Add your first employee!</td></tr>';
            return;
        }
        let html = '';
        employees.forEach((emp, index) => {
            const statusClass = emp[6] === 'Present' ? 'status-present' : 'status-left';
            html += `<tr>
                <td><strong>${index + 1}</strong></td>
                <td><strong>${escapeHtml(emp[1])}</strong></td>
                <td>${emp[2]}</td>
                <td>${emp[3]}</td>
                <td>${escapeHtml(emp[4])}</td>
                <td>${escapeHtml(emp[5])}</td>
                <td><span class="status-badge ${statusClass}">${emp[6]}</span></td>
                <td class="action-cell"><button class="delete-icon" data-id="${emp[0]}" title="Delete record"><i class="fas fa-trash-can"></i></button></td>
            </tr>`;
        });
        tbody.innerHTML = html;
        document.querySelectorAll('.delete-icon').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const empId = btn.getAttribute('data-id');
                if (confirm(`Delete employee #${empId} permanently?`)) {
                    await fetch(`/api/employee/${empId}`, { method: 'DELETE' });
                    showToast('Employee deleted successfully!');
                    loadDashboard();
                }
            });
        });
    }

    function updateStats(employees) {
        const total = employees.length;
        const present = employees.filter(emp => emp[6] === 'Present').length;
        const left = total - present;
        let totalExp = 0;
        employees.forEach(emp => { totalExp += emp[3]; });
        const avgExp = total === 0 ? 0 : (totalExp / total).toFixed(1);
        document.getElementById('totalCount').innerText = total;
        document.getElementById('presentCount').innerText = present;
        document.getElementById('leftCount').innerText = left;
        document.getElementById('avgExp').innerText = avgExp;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    // File upload handling
    document.getElementById('uploadBtn').addEventListener('click', () => {
        document.getElementById('excelUpload').click();
    });

    document.getElementById('excelUpload').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            document.getElementById('fileName').textContent = `Selected: ${file.name}`;
            document.getElementById('importBtn').style.display = 'inline-flex';
            document.getElementById('uploadStatus').innerHTML = '<span style="color: #2c5f8a;"><i class="fas fa-info-circle"></i> File ready for import</span>';
        } else {
            selectedFile = null;
            document.getElementById('fileName').textContent = '';
            document.getElementById('importBtn').style.display = 'none';
            document.getElementById('uploadStatus').innerHTML = '';
        }
    });

    // Import data
    document.getElementById('importBtn').addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Please select an Excel file first');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        document.getElementById('uploadStatus').innerHTML = '<span style="color: #ffc107;"><i class="fas fa-spinner fa-spin"></i> Importing data...</span>';
        document.getElementById('importBtn').disabled = true;

        try {
            const response = await fetch('/api/import/excel', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                showToast(`Successfully imported ${result.imported_count} employees!`);
                document.getElementById('uploadStatus').innerHTML = `<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Import complete! ${result.imported_count} records added.</span>`;
                // Reset file input
                document.getElementById('excelUpload').value = '';
                selectedFile = null;
                document.getElementById('fileName').textContent = '';
                document.getElementById('importBtn').style.display = 'none';
                // Refresh the dashboard
                loadDashboard();
            } else {
                throw new Error(result.error || 'Import failed');
            }
        } catch (error) {
            console.error('Import error:', error);
            showToast(error.message, true);
            document.getElementById('uploadStatus').innerHTML = `<span style="color: #dc3545;"><i class="fas fa-exclamation-circle"></i> Import failed: ${error.message}</span>`;
        } finally {
            document.getElementById('importBtn').disabled = false;
        }
    });

    // Add employee
    document.getElementById('addBtn').addEventListener('click', async () => {
        const name = document.getElementById('empName').value.trim();
        const age = parseInt(document.getElementById('empAge').value);
        const exp = parseFloat(document.getElementById('empExp').value);
        const education = document.getElementById('empEdu').value;
        const genderElem = document.querySelector('input[name="gender"]:checked');
        const gender = genderElem ? genderElem.value : 'Other';
        const statusElem = document.querySelector('input[name="status"]:checked');
        const status = statusElem ? statusElem.value : 'Present';

        if (!name) { alert('Please enter employee name'); return; }
        if (isNaN(age) || age < 18 || age > 100) { alert('Age must be 18-100'); return; }
        if (isNaN(exp) || exp < 0) { alert('Experience must be a valid number'); return; }

        const payload = { name, age, experience: exp, education, gender, status };
        const res = await fetch('/api/employees', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            document.getElementById('empName').value = '';
            document.getElementById('empAge').value = '';
            document.getElementById('empExp').value = '';
            document.querySelector('input[name="gender"][value="Male"]').checked = false;
            document.querySelector('input[name="gender"][value="Female"]').checked = false;
            document.querySelector('input[name="gender"][value="Other"]').checked = false;
            document.querySelector('input[name="status"][value="Present"]').checked = true;
            showToast('Employee added successfully!');
            loadDashboard();
        } else {
            const err = await res.json();
            alert('Error: ' + (err.error || 'Could not add'));
        }
    });

    // Delete all
    document.getElementById('deleteAllBtn').addEventListener('click', async () => {
        if (confirm('⚠️ DANGER: This will delete ALL employee records. Are you absolutely sure?')) {
            await fetch('/api/employees', { method: 'DELETE' });
            showToast('All employees deleted!');
            loadDashboard();
        }
    });

    // Export functions
    document.getElementById('exportCsvBtn').addEventListener('click', () => {
        window.location.href = '/export/csv';
    });
    
    document.getElementById('exportExcelBtn').addEventListener('click', () => {
        window.location.href = '/export/excel';
    });
    
    document.getElementById('exportPdfBtn').addEventListener('click', () => {
        window.location.href = '/export/pdf';
    });

    document.getElementById('refreshBtn').addEventListener('click', () => loadDashboard());

    loadDashboard();
</script>
</body>
</html>
"""

# ---------- Flask API Routes ----------
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/employees', methods=['GET'])
def api_get_employees():
    employees = get_all_employees()
    return jsonify(employees)

@app.route('/api/employees', methods=['POST'])
def api_add_employee():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    name = data.get('name')
    age = data.get('age')
    experience = data.get('experience')
    education = data.get('education')
    gender = data.get('gender')
    status = data.get('status')
    
    if not all([name, age, experience, education, gender, status]):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        add_employee_to_db(name, int(age), float(experience), education, gender, status)
        return jsonify({'message': 'Employee added'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees', methods=['DELETE'])
def api_delete_all():
    delete_all_employees()
    return jsonify({'message': 'All employees deleted'}), 200

@app.route('/api/employee/<int:emp_id>', methods=['DELETE'])
def api_delete_one(emp_id):
    delete_employee_by_id(emp_id)
    return jsonify({'message': 'Employee deleted'}), 200

# ---------- Import Route ----------
@app.route('/api/import/excel', methods=['POST'])
def api_import_excel():
    """Import employees from Excel file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Check for required columns
        required_columns = ['name', 'age', 'experience', 'education', 'gender', 'status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {", ".join(missing_columns)}. Required columns: name, age, experience, education, gender, status'}), 400
        
        # Import data
        imported_count = import_employees_from_dataframe(df)
        
        return jsonify({
            'message': f'Successfully imported {imported_count} employees',
            'imported_count': imported_count,
            'total_rows': len(df)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to import file: {str(e)}'}), 500

# ---------- Export Routes ----------
@app.route('/export/csv')
def export_csv():
    employees = get_employees_as_dict()
    output = io.StringIO()
    if employees:
        writer = csv.DictWriter(output, fieldnames=['sr_no', 'name', 'age', 'experience', 'education', 'gender', 'status'])
        writer.writeheader()
        for idx, emp in enumerate(employees, start=1):
            writer.writerow({
                'sr_no': idx,
                'name': emp['name'],
                'age': emp['age'],
                'experience': emp['experience'],
                'education': emp['education'],
                'gender': emp['gender'],
                'status': emp['status']
            })
    else:
        output.write('sr_no,name,age,experience,education,gender,status\nNo data available,,,,,,\n')
    
    response = send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'employees_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )
    return response

@app.route('/export/excel')
def export_excel():
    employees = get_employees_as_dict()
    if employees:
        # Create DataFrame with serial numbers
        data = []
        for idx, emp in enumerate(employees, start=1):
            data.append({
                'SR No': idx,
                'Name': emp['name'],
                'Age': emp['age'],
                'Experience (yrs)': emp['experience'],
                'Education': emp['education'],
                'Gender': emp['gender'],
                'Status': emp['status']
            })
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(columns=['SR No', 'Name', 'Age', 'Experience (yrs)', 'Education', 'Gender', 'Status'])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Employees', index=False)
        # Adjust column widths
        worksheet = writer.sheets['Employees']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'employees_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@app.route('/export/pdf')
def export_pdf():
    try:
        pdf_data = export_to_pdf()
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'employees_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

# ---------- Run Server ----------
if __name__ == '__main__':
    # Install required packages if not present
    print("=" * 50)
    print("Employee Dashboard Starting...")
    print("Make sure you have installed required packages:")
    print("pip install flask pandas openpyxl fpdf")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)