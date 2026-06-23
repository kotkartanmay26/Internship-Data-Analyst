"""
Toolroom Efficiency Analyzer - Fixed Version
Save as: app.py
Run with: python app.py
"""

from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Complete HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Toolroom Efficiency Analyzer | Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .navbar {
            background: rgba(255,255,255,0.95);
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            padding: 15px 0;
        }
        .navbar-brand {
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.5rem;
        }
        .hero {
            padding: 50px 0;
            text-align: center;
            color: white;
        }
        .hero h1 { font-size: 2.5rem; margin-bottom: 20px; }
        .upload-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            border: 3px dashed #667eea;
            margin: 20px auto;
            max-width: 500px;
        }
        .upload-card:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 10px; }
        .card-custom {
            border: none;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-bottom: 25px;
            background: white;
        }
        .card-header-custom {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 15px 15px 0 0 !important;
            padding: 15px 20px;
            font-weight: bold;
        }
        .table-custom {
            border-radius: 15px;
            overflow: hidden;
        }
        .table-custom thead {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .badge-up { background: #10b981; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
        .badge-down { background: #ef4444; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
        .badge-stable { background: #f59e0b; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
        .loader {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 9999;
            justify-content: center;
            align-items: center;
        }
        .loader.active { display: flex; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .btn-download {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            margin: 20px;
        }
        footer {
            text-align: center;
            padding: 30px;
            color: white;
        }
        .insight-box {
            background: linear-gradient(135deg, #667eea20, #764ba220);
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
        }
        .table { margin-bottom: 0; }
        .table th { background: #667eea; color: white; }
    </style>
</head>
<body>

<div class="loader" id="loader">
    <div class="spinner"></div>
</div>

<nav class="navbar">
    <div class="container">
        <a class="navbar-brand" href="#">
            <i class="fas fa-chart-line"></i> Toolroom Efficiency Analyzer
        </a>
    </div>
</nav>

<div class="hero">
    <div class="container">
        <h1><i class="fas fa-industry"></i> Operator Performance Dashboard</h1>
        <p class="lead">Upload Excel file to analyze efficiency, trends, and get insights</p>
        
        <div class="upload-card" id="uploadCard">
            <i class="fas fa-cloud-upload-alt fa-4x" style="color: #667eea;"></i>
            <h5 class="mt-3">Click or Drag & Drop Excel File</h5>
            <p class="text-muted">Supports .xlsx, .xls files</p>
            <input type="file" id="fileInput" accept=".xlsx,.xls" style="display: none;">
            <button class="btn btn-primary mt-2" onclick="document.getElementById('fileInput').click()">
                <i class="fas fa-folder-open"></i> Browse
            </button>
        </div>
    </div>
</div>

<div class="container" id="results" style="display: none;">
    <div class="row" id="statsRow"></div>
    
    <div class="row">
        <div class="col-md-6">
            <div class="card-custom">
                <div class="card-header-custom">
                    <i class="fas fa-trophy"></i> Top Performers
                </div>
                <div class="card-body">
                    <canvas id="topChart"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card-custom">
                <div class="card-header-custom">
                    <i class="fas fa-chart-line"></i> Monthly Trend
                </div>
                <div class="card-body">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card-custom">
        <div class="card-header-custom">
            <i class="fas fa-users"></i> Operator Performance Matrix
        </div>
        <div class="card-body">
            <div class="table-responsive" id="tableContainer"></div>
        </div>
    </div>
    
    <div class="card-custom">
        <div class="card-header-custom">
            <i class="fas fa-lightbulb"></i> AI Insights & Recommendations
        </div>
        <div class="card-body" id="insightsContainer"></div>
    </div>
    
    <div class="text-center">
        <button class="btn-download" id="downloadBtn">
            <i class="fas fa-download"></i> Download CSV Report
        </button>
    </div>
</div>

<footer>
    <p><i class="fas fa-chart-simple"></i> Real-time Analytics Dashboard</p>
</footer>

<script>
let currentData = null;

document.getElementById('uploadCard').onclick = () => {
    document.getElementById('fileInput').click();
};

document.getElementById('fileInput').onchange = (e) => {
    if (e.target.files[0]) {
        uploadFile(e.target.files[0]);
    }
};

// Drag and drop
const dropZone = document.getElementById('uploadCard');
dropZone.ondragover = (e) => {
    e.preventDefault();
    dropZone.style.background = '#eef2ff';
};
dropZone.ondragleave = () => {
    dropZone.style.background = 'white';
};
dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.style.background = 'white';
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
        uploadFile(file);
    } else {
        alert('Please upload an Excel file!');
    }
};

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    document.getElementById('loader').classList.add('active');
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loader').classList.remove('active');
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            currentData = data;
            displayResults(data);
            document.getElementById('results').style.display = 'block';
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }
    })
    .catch(error => {
        document.getElementById('loader').classList.remove('active');
        alert('Upload failed: ' + error);
    });
}

function displayResults(data) {
    // Stats Row
    const statsHtml = `
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-value">${data.company_avg}%</div>
                <div class="stat-label">Company Average</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-value">${data.top_performer}</div>
                <div class="stat-label">Top Performer</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-value">${data.total_operators}</div>
                <div class="stat-label">Total Operators</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-value">${data.high_performers}</div>
                <div class="stat-label">Above 95% Target</div>
            </div>
        </div>
    `;
    document.getElementById('statsRow').innerHTML = statsHtml;
    
    // Top Performers Chart
    if (data.top_names && data.top_names.length > 0) {
        const topCtx = document.getElementById('topChart').getContext('2d');
        new Chart(topCtx, {
            type: 'bar',
            data: {
                labels: data.top_names,
                datasets: [{
                    label: 'Avg Efficiency (%)',
                    data: data.top_values,
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    borderRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: false, min: 80, title: { display: true, text: '%' } } }
            }
        });
    }
    
    // Monthly Trend Chart
    if (data.months && data.months.length > 0) {
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Monthly Average',
                    data: data.monthly_avg,
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: 'white',
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: false, min: 80, title: { display: true, text: 'Efficiency (%)' } } }
            }
        });
    }
    
    // Operator Table
    let tableHtml = `<table class="table table-hover">
        <thead>
            <tr><th>Operator</th><th>Avg %</th><th>Latest %</th><th>Trend</th><th>Status</th><th>Action</th></tr>
        </thead>
        <tbody>`;
    data.operators.forEach(op => {
        let trendBadge = '';
        if (op.trend > 0.1) {
            trendBadge = '<span class="badge-up"><i class="fas fa-arrow-up"></i> Improving</span>';
        } else if (op.trend < -0.1) {
            trendBadge = '<span class="badge-down"><i class="fas fa-arrow-down"></i> Declining</span>';
        } else {
            trendBadge = '<span class="badge-stable"><i class="fas fa-minus"></i> Stable</span>';
        }
        
        let actionBadge = '';
        if (op.avg >= 95) actionBadge = '<span class="badge-up">🏆 Excellent</span>';
        else if (op.avg >= 90) actionBadge = '<span class="badge-stable">✅ Good</span>';
        else actionBadge = '<span class="badge-down">⚠️ Needs Training</span>';
        
        tableHtml += `<tr>
            <td><strong>${op.name.substring(0, 30)}</strong></td>
            <td>${op.avg}%</td>
            <td>${op.latest}%</td>
            <td>${trendBadge}</td>
            <td>${op.status || 'Active'}</td>
            <td>${actionBadge}</td>
        </tr>`;
    });
    tableHtml += `</tbody></table>`;
    document.getElementById('tableContainer').innerHTML = tableHtml;
    
    // Insights
    let insightsHtml = '<div class="row">';
    data.insights.forEach(insight => {
        insightsHtml += `<div class="col-md-6"><div class="insight-box"><i class="fas ${insight.icon}"></i> ${insight.text}</div></div>`;
    });
    insightsHtml += '</div>';
    document.getElementById('insightsContainer').innerHTML = insightsHtml;
}

