from flask import Flask, render_template_string, jsonify, request
import pandas as pd
import numpy as np
from collections import defaultdict
import json

app = Flask(__name__)

# Load and process Excel data
file_path = 'Best Efficiency Moulding Nov.25 to Jan.26.xlsx'

def load_all_data():
    """Load and process all employee efficiency data"""
    try:
        excel_file = pd.ExcelFile(file_path)
        sheets = ['Efficiency Nov.25', 'Efficiency Dec.25', 'Jan.26', 'Feb.26']
        
        employee_data = defaultdict(lambda: {'dates': [], 'efficiencies': [], 'months': []})
        
        for sheet in sheets:
            if sheet in excel_file.sheet_names:
                # Find the header row
                df_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
                header_row = None
                for idx, row in df_raw.iterrows():
                    if 'Sr. No.' in str(row.values):
                        header_row = idx
                        break
                
                if header_row is not None:
                    df = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
                    df = df.dropna(subset=['Sr. No.'], how='all')
                    
                    if 'Operator name' in df.columns:
                        df = df[df['Operator name'].notna()]
                        df = df[~df['Operator name'].astype(str).str.contains('Daily|operator|Production', case=False, na=False)]
                        
                        # Get date columns
                        date_columns = []
                        for col in df.columns:
                            try:
                                if col not in ['Sr. No.', 'Operator name', 'Skills ***', 'Skills']:
                                    num_val = float(col) if not isinstance(col, (int, float)) else col
                                    if isinstance(num_val, (int, float)):
                                        date_columns.append(col)
                            except (ValueError, TypeError):
                                pass
                        
                        for _, row in df.iterrows():
                            emp_name = row['Operator name']
                            if pd.isna(emp_name):
                                continue
                            
                            for col in date_columns:
                                value = row[col]
                                if pd.notna(value) and value != '' and value != 0:
                                    try:
                                        eff_value = float(value)
                                        if 0 < eff_value < 500:
                                            employee_data[emp_name]['dates'].append(f"{sheet[-5:]}-{col}")
                                            employee_data[emp_name]['efficiencies'].append(eff_value)
                                            employee_data[emp_name]['months'].append(sheet)
                                    except:
                                        pass
        
        return employee_data
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

# Load data globally
EMPLOYEE_DATA = load_all_data()
EMPLOYEES = sorted(EMPLOYEE_DATA.keys())

def get_employee_stats(emp_name):
    """Calculate statistics for an employee"""
    if emp_name not in EMPLOYEE_DATA:
        return None
    
    data = EMPLOYEE_DATA[emp_name]
    efficiencies = data['efficiencies']
    
    if not efficiencies:
        return None
    
    avg_eff = np.mean(efficiencies)
    median_eff = np.median(efficiencies)
    std_eff = np.std(efficiencies)
    max_eff = max(efficiencies)
    min_eff = min(efficiencies)
    above_100 = sum(1 for e in efficiencies if e > 100)
    above_target = sum(1 for e in efficiencies if e >= 100)
    below_target = len(efficiencies) - above_target
    
    if len(efficiencies) > 1:
        slope = np.polyfit(range(len(efficiencies)), efficiencies, 1)[0]
        if slope > 0.5:
            trend = "improving"
        elif slope < -0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    if avg_eff >= 100:
        rating = "excellent"
    elif avg_eff >= 90:
        rating = "good"
    elif avg_eff >= 80:
        rating = "satisfactory"
    else:
        rating = "needs_improvement"
    
    return {
        'name': emp_name,
        'average': round(avg_eff, 2),
        'median': round(median_eff, 2),
        'std_dev': round(std_eff, 2),
        'max': round(max_eff, 2),
        'min': round(min_eff, 2),
        'above_100_count': above_100,
        'above_target_count': above_target,
        'below_target_count': below_target,
        'total_days': len(efficiencies),
        'trend': trend,
        'rating': rating,
        'dates': data['dates'],
        'efficiencies': efficiencies
    }

