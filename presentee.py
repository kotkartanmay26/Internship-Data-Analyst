from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import numpy as np
import os
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# =======================================================
# DATA PROCESSING FUNCTIONS
# =======================================================

def safe_float(val):
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    try:
        if isinstance(val, str) and val.strip() == '':
            return 0.0
        if isinstance(val, str) and '=' in val:
            return 0.0
        return float(val)
    except:
        return 0.0

def load_and_process_data(filepath):
    """Load Excel file and process ONLY the M sheet."""
    try:
        df_m = pd.read_excel(filepath, sheet_name='M', header=None)
        data_m = []
        
        for idx in range(2, len(df_m)):
            row = df_m.iloc[idx]
            name = row[1] if len(row) > 1 and pd.notna(row[1]) else None
            if name is None or str(name).strip() == '':
                continue
            
            name_str = str(name).strip()
            if name_str and not name_str.startswith('Total') and not name_str.startswith('=SUM') and not name_str.startswith('SUM'):
                
                months = ['Apr.25', 'May.25', 'Jun.25', 'Jul.25', 'Aug.25', 'Sep.25', 
                         'Oct.25', 'Nov.25', 'Dec.25', 'Jan.26', 'Feb.26', 'Mar.26']
                
                for i, month in enumerate(months):
                    base_col = 2 + (i * 4)
                    if base_col + 3 < len(row):
                        td = safe_float(row[base_col])
                        pd_val = safe_float(row[base_col + 1])
                        ad = safe_float(row[base_col + 2])
                        percent = safe_float(row[base_col + 3]) if base_col + 3 < len(row) else 0
                        
                        if percent == 0 and td > 0 and pd_val > 0:
                            percent = (pd_val / td) * 100
                        elif percent > 0 and td > 0:
                            percent = min(percent, 100)
                        
                        if td > 0:
                            data_m.append({
                                'Employee': name_str,
                                'Month': month,
                                'TD': td,
                                'PD': pd_val,
                                'AD': ad if ad > 0 else round(td - pd_val, 1),
                                'Percentage': round(percent if percent <= 100 else (pd_val/td*100 if td>0 else 0), 1),
                                'Sheet': 'M'
                            })
        
        df_all = pd.DataFrame(data_m)
        
        if df_all.empty:
            return pd.DataFrame()
        
        month_order = ['Apr.25', 'May.25', 'Jun.25', 'Jul.25', 'Aug.25', 'Sep.25', 
                      'Oct.25', 'Nov.25', 'Dec.25', 'Jan.26', 'Feb.26', 'Mar.26']
        
        existing_months = [m for m in month_order if m in df_all['Month'].values]
        df_all = df_all[df_all['Month'].isin(existing_months)]
        df_all['Month'] = pd.Categorical(df_all['Month'], categories=existing_months, ordered=True)
        
        return df_all
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

