from flask import Flask, jsonify, render_template_string, request
import pandas as pd
from datetime import datetime

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Contractor Attrition Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 { color: #667eea; font-size: 2.2em; margin-bottom: 10px; }
        .upload-card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            cursor: pointer;
            background: #f8f9ff;
            transition: all 0.3s;
        }
        .upload-area:hover { background: #e8ebff; border-color: #764ba2; }
        .upload-icon { font-size: 48px; margin-bottom: 15px; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            margin-top: 15px;
            font-size: 16px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 48px; font-weight: bold; margin-bottom: 10px; }
        .stat-label { color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .stat-sub { font-size: 12px; margin-top: 8px; }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 25px;
            margin-bottom: 25px;
        }
        .chart-card {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .chart-card h3 { margin-bottom: 20px; color: #333; border-left: 4px solid #667eea; padding-left: 15px; }
        .table-card {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .table-card h3 { margin-bottom: 20px; color: #333; border-left: 4px solid #667eea; padding-left: 15px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; position: sticky; top: 0; }
        tr:hover { background: #f5f5f5; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .high { background: #ffebee; color: #c62828; }
        .medium { background: #fff3e0; color: #ef6c00; }
        .low { background: #e8f5e9; color: #2e7d32; }
        .file-info { margin-top: 15px; color: #666; font-size: 14px; }
        .sheet-selector {
            margin-top: 20px;
            padding: 15px;
            background: #f0f2ff;
            border-radius: 10px;
            display: none;
        }
        select {
            padding: 8px 15px;
            border-radius: 8px;
            border: 1px solid #667eea;
            margin-left: 10px;
            font-size: 14px;
        }
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .charts-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Contractor Employee Attrition Dashboard</h1>
            <p>Upload Excel file - Only CONTRACTOR sheet will be analyzed</p>
        </div>

        <div class="upload-card">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <h3>Click or Drag & Drop Excel File</h3>
                <p style="color:#666; margin-top:10px;">Supports .xlsx, .xls files</p>
                <input type="file" id="fileInput" accept=".xlsx,.xls" style="display:none">
                <button class="btn" onclick="document.getElementById('fileInput').click()">Select File</button>
            </div>
            <div class="file-info" id="fileInfo"></div>
        </div>

        <div id="results" style="display: none;">
            <div class="stats-grid" id="statsGrid"></div>
            <div class="charts-grid">
                <div class="chart-card">
                    <h3>📈 Employee Status Distribution</h3>
                    <canvas id="statusChart" height="250"></canvas>
                </div>
                <div class="chart-card">
                    <h3>📊 Top Departments by Attrition Rate</h3>
                    <canvas id="deptChart" height="250"></canvas>
                </div>
            </div>
            <div class="table-card">
                <h3>🏢 Department-wise Detailed Analysis</h3>
                <div style="overflow-x: auto; max-height: 500px; overflow-y: auto;">
                    <table>
                        <thead>
                            <tr><th>Department</th><th>Total</th><th>Working</th><th>Left</th><th>Attrition Rate</th><th>Status</th></tr>
                        </thead>
                        <tbody id="deptTableBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let statusChart, deptChart;
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.onclick = () => fileInput.click();
        uploadArea.ondragover = (e) => { e.preventDefault(); uploadArea.style.background = '#e8ebff'; };
        uploadArea.ondragleave = () => { uploadArea.style.background = '#f8f9ff'; };
        uploadArea.ondrop = (e) => {
            e.preventDefault();
            uploadArea.style.background = '#f8f9ff';
            if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        };
        
        fileInput.onchange = (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); };
        
        async function handleFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('fileInfo').innerHTML = '⏳ Processing Contractor sheet only...';
            
            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                document.getElementById('results').style.display = 'block';
                document.getElementById('fileInfo').innerHTML = `✅ Loaded: ${file.name}<br>📊 CONTRACTOR SHEET ONLY: ${data.total} valid contractors (${data.working} working, ${data.left} left)`;
                
                // Update stats
                const attrition_rate = ((data.left / data.total) * 100).toFixed(1);
                document.getElementById('statsGrid').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number" style="color:#667eea">${data.total}</div>
                        <div class="stat-label">Total Contractors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color:#4caf50">${data.working}</div>
                        <div class="stat-label">Currently Working</div>
                        <div class="stat-sub">Active contractors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color:#f44336">${data.left}</div>
                        <div class="stat-label">Left</div>
                        <div class="stat-sub">${((data.left/data.total)*100).toFixed(1)}% Attrition</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color:#ff9800">${attrition_rate}%</div>
                        <div class="stat-label">Overall Attrition Rate</div>
                    </div>
                `;
                
                // Status chart
                if (statusChart) statusChart.destroy();
                statusChart = new Chart(document.getElementById('statusChart'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Working (' + data.working + ')', 'Left (' + data.left + ')'],
                        datasets: [{ data: [data.working, data.left], backgroundColor: ['#4caf50', '#f44336'], borderWidth: 0 }]
                    },
                    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }
                });
                
                // Department chart
                const topDepts = data.departments.slice(0, 10);
                if (deptChart) deptChart.destroy();
                deptChart = new Chart(document.getElementById('deptChart'), {
                    type: 'bar',
                    data: {
                        labels: topDepts.map(d => d.name),
                        datasets: [{ label: 'Attrition Rate (%)', data: topDepts.map(d => d.attrition), backgroundColor: '#667eea', borderRadius: 8 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: 'Attrition Rate (%)' } } }
                    }
                });
                
                // Department table
                const tbody = document.getElementById('deptTableBody');
                tbody.innerHTML = '';
                data.departments.forEach(dept => {
                    let badgeClass = 'low';
                    if (dept.attrition > 70) badgeClass = 'high';
                    else if (dept.attrition > 30) badgeClass = 'medium';
                    
                    let statusText = '';
                    if (dept.attrition === 0) statusText = '✅ Stable';
                    else if (dept.attrition < 30) statusText = '⚠️ Moderate';
                    else statusText = '🔴 Critical';
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${dept.name}</strong></td>
                            <td>${dept.total}</td>
                            <td style="color:#4caf50; font-weight:bold;">${dept.working}</td>
                            <td style="color:#f44336; font-weight:bold;">${dept.left}</td>
                            <td><span class="badge ${badgeClass}">${dept.attrition}%</span></td>
                            <td>${statusText}</td>
                        </tr>
                    `;
                });
                
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file:
        return jsonify({'error': 'No file uploaded'})
    
    try:
        # Read ONLY the Contractor sheet
        df = pd.read_excel(file, sheet_name='Contractor', header=None)
        
        contractors = []
        
        for idx in range(1, len(df)):  # Start from row 1 to skip header
            row = df.iloc[idx]
            
            # Get Name (column 1)
            name = row[1] if len(row) > 1 and pd.notna(row[1]) else ''
            name_str = str(name).strip()
            
            # Skip empty names or invalid rows
            if not name_str or name_str == '' or name_str.lower() in ['nan', 'none', '']:
                continue
            
            # Get Department (column 2)
            dept = row[2] if len(row) > 2 and pd.notna(row[2]) else 'Unknown'
            dept = str(dept).strip()
            
            # Get Left Date (column 4)
            left_date = row[4] if len(row) > 4 and pd.notna(row[4]) else ''
            left_date_str = str(left_date).strip()
            
            # Check if left date exists (not empty)
            has_left = left_date_str != '' and left_date_str.lower() not in ['nan', 'none']
            
            contractors.append({
                'name': name_str,
                'dept': dept,
                'has_left': has_left
            })
        
        # Calculate statistics
        total = len(contractors)
        working = sum(1 for c in contractors if not c['has_left'])
        left = total - working
        
        # Department analysis
        dept_stats = {}
        for c in contractors:
            dept = c['dept']
            if dept not in dept_stats:
                dept_stats[dept] = {'total': 0, 'left': 0}
            dept_stats[dept]['total'] += 1
            if c['has_left']:
                dept_stats[dept]['left'] += 1
        
        departments = []
        for dept, stats in dept_stats.items():
            attrition = round((stats['left'] / stats['total']) * 100, 1)
            departments.append({
                'name': dept,
                'total': stats['total'],
                'working': stats['total'] - stats['left'],
                'left': stats['left'],
                'attrition': attrition
            })
        
        # Sort by attrition rate descending
        departments.sort(key=lambda x: x['attrition'], reverse=True)
        
        print(f"DEBUG: Total contractors found: {total}, Working: {working}, Left: {left}")
        
        return jsonify({
            'total': total,
            'working': working,
            'left': left,
            'departments': departments
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" CONTRACTOR ATTRITION DASHBOARD")
    print("="*60)
    print("\n✅ Reading ONLY the 'Contractor' sheet from your Excel file")
    print("✅ Open: http://localhost:5000")
    print("✅ Upload your 'Employee Joining Data 26.xlsx' file")
    print("\n📊 EXPECTED RESULTS:")
    print("   • Total Contractors: 55")
    print("   • Currently Working: 6")
    print("   • Left: 49")
    print("   • Overall Attrition Rate: 89.1%")
    print("\n" + "="*60)
    print("🎯 Running on: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)