document.getElementById('downloadBtn').onclick = () => {
    if (currentData && currentData.csv_data) {
        const blob = new Blob([currentData.csv_data], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'efficiency_report.csv';
        a.click();
        URL.revokeObjectURL(url);
    }
};
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        # Read Excel file
        df = pd.read_excel(file)
        
        print("Original columns:", df.columns.tolist())
        print("First few rows:\n", df.head())
        
        # Identify columns
        # First 3 columns are typically: Sr_no, Name, Status
        name_col = None
        status_col = None
        
        # Find name column (look for 'Name' or similar)
        for col in df.columns[:5]:
            col_lower = str(col).lower()
            if 'name' in col_lower or 'operator' in col_lower or 'employee' in col_lower:
                name_col = col
                break
        if name_col is None:
            name_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        # Find status column
        for col in df.columns[:5]:
            col_lower = str(col).lower()
            if 'status' in col_lower or 'left' in col_lower:
                status_col = col
                break
        
        # Get month columns (all columns after the first 3 or after name column)
        # Month columns contain numbers (efficiency values)
        month_cols = []
        for col in df.columns:
            # Check if column contains numeric values (efficiency)
            if col not in [name_col, status_col] and col != df.columns[0]:
                # Try to convert to numeric
                test_series = pd.to_numeric(df[col], errors='coerce')
                if test_series.notna().sum() > 0:
                    month_cols.append(col)
        
        print(f"Name column: {name_col}")
        print(f"Status column: {status_col}")
        print(f"Month columns found: {len(month_cols)}")
        
        if len(month_cols) == 0:
            return jsonify({'error': 'No numeric efficiency data found in the file'})
        
        # Prepare data for analysis
        records = []
        for _, row in df.iterrows():
            operator_name = str(row[name_col]) if pd.notna(row[name_col]) else "Unknown"
            if operator_name == "nan" or operator_name == "Unknown":
                continue
                
            status = str(row[status_col]) if status_col and pd.notna(row[status_col]) else "Active"
            
            for month in month_cols:
                efficiency = pd.to_numeric(row[month], errors='coerce')
                if pd.notna(efficiency):
                    records.append({
                        'Name': operator_name,
                        'Status': status,
                        'Month': str(month),
                        'Efficiency': efficiency
                    })
        
        if len(records) == 0:
            return jsonify({'error': 'No valid efficiency data found'})
        
        df_melted = pd.DataFrame(records)
        
        # Calculate operator statistics
        operator_stats = []
        for name in df_melted['Name'].unique():
            op_data = df_melted[df_melted['Name'] == name]
            efficiencies = op_data['Efficiency'].tolist()
            
            avg_eff = np.mean(efficiencies)
            latest_eff = efficiencies[-1] if efficiencies else 0
            
            # Calculate trend (slope)
            if len(efficiencies) > 1:
                x = range(len(efficiencies))
                slope = np.polyfit(x, efficiencies, 1)[0]
            else:
                slope = 0
            
            status = op_data['Status'].iloc[0] if len(op_data) > 0 else "Active"
            
            operator_stats.append({
                'name': name,
                'avg': round(avg_eff, 2),
                'latest': round(latest_eff, 2),
                'trend': round(slope, 2),
                'status': status
            })
        
        operator_df = pd.DataFrame(operator_stats)
        operator_df = operator_df.sort_values('avg', ascending=False)
        
        # Calculate monthly averages
        monthly_avg = df_melted.groupby('Month')['Efficiency'].mean().sort_index()
        
        # Get last 12 months for chart
        months_list = monthly_avg.index.tolist()[-12:] if len(monthly_avg) > 0 else []
        monthly_list = monthly_avg.tolist()[-12:] if len(monthly_avg) > 0 else []
        
        # Top 5 performers
        top_5 = operator_df.head(5)
        
        # Calculate insights
        company_avg = operator_df['avg'].mean()
        total_operators = len(operator_df)
        high_performers = len(operator_df[operator_df['avg'] >= 95])
        low_performers = len(operator_df[operator_df['avg'] < 90])
        declining = operator_df[operator_df['trend'] < -0.1]
        
        insights = []
        
        if company_avg < 90:
            insights.append({'icon': 'fa-exclamation-triangle', 'text': f'⚠️ Company average is {company_avg:.1f}% - Below target! Immediate action needed.'})
        elif company_avg < 95:
            insights.append({'icon': 'fa-chart-line', 'text': f'📊 Company average is {company_avg:.1f}% - Room for improvement to reach 95%.'})
        else:
            insights.append({'icon': 'fa-trophy', 'text': f'🏆 Excellent! Company average is {company_avg:.1f}% - Above target!'})
        
        if low_performers > 0:
            insights.append({'icon': 'fa-user-graduate', 'text': f'📚 {low_performers} operators need training/support (below 90%).'})
        
        if len(declining) > 0:
            names = ', '.join(declining.head(3)['name'].tolist())
            insights.append({'icon': 'fa-chart-line', 'text': f'📉 Declining trend for: {names}. Review performance support.'})
        
        if high_performers > 0:
            insights.append({'icon': 'fa-star', 'text': f'🌟 {high_performers} operators exceed 95% target! Great job!'})
        
        if len(insights) < 3:
            insights.append({'icon': 'fa-calendar-check', 'text': '✅ Continue monthly monitoring and celebrate achievements!'})
        
        # Generate CSV for download
        csv_data = operator_df[['name', 'avg', 'trend', 'status', 'latest']].to_csv(index=False)
        
        return jsonify({
            'company_avg': round(company_avg, 1),
            'top_performer': top_5.iloc[0]['name'] if len(top_5) > 0 else 'N/A',
            'total_operators': total_operators,
            'high_performers': high_performers,
            'top_names': top_5['name'].tolist() if len(top_5) > 0 else [],
            'top_values': top_5['avg'].tolist() if len(top_5) > 0 else [],
            'months': months_list,
            'monthly_avg': monthly_list,
            'operators': operator_df.head(50).to_dict('records'),
            'insights': insights,
            'csv_data': csv_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Toolroom Efficiency Analyzer - STARTING")
    print("="*60)
    print("\n📌 Open your browser and go to: http://localhost:5000")
    print("📁 Upload your Excel file with operator efficiency data")
    print("\n⚠️  Press Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)