# HTML Template with embedded CSS and JavaScript
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Employee Efficiency Dashboard | Puja Fluid Seals</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .header {
            background: white;
            padding: 20px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .logo h1 {
            color: #667eea;
            font-size: 24px;
        }

        .logo p {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }

        .search-box {
            display: flex;
            gap: 10px;
        }

        .search-box input {
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            width: 250px;
            transition: all 0.3s;
        }

        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }

        .search-box button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .search-box button:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
            cursor: pointer;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }

        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }

        .stat-card .trend {
            font-size: 14px;
            margin-top: 10px;
        }

        .trend-up { color: #48bb78; }
        .trend-down { color: #f56565; }
        .trend-stable { color: #4299e1; }

        .charts-section {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .chart-card h3 {
            margin-bottom: 20px;
            color: #333;
            font-size: 18px;
        }

        .employee-selector {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .selector-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }

        .employee-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            max-height: 200px;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }

        .employee-item {
            padding: 10px;
            background: #f7f7f7;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }

        .employee-item:hover {
            background: #667eea;
            color: white;
            transform: translateX(5px);
        }

        .employee-item.active {
            background: #667eea;
            color: white;
        }

        .quick-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .action-btn {
            padding: 10px 20px;
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }

        .action-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }

        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .header {
                flex-direction: column;
                text-align: center;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }

        .loading {
            text-align: center;
            padding: 50px;
            font-size: 18px;
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <h1>📊 Employee Efficiency Dashboard</h1>
            <p>Puja Fluid Seals Pvt. Ltd. | Performance Monitoring System</p>
        </div>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search employee..." onkeyup="searchEmployee()">
            <button onclick="searchAndSelect()">Search</button>
        </div>
    </div>

    <div class="container">
        <div class="quick-actions">
            <button class="action-btn" onclick="showTopPerformers()">🏆 Top Performers</button>
            <button class="action-btn" onclick="showNeedsImprovement()">⚠️ Needs Improvement</button>
            <button class="action-btn" onclick="showComparison()">📊 Compare Employees</button>
            <button class="action-btn" onclick="exportData()">📁 Export Report</button>
        </div>

        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <h3>Average Efficiency</h3>
                <div class="value" id="avgEfficiency">--</div>
                <div class="trend" id="avgTrend">--</div>
            </div>
            <div class="stat-card">
                <h3>Days Above 100%</h3>
                <div class="value" id="daysAbove100">--</div>
                <div class="trend">⭐ Exceptional Performance</div>
            </div>
            <div class="stat-card">
                <h3>Highest Score</h3>
                <div class="value" id="maxEfficiency">--</div>
                <div class="trend">🎯 Target Achieved</div>
            </div>
            <div class="stat-card">
                <h3>Performance Rating</h3>
                <div class="value" id="performanceRating">--</div>
                <div class="trend" id="ratingTrend">--</div>
            </div>
        </div>

        <div class="employee-selector">
            <div class="selector-title">👥 Select Employee</div>
            <div class="employee-list" id="employeeList">
                Loading employees...
            </div>
        </div>

        <div class="charts-section">
            <div class="chart-card">
                <h3>📈 Efficiency Trend Over Time</h3>
                <div id="trendChart"></div>
            </div>
            <div class="chart-card">
                <h3>📊 Efficiency Distribution</h3>
                <div id="distributionChart"></div>
            </div>
        </div>

        <div class="charts-section">
            <div class="chart-card">
                <h3>🎯 Performance Gauge</h3>
                <div id="gaugeChart"></div>
            </div>
            <div class="chart-card">
                <h3>📋 Detailed Statistics</h3>
                <div id="detailedStats" style="padding: 20px;"></div>
            </div>
        </div>
    </div>

    <script>
        let currentEmployee = null;
        let allEmployees = [];

        async function loadEmployees() {
            try {
                const response = await fetch('/api/employees');
                const data = await response.json();
                allEmployees = data.employees;
                displayEmployeeList(allEmployees);
                
                if (allEmployees.length > 0) {
                    selectEmployee(allEmployees[0]);
                }
            } catch (error) {
                console.error('Error loading employees:', error);
            }
        }

        function displayEmployeeList(employees) {
            const listDiv = document.getElementById('employeeList');
            if (employees.length === 0) {
                listDiv.innerHTML = '<div class="employee-item">No employees found</div>';
                return;
            }
            
            listDiv.innerHTML = employees.map(emp => `
                <div class="employee-item" onclick="selectEmployee('${emp.replace(/'/g, "\\'")}')">
                    ${emp}
                </div>
            `).join('');
        }

        function searchEmployee() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allEmployees.filter(emp => 
                emp.toLowerCase().includes(searchTerm)
            );
            displayEmployeeList(filtered);
        }

        function searchAndSelect() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const found = allEmployees.find(emp => 
                emp.toLowerCase().includes(searchTerm)
            );
            if (found) {
                selectEmployee(found);
            } else {
                alert('Employee not found!');
            }
        }

        async function selectEmployee(employeeName) {
            currentEmployee = employeeName;
            
            document.querySelectorAll('.employee-item').forEach(item => {
                if (item.textContent === employeeName) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
            
            try {
                const response = await fetch(`/api/employee/${encodeURIComponent(employeeName)}`);
                const data = await response.json();
                
                if (data.error) {
                    console.error(data.error);
                    return;
                }
                
                updateDashboard(data);
            } catch (error) {
                console.error('Error loading employee data:', error);
            }
        }

        function updateDashboard(data) {
            document.getElementById('avgEfficiency').innerHTML = `${data.average}%`;
            document.getElementById('daysAbove100').innerHTML = data.above_100_count;
            document.getElementById('maxEfficiency').innerHTML = `${data.max}%`;
            
            const ratingText = {
                'excellent': 'EXCELLENT 🌟🌟🌟',
                'good': 'GOOD 🌟🌟',
                'satisfactory': 'SATISFACTORY 🌟',
                'needs_improvement': 'NEEDS IMPROVEMENT ⚠️'
            };
            document.getElementById('performanceRating').innerHTML = ratingText[data.rating];
            
            const trendText = {
                'improving': '📈 Improving',
                'declining': '📉 Declining',
                'stable': '➡️ Stable'
            };
            document.getElementById('avgTrend').innerHTML = trendText[data.trend];
            
            // Trend chart
            const trace1 = {
                x: data.dates,
                y: data.efficiencies,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Efficiency',
                line: { color: '#667eea', width: 3 },
                marker: { size: 8, color: '#764ba2' }
            };
            
            const layout1 = {
                title: 'Efficiency Trend',
                xaxis: { title: 'Date', tickangle: -45 },
                yaxis: { title: 'Efficiency (%)', range: [0, Math.max(150, Math.max(...data.efficiencies) + 20)] },
                hovermode: 'closest',
                shapes: [{
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    y0: 100,
                    y1: 100,
                    xref: 'paper',
                    yref: 'y',
                    line: { color: 'red', width: 2, dash: 'dash' }
                }]
            };
            
            Plotly.newPlot('trendChart', [trace1], layout1, { responsive: true });
            
            // Distribution chart
            const trace2 = {
                x: data.efficiencies,
                type: 'histogram',
                marker: { color: '#48bb78' },
                nbinsx: 15
            };
            
            const layout2 = {
                title: 'Efficiency Distribution',
                xaxis: { title: 'Efficiency (%)' },
                yaxis: { title: 'Frequency' },
                shapes: [{
                    type: 'line',
                    x0: 100,
                    x1: 100,
                    y0: 0,
                    y1: 1,
                    xref: 'x',
                    yref: 'paper',
                    line: { color: 'red', width: 2, dash: 'dash' }
                }]
            };
            
            Plotly.newPlot('distributionChart', [trace2], layout2, { responsive: true });
            
            // Gauge chart
            const gaugeData = [{
                type: 'indicator',
                mode: 'gauge+number+delta',
                value: data.average,
                title: { text: 'Average Efficiency', font: { size: 24 } },
                delta: { reference: 100 },
                gauge: {
                    axis: { range: [0, 150], tickwidth: 1 },
                    bar: { color: data.average >= 100 ? '#48bb78' : data.average >= 85 ? '#4299e1' : '#f56565' },
                    bgcolor: 'white',
                    borderwidth: 2,
                    bordercolor: 'gray',
                    steps: [
                        { range: [0, 85], color: '#fed7d7' },
                        { range: [85, 100], color: '#feebc8' },
                        { range: [100, 150], color: '#c6f6d5' }
                    ],
                    threshold: {
                        line: { color: 'red', width: 4 },
                        thickness: 0.75,
                        value: 100
                    }
                }
            }];
            
            const gaugeLayout = { width: 500, height: 400, margin: { t: 25, r: 25, l: 25, b: 25 } };
            Plotly.newPlot('gaugeChart', gaugeData, gaugeLayout, { responsive: true });
            
            // Detailed statistics
            const statsHtml = `
                <div style="line-height: 2;">
                    <p><strong>📊 Employee:</strong> ${data.name}</p>
                    <p><strong>📈 Average Efficiency:</strong> ${data.average}%</p>
                    <p><strong>📍 Median Efficiency:</strong> ${data.median}%</p>
                    <p><strong>📊 Standard Deviation:</strong> ${data.std_dev}</p>
                    <p><strong>🏆 Highest Score:</strong> ${data.max}%</p>
                    <p><strong>📉 Lowest Score:</strong> ${data.min}%</p>
                    <p><strong>⭐ Days Above 100%:</strong> ${data.above_100_count}</p>
                    <p><strong>🎯 Days Above Target (≥100%):</strong> ${data.above_target_count}</p>
                    <p><strong>⚠️ Days Below Target (<100%):</strong> ${data.below_target_count}</p>
                    <p><strong>📅 Total Days Tracked:</strong> ${data.total_days}</p>
                    <p><strong>📊 Performance Trend:</strong> ${trendText[data.trend]}</p>
                    <p><strong>⭐ Rating:</strong> ${ratingText[data.rating]}</p>
                </div>
            `;
            document.getElementById('detailedStats').innerHTML = statsHtml;
        }

        async function showTopPerformers() {
            try {
                const response = await fetch('/api/top_performers');
                const performers = await response.json();
                
                let message = "🏆 TOP PERFORMERS 🏆\\n\\n";
                performers.forEach((p, i) => {
                    message += `${i+1}. ${p.name}\\n   Average: ${p.average}% - ${p.rating.toUpperCase()}\\n\\n`;
                });
                
                alert(message);
            } catch (error) {
                console.error('Error loading top performers:', error);
            }
        }

        async function showNeedsImprovement() {
            try {
                const response = await fetch('/api/needs_improvement');
                const employees = await response.json();
                
                if (employees.length === 0) {
                    alert("✅ Great job! No employees currently need improvement!");
                } else {
                    let message = "⚠️ EMPLOYEES NEEDING IMPROVEMENT ⚠️\\n\\n";
                    employees.forEach((emp, i) => {
                        message += `${i+1}. ${emp.name}\\n   Average: ${emp.average}% (Below 85%)\\n\\n`;
                    });
                    alert(message);
                }
            } catch (error) {
                console.error('Error loading needs improvement:', error);
            }
        }

        async function showComparison() {
            const empNames = prompt("Enter employee names to compare (comma-separated, max 5):\\nExample: Anil Patel, Bhola, Aman Singh");
            if (empNames) {
                const employees = empNames.split(',').map(e => e.trim()).slice(0, 5);
                try {
                    const response = await fetch('/api/compare', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ employees: employees })
                    });
                    const comparison = await response.json();
                    
                    let message = "📊 EMPLOYEE COMPARISON 📊\\n\\n";
                    comparison.forEach(emp => {
                        message += `${emp.name}\\n`;
                        message += `  Average: ${emp.average}%\\n`;
                        message += `  Max: ${emp.max}%\\n`;
                        message += `  Min: ${emp.min}%\\n`;
                        message += `  Trend: ${emp.trend}\\n\\n`;
                    });
                    alert(message);
                } catch (error) {
                    console.error('Error comparing employees:', error);
                }
            }
        }

        function exportData() {
            if (currentEmployee) {
                const url = `/api/employee/${encodeURIComponent(currentEmployee)}`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        let csv = "Date,Efficiency (%)\\n";
                        data.dates.forEach((date, i) => {
                            csv += `${date},${data.efficiencies[i]}\\n`;
                        });
                        
                        const blob = new Blob([csv], { type: 'text/csv' });
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = `${currentEmployee}_efficiency_data.csv`;
                        link.click();
                        alert("✅ Data exported successfully!");
                    });
            }
        }

        loadEmployees();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE, employees=EMPLOYEES)