def calculate_aggregates(df):
    """Calculate aggregate statistics."""
    if df.empty:
        return None
    
    try:
        total_employees = int(df['Employee'].nunique())
        total_td = float(df['TD'].sum())
        total_pd = float(df['PD'].sum())
        total_ad = float(df['AD'].sum())
        overall_percentage = float((total_pd / total_td * 100) if total_td > 0 else 0)
        
        monthly_stats = df.groupby('Month', observed=True).agg({
            'TD': 'sum', 'PD': 'sum', 'AD': 'sum'
        }).reset_index()
        monthly_stats['Percentage'] = (monthly_stats['PD'] / monthly_stats['TD'] * 100).fillna(0)
        
        employee_stats = df.groupby('Employee').agg({
            'TD': 'sum', 'PD': 'sum', 'AD': 'sum'
        }).reset_index()
        employee_stats['Percentage'] = (employee_stats['PD'] / employee_stats['TD'] * 100).fillna(0)
        employee_stats = employee_stats.sort_values('Percentage', ascending=False)
        
        absent_trend = df.groupby('Month', observed=True)['AD'].sum().reset_index()
        
        # FIXED: Store data for ALL employees, not just first 50
        employee_monthly_data = {}
        all_employees_list = employee_stats['Employee'].tolist()
        
        for employee in all_employees_list:
            emp_df = df[df['Employee'] == employee]
            emp_monthly = []
            for month in monthly_stats['Month'].tolist():
                month_data = emp_df[emp_df['Month'] == month]
                if not month_data.empty:
                    emp_monthly.append({
                        'month': str(month),
                        'percentage': float(month_data['Percentage'].iloc[0]),
                        'pd': float(month_data['PD'].iloc[0]),
                        'td': float(month_data['TD'].iloc[0])
                    })
                else:
                    emp_monthly.append({
                        'month': str(month), 
                        'percentage': 0, 
                        'pd': 0, 
                        'td': 0
                    })
            employee_monthly_data[employee] = emp_monthly
        
        # Heatmap data - top 40 for better visibility
        top_employees = employee_stats.head(40)['Employee'].tolist()
        df_heatmap = df[df['Employee'].isin(top_employees)]
        heatmap_data = df_heatmap.pivot_table(index='Employee', columns='Month', values='Percentage', fill_value=0)
        
        performance_buckets = {
            'Excellent (90-100%)': len(employee_stats[employee_stats['Percentage'] >= 90]),
            'Good (75-89%)': len(employee_stats[(employee_stats['Percentage'] >= 75) & (employee_stats['Percentage'] < 90)]),
            'Average (60-74%)': len(employee_stats[(employee_stats['Percentage'] >= 60) & (employee_stats['Percentage'] < 75)]),
            'Below Avg (40-59%)': len(employee_stats[(employee_stats['Percentage'] >= 40) & (employee_stats['Percentage'] < 60)]),
            'Critical (<40%)': len(employee_stats[employee_stats['Percentage'] < 40])
        }
        
        return {
            'total_employees': total_employees,
            'total_td': round(total_td, 1),
            'total_pd': round(total_pd, 1),
            'total_ad': round(total_ad, 1),
            'overall_percentage': round(overall_percentage, 1),
            'monthly_labels': [str(m) for m in monthly_stats['Month'].tolist()],
            'monthly_pd': [round(x, 1) for x in monthly_stats['PD'].tolist()],
            'monthly_ad': [round(x, 1) for x in monthly_stats['AD'].tolist()],
            'monthly_percentages': [round(x, 1) for x in monthly_stats['Percentage'].tolist()],
            'employee_labels': [str(e) for e in employee_stats['Employee'].head(15).tolist()],
            'employee_percentages': [round(x, 1) for x in employee_stats['Percentage'].head(15).tolist()],
            'bottom_employee_labels': [str(e) for e in employee_stats['Employee'].tail(10).tolist()],
            'bottom_employee_percentages': [round(x, 1) for x in employee_stats['Percentage'].tail(10).tolist()],
            'absent_labels': [str(m) for m in absent_trend['Month'].tolist()],
            'absent_values': [round(x, 1) for x in absent_trend['AD'].tolist()],
            'heatmap_employees': [str(e) for e in heatmap_data.index.tolist()],
            'heatmap_months': [str(m) for m in heatmap_data.columns.tolist()],
            'heatmap_values': [[round(val, 1) for val in row] for row in heatmap_data.values.tolist()],
            'employee_monthly_data': employee_monthly_data,  # NOW CONTAINS ALL EMPLOYEES
            'all_employees': all_employees_list,
            'performance_buckets': performance_buckets,
            'employee_table': [
                {'Employee': str(row['Employee']), 'TD': round(row['TD'], 1), 'PD': round(row['PD'], 1), 
                 'AD': round(row['AD'], 1), 'Percentage': round(row['Percentage'], 1)} 
                for _, row in employee_stats.head(100).iterrows()
            ],
            'monthly_table': [
                {'Month': str(row['Month']), 'TD': round(row['TD'], 1), 'PD': round(row['PD'], 1), 
                 'AD': round(row['AD'], 1), 'Percentage': round(row['Percentage'], 1)} 
                for _, row in monthly_stats.iterrows()
            ]
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return None

# =======================================================
# HTML TEMPLATE
# =======================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Attendance Analytics | Professional Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0c10;
            color: #e8edf2;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .header {
            text-align: center;
            padding: 40px 30px;
            background: #0f1218;
            border-radius: 20px;
            margin-bottom: 30px;
            border: 1px solid #1a1f2e;
        }
        
        .header h1 {
            font-size: 2.4rem;
            font-weight: 600;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }
        
        .header .badge {
            display: inline-block;
            background: #1a1f2e;
            padding: 6px 16px;
            border-radius: 40px;
            font-size: 0.8rem;
            margin-top: 15px;
            color: #8a94a1;
        }
        
        .header p {
            color: #8a94a1;
            font-size: 0.95rem;
        }
        
        .upload-area {
            background: #0f1218;
            border: 2px dashed #2a2f3e;
            border-radius: 20px;
            padding: 60px;
            text-align: center;
            margin-bottom: 30px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            border-color: #4a6f5e;
            background: #12161e;
        }
        
        .upload-area input {
            display: none;
        }
        
        .upload-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .upload-area h3 {
            font-size: 1.3rem;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .upload-area p {
            color: #6a7380;
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            background: #0f1218;
            border-radius: 20px;
            display: none;
            border: 1px solid #1a1f2e;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid #1a1f2e;
            border-top-color: #00ff88;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            background: #1a0f0f;
            border: 1px solid #ff4444;
            border-radius: 16px;
            padding: 16px 24px;
            margin-bottom: 20px;
            display: none;
            color: #ff8888;
        }
        
        .error.active {
            display: block;
        }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .kpi-card {
            background: #0f1218;
            border-radius: 20px;
            padding: 24px;
            text-align: center;
            border: 1px solid #1a1f2e;
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: #2a2f3e;
        }
        
        .kpi-card h3 {
            font-size: 0.75rem;
            color: #8a94a1;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }
        
        .kpi-card .value {
            font-size: 2.2rem;
            font-weight: 600;
            color: #e8edf2;
        }
        
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(550px, 1fr));
            gap: 24px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: #0f1218;
            border-radius: 20px;
            padding: 20px;
            border: 1px solid #1a1f2e;
        }
        
        .chart-card h3 {
            margin-bottom: 16px;
            font-size: 1rem;
            font-weight: 500;
            color: #e8edf2;
            border-left: 3px solid #00ff88;
            padding-left: 12px;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        .employee-selector {
            background: #0f1218;
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 24px;
            border: 1px solid #1a1f2e;
        }
        
        .employee-selector h3 {
            margin-bottom: 16px;
            font-size: 1rem;
            font-weight: 500;
            border-left: 3px solid #ffaa44;
            padding-left: 12px;
            color: #e8edf2;
        }
        
        .employee-search {
            width: 100%;
            padding: 12px 16px;
            background: #0a0c10;
            border: 1px solid #1a1f2e;
            border-radius: 12px;
            color: #e8edf2;
            font-size: 0.9rem;
            margin-bottom: 16px;
        }
        
        .employee-search:focus {
            outline: none;
            border-color: #3a4a5e;
        }
        
        .employee-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            max-height: 200px;
            overflow-y: auto;
            padding: 4px;
        }
        
        .employee-list::-webkit-scrollbar {
            width: 5px;
        }
        
        .employee-list::-webkit-scrollbar-track {
            background: #0a0c10;
            border-radius: 5px;
        }
        
        .employee-list::-webkit-scrollbar-thumb {
            background: #2a2f3e;
            border-radius: 5px;
        }
        
        .employee-btn {
            padding: 8px 16px;
            background: #0a0c10;
            border: 1px solid #1a1f2e;
            border-radius: 30px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s;
            color: #e8edf2;
        }
        
        .employee-btn:hover {
            border-color: #4a6f5e;
        }
        
        .employee-btn.active {
            background: #1a2a2a;
            border-color: #00ff88;
        }
        
        .employee-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .emp-stat-card {
            background: #0a0c10;
            border-radius: 14px;
            padding: 14px;
            text-align: center;
            border: 1px solid #1a1f2e;
        }
        
        .emp-stat-card .label {
            font-size: 0.65rem;
            color: #8a94a1;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .emp-stat-card .value {
            font-size: 1.6rem;
            font-weight: 600;
            margin-top: 6px;
            color: #e8edf2;
        }
        
        .tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .tab-btn {
            background: #0a0c10;
            border: 1px solid #1a1f2e;
            padding: 10px 24px;
            border-radius: 30px;
            cursor: pointer;
            color: #e8edf2;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        
        .tab-btn:hover {
            border-color: #4a6f5e;
        }
        
        .tab-btn.active {
            background: #1a2a2a;
            border-color: #00ff88;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #1a1f2e;
        }
        
        th {
            background: #12161e;
            color: #8a94a1;
            font-weight: 500;
            font-size: 0.8rem;
        }
        
        tr:hover {
            background: #12161e;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: #5a636e;
            font-size: 0.75rem;
            border-top: 1px solid #1a1f2e;
            margin-top: 30px;
        }
        
        @media (max-width: 1200px) {
            .chart-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            .kpi-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }
            .kpi-card .value {
                font-size: 1.6rem;
            }
            .employee-stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 M-Sheet Attendance Analytics</h1>
            <p>Enterprise attendance intelligence | Real-time insights | Employee analytics</p>
            <div class="badge">M-Sheet Data Only | Professional Dashboard</div>
        </div>
        
        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
            <input type="file" id="fileInput" accept=".xlsx,.xls">
            <div class="upload-icon">📁</div>
            <h3>Upload Excel File (M-Sheet)</h3>
            <p>Supports .xlsx and .xls formats</p>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processing attendance data...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div id="dashboard" style="display: none;">
            <!-- KPI Cards -->
            <div class="kpi-grid" id="kpiGrid"></div>
            
            <!-- Performance Distribution -->
            <div class="chart-grid">
                <div class="chart-card full-width">
                    <h3>Employee Performance Distribution</h3>
                    <div id="performanceChart"></div>
                </div>
            </div>
            
            <!-- Main Charts -->
            <div class="chart-grid">
                <div class="chart-card">
                    <h3>Overall Attendance Gauge</h3>
                    <div id="gaugeChart"></div>
                </div>
                <div class="chart-card">
                    <h3>Present vs Absent Distribution</h3>
                    <div id="donutChart"></div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-card">
                    <h3>Monthly Attendance Overview</h3>
                    <div id="monthlyBarChart"></div>
                </div>
                <div class="chart-card">
                    <h3>Attendance Percentage Trend</h3>
                    <div id="trendLineChart"></div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-card">
                    <h3>Absenteeism Trend Analysis</h3>
                    <div id="absentAreaChart"></div>
                </div>
                <div class="chart-card">
                    <h3>Attendance Distribution</h3>
                    <div id="histogramChart"></div>
                </div>
            </div>
            
            <!-- Rankings -->
            <div class="chart-grid">
                <div class="chart-card full-width">
                    <h3>Top 15 High Performers</h3>
                    <div id="topBarChart"></div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-card full-width">
                    <h3>Bottom 10 - Needs Improvement</h3>
                    <div id="bottomBarChart"></div>
                </div>
            </div>
            
            <!-- Heatmap -->
            <div class="chart-grid">
                <div class="chart-card full-width">
                    <h3>Employee Attendance Heatmap</h3>
                    <div id="heatmapChart"></div>
                </div>
            </div>
            
            <!-- Employee Deep Dive -->
            <div class="employee-selector">
                <h3>👤 Employee Deep Dive Analytics</h3>
                <input type="text" class="employee-search" id="employeeSearch" placeholder="Search employee by name..." onkeyup="filterEmployees()">
                <div class="employee-list" id="employeeList"></div>
                
                <div id="employeeAnalytics" style="margin-top: 20px; display: none;">
                    <div class="employee-stats" id="empStats"></div>
                    <div id="employeeTrendChart" style="height: 380px;"></div>
                    <div id="employeeRadarChart" style="height: 380px; margin-top: 20px;"></div>
                </div>
            </div>
            
            <!-- Data Tables -->
            <div class="chart-card">
                <h3>Detailed Data Insights</h3>
                <div class="tabs">
                    <button class="tab-btn active" onclick="showTab('monthly')">Monthly Summary</button>
                    <button class="tab-btn" onclick="showTab('employee')">Employee Performance</button>
                </div>
                <div id="monthlyTab" class="tab-content active">
                    <div class="table-wrapper" id="monthlyTable"></div>
                </div>
                <div id="employeeTab" class="tab-content">
                    <div class="table-wrapper" id="employeeTable"></div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>M-Sheet Attendance Analytics Dashboard | © 2025</p>
        </div>
    </div>
    
    <script>
        let currentData = null;
        
        document.getElementById('fileInput').addEventListener('change', async function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const dashboard = document.getElementById('dashboard');
            
            loading.classList.add('active');
            error.classList.remove('active');
            dashboard.style.display = 'none';
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok && !data.error) {
                    currentData = data;
                    renderDashboard(data);
                    renderEmployeeList(data);
                    dashboard.style.display = 'block';
                } else {
                    error.textContent = data.error || 'Error processing file.';
                    error.classList.add('active');
                }
            } catch (err) {
                error.textContent = 'Network error. Make sure server is running on port 5000';
                error.classList.add('active');
            } finally {
                loading.classList.remove('active');
            }
        });
        
        function renderDashboard(data) {
            // KPI Cards
            document.getElementById('kpiGrid').innerHTML = `
                <div class="kpi-card"><h3>TOTAL EMPLOYEES</h3><div class="value">${data.total_employees}</div></div>
                <div class="kpi-card"><h3>TOTAL WORKING DAYS</h3><div class="value">${data.total_td}</div></div>
                <div class="kpi-card"><h3>TOTAL PRESENT DAYS</h3><div class="value">${data.total_pd}</div></div>
                <div class="kpi-card"><h3>TOTAL ABSENT DAYS</h3><div class="value">${data.total_ad}</div></div>
                <div class="kpi-card"><h3>ATTENDANCE RATE</h3><div class="value">${data.overall_percentage}%</div></div>
            `;
            
            // Performance Distribution
            const perfBuckets = data.performance_buckets;
            Plotly.newPlot('performanceChart', [{
                x: Object.keys(perfBuckets),
                y: Object.values(perfBuckets),
                type: 'bar',
                marker: { color: ['#00ff88', '#44aaff', '#ffaa44', '#ff8844', '#ff4444'] },
                text: Object.values(perfBuckets),
                textposition: 'auto',
                textfont: { color: '#e8edf2' }
            }], {
                plot_bgcolor: '#0f1218',
                paper_bgcolor: '#0f1218',
                font: { color: '#8a94a1' },
                xaxis: { gridcolor: '#1a1f2e', tickangle: -20 },
                yaxis: { gridcolor: '#1a1f2e', title: 'Number of Employees' },
                height: 350,
                margin: { t: 30, l: 50, r: 30, b: 80 }
            });
            
            // Gauge Chart
            Plotly.newPlot('gaugeChart', [{
                type: 'indicator',
                mode: 'gauge+number',
                value: data.overall_percentage,
                title: { text: 'Attendance Rate', font: { color: '#8a94a1', size: 14 } },
                gauge: {
                    axis: { range: [0, 100], tickcolor: '#444', tickfont: { color: '#8a94a1' } },
                    bar: { color: '#00ff88' },
                    bgcolor: '#0f1218',
                    borderwidth: 1,
                    bordercolor: '#1a1f2e',
                    steps: [
                        { range: [0, 60], color: 'rgba(255, 68, 68, 0.15)' },
                        { range: [60, 75], color: 'rgba(255, 170, 68, 0.15)' },
                        { range: [75, 90], color: 'rgba(0, 255, 136, 0.15)' },
                        { range: [90, 100], color: 'rgba(0, 255, 136, 0.3)' }
                    ],
                    threshold: { line: { color: '#fff', width: 2 }, value: 90 }
                },
                number: { font: { size: 48, color: '#e8edf2' } }
            }], { paper_bgcolor: '#0f1218', height: 380, margin: { t: 60, l: 50, r: 50, b: 50 } });
            
            // Donut Chart
            Plotly.newPlot('donutChart', [{
                type: 'pie',
                values: [data.overall_percentage, 100 - data.overall_percentage],
                labels: ['Present', 'Absent'],
                hole: 0.65,
                marker: { colors: ['#00ff88', '#ff4444'] },
                textinfo: 'percent',
                textfont: { color: '#e8edf2', size: 14 }
            }], { paper_bgcolor: '#0f1218', height: 380, margin: { t: 60, l: 50, r: 50, b: 50 }, showlegend: true, legend: { font: { color: '#8a94a1' }, bgcolor: 'rgba(0,0,0,0)' } });
            
            // Monthly Bar Chart
            Plotly.newPlot('monthlyBarChart', [
                { x: data.monthly_labels, y: data.monthly_pd, name: 'Present Days', type: 'bar', marker: { color: '#00ff88' }, text: data.monthly_pd, textposition: 'auto', textfont: { color: '#e8edf2' } },
                { x: data.monthly_labels, y: data.monthly_ad, name: 'Absent Days', type: 'bar', marker: { color: '#ff4444' }, text: data.monthly_ad, textposition: 'auto', textfont: { color: '#e8edf2' } }
            ], { barmode: 'stack', plot_bgcolor: '#0f1218', paper_bgcolor: '#0f1218', font: { color: '#8a94a1' }, xaxis: { gridcolor: '#1a1f2e' }, yaxis: { gridcolor: '#1a1f2e' }, height: 400, legend: { font: { color: '#8a94a1' }, bgcolor: 'rgba(0,0,0,0)' } });
            
            // Trend Line Chart
            Plotly.newPlot('trendLineChart', [{
                x: data.monthly_labels, y: data.monthly_percentages, type: 'scatter', mode: 'lines+markers',
                line: { color: '#ffaa44', width: 3 }, marker: { size: 10, color: '#ffaa44' },
                text: data.monthly_percentages.map(v => v + '%'), textposition: 'top center', textfont: { color: '#e8edf2' }
            }], { plot_bgcolor: '#0f1218', paper_bgcolor: '#0f1218', font: { color: '#8a94a1' }, xaxis: { gridcolor: '#1a1f2e' }, yaxis: { gridcolor: '#1a1f2e', range: [0, 105] }, height: 400, shapes: [{ type: 'line', y0: 90, y1: 90, x0: 0, x1: 1, xref: 'paper', line: { color: '#00ff88', width: 1.5, dash: 'dash' } }] });
            
            // Absent Area Chart
            Plotly.newPlot('absentAreaChart', [{
                x: data.absent_labels, y: data.absent_values, type: 'scatter', mode: 'lines',
                fill: 'tozeroy', line: { color: '#ff6b6b', width: 2.5 },
                fillcolor: 'rgba(255, 107, 107, 0.2)'
            }], { plot_bgcolor: '#0f1218', paper_bgcolor: '#0f1218', font: { color: '#8a94a1' }, xaxis: { gridcolor: '#1a1f2e' }, yaxis: { gridcolor: '#1a1f2e' }, height: 400 });
            
            // Histogram
            const percentages = data.employee_table.map(e => e.Percentage);
            Plotly.newPlot('histogramChart', [{
                x: percentages,
                type: 'histogram',
                marker: { color: '#44aaff' },
                nbinsx: 20
            }], {
                plot_bgcolor: '#0f1218',
                paper_bgcolor: '#0f1218',
                font: { color: '#8a94a1' },
                xaxis: { title: 'Attendance Percentage', gridcolor: '#1a1f2e', range: [0, 100] },
                yaxis: { title: 'Number of Employees', gridcolor: '#1a1f2e' },
                height: 400,
                bargap: 0.05
            });
            
            // Top Employees
            const topColors = data.employee_percentages.map(p => {
                if (p >= 90) return '#00ff88';
                if (p >= 75) return '#44aaff';
                if (p >= 60) return '#ffaa44';
                return '#ff6666';
            });
            
            Plotly.newPlot('topBarChart', [{
                x: data.employee_percentages, y: data.employee_labels, type: 'bar', orientation: 'h',
                marker: { color: topColors },
                text: data.employee_percentages.map(v => v + '%'), textposition: 'outside', textfont: { color: '#e8edf2' }
            }], { plot_bgcolor: '#0f1218', paper_bgcolor: '#0f1218', font: { color: '#8a94a1' }, xaxis: { gridcolor: '#1a1f2e', range: [0, 105] }, yaxis: { gridcolor: '#1a1f2e' }, height: 520, margin: { l: 220, r: 60, t: 30, b: 30 } });
            
            // Bottom Employees
            Plotly.newPlot('bottomBarChart', [{
                x: data.bottom_employee_percentages, y: data.bottom_employee_labels, type: 'bar', orientation: 'h',
                marker: { color: '#ff6b6b' },
                text: data.bottom_employee_percentages.map(v => v + '%'), textposition: 'outside', textfont: { color: '#e8edf2' }
            }], { plot_bgcolor: '#0f1218', paper_bgcolor: '#0f1218', font: { color: '#8a94a1' }, xaxis: { gridcolor: '#1a1f2e', range: [0, 100] }, yaxis: { gridcolor: '#1a1f2e' }, height: 450, margin: { l: 220, r: 60, t: 30, b: 30 } });
            
            // Heatmap
            Plotly.newPlot('heatmapChart', [{
                z: data.heatmap_values, x: data.heatmap_months, y: data.heatmap_employees,
                type: 'heatmap', colorscale: [[0, '#ff4444'], [0.5, '#ffaa44'], [0.75, '#44aaff'], [1, '#00ff88']],
                zmin: 0, zmax: 100
            }], { plot_bgcolor: '#0f1218', paper_bgcolor: '#0f1218', font: { color: '#8a94a1' }, xaxis: { tickangle: 45 }, yaxis: { tickfont: { size: 10 } }, height: 650 });
            
            // Tables
            renderTables(data);
        }
        
        function renderEmployeeList(data) {
            const container = document.getElementById('employeeList');
            container.innerHTML = data.all_employees.map(emp => 
                `<button class="employee-btn" onclick="selectEmployee('${emp.replace(/'/g, "\\'")}')">👤 ${emp}</button>`
            ).join('');
        }
        
        function filterEmployees() {
            const search = document.getElementById('employeeSearch').value.toLowerCase();
            const btns = document.querySelectorAll('.employee-btn');
            btns.forEach(btn => {
                if (btn.textContent.toLowerCase().includes(search)) {
                    btn.style.display = 'inline-block';
                } else {
                    btn.style.display = 'none';
                }
            });
        }
        
        function selectEmployee(employee) {
            // Update active button
            document.querySelectorAll('.employee-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent === employee || btn.textContent === `👤 ${employee}`) {
                    btn.classList.add('active');
                }
            });
            
            // Get employee data - FIXED: Now works for ALL employees
            const empData = currentData.employee_monthly_data[employee];
            
            if (!empData) {
                console.error('No data found for employee:', employee);
                return;
            }
            
            const months = empData.map(d => d.month);
            const percentages = empData.map(d => d.percentage);
            const pd = empData.map(d => d.pd);
            const td = empData.map(d => d.td);
            
            const totalTD = td.reduce((a, b) => a + b, 0);
            const totalPD = pd.reduce((a, b) => a + b, 0);
            const overallPct = totalTD > 0 ? (totalPD / totalTD * 100).toFixed(1) : 0;
            const avgPct = percentages.filter(p => p > 0).length > 0 ? 
                (percentages.reduce((a, b) => a + b, 0) / percentages.filter(p => p > 0).length).toFixed(1) : 0;
            
            // Update employee stats
            document.getElementById('empStats').innerHTML = `
                <div class="emp-stat-card"><div class="label">Total Days</div><div class="value">${totalTD}</div></div>
                <div class="emp-stat-card"><div class="label">Present Days</div><div class="value">${totalPD}</div></div>
                <div class="emp-stat-card"><div class="label">Absent Days</div><div class="value">${(totalTD - totalPD).toFixed(1)}</div></div>
                <div class="emp-stat-card"><div class="label">Attendance Rate</div><div class="value">${overallPct}%</div></div>
            `;
            
            // Employee Trend Chart (Line + Bar)
            Plotly.newPlot('employeeTrendChart', [
                { 
                    x: months, y: percentages, type: 'scatter', mode: 'lines+markers', name: 'Attendance %',
                    line: { color: '#ffaa44', width: 3 }, 
                    marker: { size: 10, color: '#ffaa44', symbol: 'circle' },
                    text: percentages.map(v => v + '%'), 
                    textposition: 'top center', 
                    textfont: { color: '#e8edf2' },
                    yaxis: 'y1'
                },
                { 
                    x: months, y: pd, type: 'bar', name: 'Present Days', 
                    marker: { color: '#00ff88', opacity: 0.6 },
                    text: pd.map(v => v), 
                    textposition: 'auto',
                    textfont: { color: '#e8edf2' },
                    yaxis: 'y2'
                }
            ], {
                plot_bgcolor: '#0f1218', 
                paper_bgcolor: '#0f1218', 
                font: { color: '#8a94a1' },
                xaxis: { 
                    gridcolor: '#1a1f2e', 
                    tickfont: { color: '#8a94a1' },
                    title: 'Month'
                },
                yaxis: { 
                    title: 'Attendance Percentage (%)', 
                    range: [0, 105], 
                    gridcolor: '#1a1f2e', 
                    tickfont: { color: '#8a94a1' },
                    side: 'left'
                },
                yaxis2: { 
                    title: 'Present Days', 
                    overlaying: 'y', 
                    side: 'right', 
                    gridcolor: '#1a1f2e', 
                    tickfont: { color: '#8a94a1' },
                    showgrid: false
                },
                height: 380, 
                margin: { t: 40, l: 60, r: 70, b: 50 },
                legend: { 
                    font: { color: '#8a94a1' }, 
                    bgcolor: 'rgba(0,0,0,0)',
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: 1.02,
                    xanchor: 'right',
                    x: 1
                }
            });
            
            // Radar Chart for monthly performance comparison
            Plotly.newPlot('employeeRadarChart', [{
                type: 'scatterpolar',
                r: percentages,
                theta: months,
                fill: 'toself',
                name: employee,
                line: { color: '#00ff88', width: 2 },
                marker: { color: '#00ff88', size: 6 },
                text: percentages.map(v => v + '%'),
                hovertemplate: 'Month: %{theta}<br>Attendance: %{r:.1f}%<extra></extra>'
            }], {
                paper_bgcolor: '#0f1218', 
                font: { color: '#8a94a1' },
                polar: { 
                    bgcolor: '#0f1218', 
                    radialaxis: { 
                        range: [0, 100], 
                        gridcolor: '#1a1f2e', 
                        tickfont: { color: '#8a94a1' },
                        title: 'Attendance %'
                    }, 
                    angularaxis: { 
                        gridcolor: '#1a1f2e', 
                        tickfont: { color: '#8a94a1', size: 10 },
                        rotation: 90
                    } 
                },
                height: 380, 
                margin: { t: 40, l: 80, r: 80, b: 80 },
                showlegend: true,
                legend: { font: { color: '#8a94a1' }, bgcolor: 'rgba(0,0,0,0)' }
            });
            
            // Show the analytics section
            document.getElementById('employeeAnalytics').style.display = 'block';
            
            // Scroll to employee analytics
            document.getElementById('employeeAnalytics').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        function renderTables(data) {
            // Monthly Table
            let monthlyHtml = '<table><thead><tr><th>Month</th><th>TD</th><th>PD</th><th>AD</th><th>Percentage</th></tr></thead><tbody>';
            data.monthly_table.forEach(row => {
                monthlyHtml += `<tr><td>${row.Month}</td><td>${row.TD}</td><td>${row.PD}</td><td>${row.AD}</td><td>${row.Percentage}%</td></tr>`;
            });
            monthlyHtml += '</tbody></table>';
            document.getElementById('monthlyTable').innerHTML = monthlyHtml;
            
            // Employee Table
            let employeeHtml = '<table><thead><tr><th>Employee</th><th>TD</th><th>PD</th><th>AD</th><th>Percentage</th></tr></thead><tbody>';
            data.employee_table.forEach(row => {
                employeeHtml += `<tr><td>${row.Employee}</td><td>${row.TD}</td><td>${row.PD}</td><td>${row.AD}</td><td>${row.Percentage}%</td></tr>`;
            });
            employeeHtml += '</tbody></table>';
            document.getElementById('employeeTable').innerHTML = employeeHtml;
        }
        
        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            if (tab === 'monthly') {
                document.getElementById('monthlyTab').classList.add('active');
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
            } else {
                document.getElementById('employeeTab').classList.add('active');
                document.querySelectorAll('.tab-btn')[1].classList.add('active');
            }
        }
    </script>
</body>
</html>
'''

# =======================================================
# FLASK ROUTES
# =======================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file type. Please upload .xlsx or .xls file'}), 400
        
        temp_path = 'temp_upload.xlsx'
        file.save(temp_path)
        
        df_all = load_and_process_data(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if df_all.empty:
            return jsonify({'error': 'No valid data found in M-Sheet.'}), 400
        
        data = calculate_aggregates(df_all)
        
        if data is None:
            return jsonify({'error': 'Error processing data.'}), 400
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    
if __name__ == '__main__':
    print("=" * 60)
    print("M-SHEET ATTENDANCE ANALYTICS DASHBOARD")
    print("=" * 60)
    print("✅ Server is running at: http://localhost:5000")
    print("✅ ALL employees will have individual graphs")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)