# -*- coding: utf-8 -*-
"""
HR ANALYTICS DASHBOARD - FULLY INTERACTIVE
All charts update when filters change
"""

from flask import Flask, render_template_string, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

app = Flask(__name__)

# Global variable for data
excel_data = None

def parse_date_work(date_str):
    """Parse date from Excel"""
    if pd.isna(date_str) or date_str == "" or date_str is None:
        return None
    try:
        if isinstance(date_str, datetime):
            return date_str
        date_str = str(date_str).strip()
        if '.' in date_str:
            parts = date_str.split('.')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = 2000 + int(year) if int(year) < 30 else 1900 + int(year)
                return datetime(int(year), int(month), int(day))
        return pd.to_datetime(date_str, dayfirst=True)
    except:
        return None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    global excel_data
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read Excel file
        df = pd.read_excel(file, header=None)
        
        # Extract data
        employees = []
        workforce = []
        contractors = []
        
        current_section = "employees"
        employee_count = 0
        
        for idx, row in df.iterrows():
            col0 = str(row[0]) if pd.notna(row[0]) else ""
            col1 = str(row[1]) if pd.notna(row[1]) else ""
            col2 = str(row[2]) if pd.notna(row[2]) else ""
            col3 = str(row[3]) if pd.notna(row[3]) else ""
            col4 = str(row[4]) if pd.notna(row[4]) else ""
            
            if 'Name' in col1 or 'Sr.No' in col0:
                if employee_count > 0:
                    current_section = "workforce"
                continue
            
            if col1 and col1 != 'nan' and len(col1) > 1 and not col1.isdigit():
                record = {
                    'name': col1,
                    'dept': col2 if col2 != 'nan' else '',
                    'doj': col3 if col3 != 'nan' else '',
                    'left_date': col4 if col4 != 'nan' and col4 != '' else '',
                }
                
                if col0.isdigit() or (col0 and col0.replace('.', '').isdigit()):
                    try:
                        sr_no = int(float(col0))
                        if sr_no <= 39 and current_section == "employees":
                            employees.append(record)
                            employee_count += 1
                        else:
                            workforce.append(record)
                    except:
                        workforce.append(record)
                else:
                    workforce.append(record)
        
        # Read Contractor sheet
        try:
            contractors_df = pd.read_excel(file, sheet_name='Contractor', header=None)
            for idx, row in contractors_df.iterrows():
                col1 = str(row[1]) if len(row) > 1 and pd.notna(row[1]) else ""
                col2 = str(row[2]) if len(row) > 2 and pd.notna(row[2]) else ""
                col3 = str(row[3]) if len(row) > 3 and pd.notna(row[3]) else ""
                col4 = str(row[4]) if len(row) > 4 and pd.notna(row[4]) else ""
                
                if col1 and col1 != 'nan' and 'Name' not in col1:
                    contractors.append({
                        'name': col1,
                        'dept': col2 if col2 != 'nan' else '',
                        'doj': col3 if col3 != 'nan' else '',
                        'left_date': col4 if col4 != 'nan' and col4 != '' else '',
                    })
        except:
            pass
        
        # Process records
        today = datetime.now()
        
        def process_records(records, source):
            processed = []
            for r in records:
                doj_parsed = parse_date_work(r['doj'])
                left_parsed = parse_date_work(r['left_date']) if r['left_date'] else None
                status = 'Left' if left_parsed else 'Active'
                
                if doj_parsed:
                    if left_parsed:
                        days = (left_parsed - doj_parsed).days
                    else:
                        days = (today - doj_parsed).days
                    tenure_years = round(days / 365.25, 1)
                else:
                    tenure_years = 0
                
                # Extract year and month from DOJ
                year = ''
                month = ''
                if r['doj'] and r['doj'] != '':
                    match = re.search(r'(\d{2})\.(\d{2})\.(\d{2,4})', str(r['doj']))
                    if match:
                        day, mon, yr = match.groups()
                        if len(yr) == 2:
                            yr = '20' + yr if int(yr) <= 30 else '19' + yr
                        year = yr
                        month = mon
                
                processed.append({
                    'name': r['name'],
                    'dept': r['dept'],
                    'doj': r['doj'],
                    'left_date': r['left_date'] if r['left_date'] else '',
                    'status': status,
                    'tenure_years': tenure_years,
                    'source': source,
                    'year': year,
                    'month': month
                })
            return processed
        
        emp_processed = process_records(employees, "PFSPL Employee")
        work_processed = process_records(workforce, "PFSPL Workforce")
        cont_processed = process_records(contractors, "Contractor")
        
        all_data = emp_processed + work_processed + cont_processed
        
        excel_data = {
            'all': all_data,
            'employees': emp_processed,
            'workforce': work_processed,
            'contractors': cont_processed
        }
        
        active = len([d for d in all_data if d['status'] == 'Active'])
        left = len([d for d in all_data if d['status'] == 'Left'])
        avg_tenure = sum(d['tenure_years'] for d in all_data) / len(all_data) if all_data else 0
        
        return jsonify({
            'success': True,
            'total': len(all_data),
            'employees': len(emp_processed),
            'workforce': len(work_processed),
            'contractors': len(cont_processed),
            'active': active,
            'left': left,
            'avg_tenure': round(avg_tenure, 1)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filtered_data')
def get_filtered_data():
    """Get filtered data based on source and status"""
    if not excel_data:
        return jsonify({'error': 'No data'}), 404
    
    source = request.args.get('source', 'all')
    status = request.args.get('status', 'all')
    
    # Get data based on source
    if source == 'employees':
        data = excel_data['employees']
    elif source == 'workforce':
        data = excel_data['workforce']
    elif source == 'contractors':
        data = excel_data['contractors']
    else:
        data = excel_data['all']
    
    # Filter by status
    if status != 'all':
        data = [d for d in data if d['status'] == status]
    
    # Calculate statistics
    total = len(data)
    active = len([d for d in data if d['status'] == 'Active'])
    left = len([d for d in data if d['status'] == 'Left'])
    avg_tenure = sum(d['tenure_years'] for d in data) / total if total > 0 else 0
    
    # Department distribution
    dept_stats = {}
    for record in data:
        dept = record['dept']
        if not dept:
            continue
        if dept not in dept_stats:
            dept_stats[dept] = {'total': 0, 'active': 0, 'left': 0}
        dept_stats[dept]['total'] += 1
        if record['status'] == 'Active':
            dept_stats[dept]['active'] += 1
        else:
            dept_stats[dept]['left'] += 1
    
    for dept in dept_stats:
        total_dept = dept_stats[dept]['total']
        left_dept = dept_stats[dept]['left']
        dept_stats[dept]['turnover'] = round((left_dept / total_dept * 100), 1) if total_dept > 0 else 0
    
    # Sort by total descending
    dept_stats = dict(sorted(dept_stats.items(), key=lambda x: x[1]['total'], reverse=True))
    
    # Yearly joining trends
    yearly = {}
    for record in data:
        year = record['year']
        if year:
            yearly[year] = yearly.get(year, 0) + 1
    yearly = dict(sorted(yearly.items()))
    
    # Monthly joining trends
    monthly = {}
    month_names = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
                   '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}
    for record in data:
        month = record['month']
        if month:
            month_name = month_names.get(month, month)
            monthly[month_name] = monthly.get(month_name, 0) + 1
    
    # Status distribution for pie chart
    status_dist = {'Active': active, 'Left': left}
    
    return jsonify({
        'total': total,
        'active': active,
        'left': left,
        'avg_tenure': round(avg_tenure, 1),
        'departments': len(dept_stats),
        'dept_stats': dept_stats,
        'yearly_trends': yearly,
        'monthly_trends': monthly,
        'status_distribution': status_dist
    })

@app.route('/api/employees')
def get_employees():
    if not excel_data:
        return jsonify({'data': [], 'total': 0})
    
    source = request.args.get('source', 'all')
    status = request.args.get('status', 'all')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    if source == 'employees':
        data = excel_data['employees']
    elif source == 'workforce':
        data = excel_data['workforce']
    elif source == 'contractors':
        data = excel_data['contractors']
    else:
        data = excel_data['all']
    
    if status != 'all':
        data = [d for d in data if d['status'] == status]
    
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = data[start:end]
    
    return jsonify({
        'data': page_data,
        'total': total,
        'page': page,
        'total_pages': (total + per_page - 1) // per_page
    })

# Professional HTML Template with Interactive Charts
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Analytics Dashboard | Interactive</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #f5f7fb; }
        
        .header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 30px 40px;
        }
        .header h1 { font-size: 28px; font-weight: 700; }
        .header p { margin-top: 8px; opacity: 0.8; font-size: 14px; }
        
        .container { max-width: 1400px; margin: -20px auto 0; padding: 0 20px 40px; }
        
        .upload-card {
            background: white;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            border: 2px dashed #cbd5e1;
            transition: all 0.3s;
        }
        .upload-card:hover { border-color: #3b82f6; background: #f8fafc; }
        .upload-btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 20px;
        }
        .upload-btn:hover { background: #2563eb; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-icon { font-size: 32px; margin-bottom: 10px; }
        .stat-value { font-size: 32px; font-weight: 800; color: #0f172a; }
        .stat-label { font-size: 12px; color: #64748b; margin-top: 8px; font-weight: 500; }
        
        .filters {
            background: white;
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 25px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .filter-group { display: flex; align-items: center; gap: 10px; }
        .filter-group label { font-weight: 600; font-size: 13px; }
        .filter-group select {
            padding: 8px 15px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            font-size: 13px;
            background: white;
            cursor: pointer;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 25px;
            margin-bottom: 30px;
        }
        .chart-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .chart-card h3 {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        canvas { max-height: 300px; }
        
        .dept-section {
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .dept-section h3 {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dept-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .dept-item {
            background: #f8fafc;
            border-radius: 12px;
            padding: 15px;
            border-left: 4px solid;
        }
        .dept-name { font-weight: 700; font-size: 14px; margin-bottom: 10px; }
        .dept-stats { display: flex; gap: 15px; font-size: 12px; flex-wrap: wrap; }
        .dept-stats span { color: #64748b; }
        .dept-stats strong { color: #0f172a; }
        .turnover-high { color: #dc2626; font-weight: 700; }
        .turnover-medium { color: #f59e0b; font-weight: 700; }
        .turnover-low { color: #10b981; font-weight: 700; }
        
        .data-table {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .search-box {
            padding: 10px 15px;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            width: 250px;
            font-size: 13px;
            margin-bottom: 15px;
        }
        .table-wrapper { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 12px; background: #f8fafc; font-weight: 600; font-size: 12px; border-bottom: 2px solid #e2e8f0; }
        td { padding: 12px; font-size: 13px; border-bottom: 1px solid #e2e8f0; }
        tr:hover { background: #f8fafc; }
        .status-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .status-active { background: #d1fae5; color: #065f46; }
        .status-left { background: #fee2e2; color: #991b1b; }
        
        .pagination { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
        .page-btn {
            padding: 8px 14px;
            border: 1px solid #e2e8f0;
            background: white;
            border-radius: 8px;
            cursor: pointer;
        }
        .page-btn:hover { background: #0f172a; color: white; }
        .page-btn.active { background: #0f172a; color: white; }
        
        .footer { text-align: center; padding: 30px; color: #64748b; font-size: 12px; }
        
        @media (max-width: 768px) { .charts-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-chart-line"></i> HR Analytics Dashboard</h1>
        <p>Upload Excel file - All charts update dynamically when you change filters</p>
    </div>
    
    <div class="container">
        <div class="upload-card" id="uploadCard">
            <i class="fas fa-cloud-upload-alt" style="font-size: 48px; color: #3b82f6; margin-bottom: 15px;"></i>
            <h3>Upload Employee Data Excel File</h3>
            <p style="color: #64748b; margin-top: 8px;">Upload your Employee Joining Data 26.xlsx</p>
            <input type="file" id="fileInput" accept=".xlsx,.xls" style="display: none;">
            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                <i class="fas fa-folder-open"></i> Choose File
            </button>
            <div id="uploadStatus" style="margin-top: 15px;"></div>
        </div>
        
        <div id="dashboard" style="display: none;">
            <div class="stats-grid" id="statsGrid"></div>
            
            <div class="filters">
                <div class="filter-group">
                    <label><i class="fas fa-database"></i> Source:</label>
                    <select id="sourceFilter" onchange="refreshAll()">
                        <option value="all">📊 All Sources (419)</option>
                        <option value="employees">👔 PFSPL Employees (39)</option>
                        <option value="workforce">👷 PFSPL Workforce (324)</option>
                        <option value="contractors">📋 Contractors (56)</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label><i class="fas fa-user-check"></i> Status:</label>
                    <select id="statusFilter" onchange="refreshAll()">
                        <option value="all">🔄 All Status</option>
                        <option value="Active">✅ Active</option>
                        <option value="Left">❌ Left</option>
                    </select>
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-card">
                    <h3><i class="fas fa-calendar"></i> Yearly Joining Trends</h3>
                    <canvas id="yearlyChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3><i class="fas fa-chart-pie"></i> Active vs Left Distribution</h3>
                    <canvas id="statusChart"></canvas>
                </div>
            </div>
            
            <div class="dept-section">
                <h3><i class="fas fa-building"></i> Department-wise Analysis</h3>
                <div class="dept-grid" id="deptGrid"></div>
            </div>
            
            <div class="data-table">
                <h3><i class="fas fa-users"></i> Employee Directory</h3>
                <input type="text" class="search-box" id="searchInput" placeholder="Search by name or department...">
                <div class="table-wrapper">
                    <table>
                        <thead><tr><th>Name</th><th>Department</th><th>Source</th><th>DOJ</th><th>Left Date</th><th>Status</th><th>Tenure</th></tr></thead>
                        <tbody id="tableBody"></tbody>
                    </table>
                </div>
                <div class="pagination" id="pagination"></div>
            </div>
        </div>
        
        <div class="footer">
            <i class="fas fa-chart-line"></i> Interactive Dashboard | Filters update all charts in real-time
        </div>
    </div>
    
    <script>
        let yearlyChart, statusChart;
        let currentPage = 1;
        let totalPages = 1;
        
        document.getElementById('fileInput').addEventListener('change', function(e) {
            if (e.target.files[0]) uploadFile();
        });
        
        async function uploadFile() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('uploadStatus').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            
            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('uploadStatus').innerHTML = `<i class="fas fa-check-circle" style="color: #10b981;"></i> Loaded ${result.total} records`;
                    document.getElementById('dashboard').style.display = 'block';
                    refreshAll();
                } else {
                    document.getElementById('uploadStatus').innerHTML = `<i class="fas fa-exclamation-circle" style="color: #ef4444;"></i> Error: ${result.error}`;
                }
            } catch (error) {
                document.getElementById('uploadStatus').innerHTML = `<i class="fas fa-exclamation-circle" style="color: #ef4444;"></i> Upload failed`;
            }
        }
        
        async function refreshAll() {
            await loadFilteredData();
            await loadEmployees();
        }
        
        async function loadFilteredData() {
            const source = document.getElementById('sourceFilter').value;
            const status = document.getElementById('statusFilter').value;
            const response = await fetch(`/api/filtered_data?source=${source}&status=${status}`);
            const data = await response.json();
            
            // Update stats
            document.getElementById('statsGrid').innerHTML = `
                <div class="stat-card"><div class="stat-icon">👥</div><div class="stat-value">${data.total}</div><div class="stat-label">Total Personnel</div></div>
                <div class="stat-card"><div class="stat-icon">✅</div><div class="stat-value">${data.active}</div><div class="stat-label">Active</div></div>
                <div class="stat-card"><div class="stat-icon">❌</div><div class="stat-value">${data.left}</div><div class="stat-label">Left</div></div>
                <div class="stat-card"><div class="stat-icon">⏱️</div><div class="stat-value">${data.avg_tenure}</div><div class="stat-label">Avg Tenure (Yrs)</div></div>
                <div class="stat-card"><div class="stat-icon">🏢</div><div class="stat-value">${data.departments}</div><div class="stat-label">Departments</div></div>
            `;
            
            // Update Yearly Chart
            const years = Object.keys(data.yearly_trends);
            const counts = Object.values(data.yearly_trends);
            if (yearlyChart) yearlyChart.destroy();
            yearlyChart = new Chart(document.getElementById('yearlyChart'), {
                type: 'bar',
                data: { labels: years, datasets: [{ label: 'New Joiners', data: counts, backgroundColor: '#3b82f6', borderRadius: 8 }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'top' } } }
            });
            
            // Update Status Chart
            if (statusChart) statusChart.destroy();
            statusChart = new Chart(document.getElementById('statusChart'), {
                type: 'pie',
                data: { labels: ['Active', 'Left'], datasets: [{ data: [data.active, data.left], backgroundColor: ['#10b981', '#ef4444'] }] },
                options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'top' } } }
            });
            
            // Update Department Grid
            const deptGrid = document.getElementById('deptGrid');
            deptGrid.innerHTML = '';
            for (const [dept, stats] of Object.entries(data.dept_stats)) {
                const turnClass = stats.turnover > 30 ? 'turnover-high' : (stats.turnover > 15 ? 'turnover-medium' : 'turnover-low');
                const color = stats.turnover > 30 ? '#dc2626' : (stats.turnover > 15 ? '#f59e0b' : '#10b981');
                deptGrid.innerHTML += `
                    <div class="dept-item" style="border-left-color: ${color}">
                        <div class="dept-name">${dept}</div>
                        <div class="dept-stats">
                            <span>📊 Total: <strong>${stats.total}</strong></span>
                            <span>✅ Active: <strong>${stats.active}</strong></span>
                            <span>❌ Left: <strong>${stats.left}</strong></span>
                            <span>📈 Turnover: <strong class="${turnClass}">${stats.turnover}%</strong></span>
                        </div>
                    </div>
                `;
            }
        }
        
        async function loadEmployees() {
            const source = document.getElementById('sourceFilter').value;
            const status = document.getElementById('statusFilter').value;
            const response = await fetch(`/api/employees?source=${source}&status=${status}&page=${currentPage}`);
            const result = await response.json();
            
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            result.data.forEach(row => {
                tbody.innerHTML += `
                    <tr>
                        <td>${row.name}</td>
                        <td>${row.dept}</td>
                        <td>${row.source}</td>
                        <td>${row.doj}</td>
                        <td>${row.left_date || 'Active'}</td>
                        <td><span class="status-badge status-${row.status === 'Active' ? 'active' : 'left'}">${row.status}</span></td>
                        <td>${row.tenure_years} yrs</td>
                    </tr>
                `;
            });
            
            totalPages = result.total_pages;
            renderPagination();
        }
        
        function renderPagination() {
            const paginationDiv = document.getElementById('pagination');
            paginationDiv.innerHTML = '';
            
            if (totalPages <= 1) return;
            
            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn';
            prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => { if (currentPage > 1) { currentPage--; loadEmployees(); } };
            paginationDiv.appendChild(prevBtn);
            
            for (let i = 1; i <= Math.min(totalPages, 5); i++) {
                const btn = document.createElement('button');
                btn.className = 'page-btn';
                if (i === currentPage) btn.classList.add('active');
                btn.textContent = i;
                btn.onclick = () => { currentPage = i; loadEmployees(); };
                paginationDiv.appendChild(btn);
            }
            
            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn';
            nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => { if (currentPage < totalPages) { currentPage++; loadEmployees(); } };
            paginationDiv.appendChild(nextBtn);
        }
        
        document.getElementById('searchInput').addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#tableBody tr');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    print("\n" + "="*60)
    print("📊 INTERACTIVE HR ANALYTICS DASHBOARD")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("📂 Upload your Excel file")
    print("✅ All charts update when you change Source or Status filters")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)