@app.route('/api/employees')
def get_employees():
    """Get list of all employees"""
    return jsonify({'employees': EMPLOYEES})

@app.route('/api/employee/<name>')
def get_employee(name):
    """Get data for specific employee"""
    stats = get_employee_stats(name)
    if stats:
        return jsonify(stats)
    return jsonify({'error': 'Employee not found'}), 404

@app.route('/api/top_performers')
def top_performers():
    """Get top 10 performers"""
    performers = []
    for emp in EMPLOYEES:
        stats = get_employee_stats(emp)
        if stats and stats['total_days'] >= 3:
            performers.append({
                'name': emp,
                'average': stats['average'],
                'rating': stats['rating']
            })
    
    performers.sort(key=lambda x: x['average'], reverse=True)
    return jsonify(performers[:10])

@app.route('/api/needs_improvement')
def needs_improvement():
    """Get employees needing improvement"""
    improvement = []
    for emp in EMPLOYEES:
        stats = get_employee_stats(emp)
        if stats and stats['average'] < 85 and stats['total_days'] >= 3:
            improvement.append({
                'name': emp,
                'average': stats['average']
            })
    
    improvement.sort(key=lambda x: x['average'])
    return jsonify(improvement)

@app.route('/api/compare', methods=['POST'])
def compare_employees():
    """Compare multiple employees"""
    data = request.json
    employees = data.get('employees', [])
    
    comparison = []
    for emp in employees[:5]:  # Max 5 employees
        stats = get_employee_stats(emp)
        if stats:
            comparison.append({
                'name': emp,
                'average': stats['average'],
                'max': stats['max'],
                'min': stats['min'],
                'trend': stats['trend']
            })
    
    return jsonify(comparison)

if __name__ == '__main__':
    print("="*60)
    print("🚀 EMPLOYEE EFFICIENCY DASHBOARD")
    print("="*60)
    print(f"✅ Loaded {len(EMPLOYEES)} employees")
    print(f"📊 Excel file: {file_path}")
    print("\n🌐 Starting Flask server...")
    print("👉 Open your browser and go to: http://localhost:5000")
    print("="*60)
    app.run(debug=True, port=5000)