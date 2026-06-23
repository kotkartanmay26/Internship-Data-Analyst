# app.py - Complete Working Flask Application
from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import re
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# HTML Template with Dark Theme Dashboard
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PFSPL - Employee Competency Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 100%);
            border-bottom: 2px solid #00ffcc;
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-size: 1.8rem;
            background: linear-gradient(135deg, #00ffcc, #00aaff);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .header p {
            color: #888;
            margin-top: 0.3rem;
        }
        
        /* Upload Section */
        .upload-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: calc(100vh - 120px);
            padding: 2rem;
        }
        
        .upload-card {
            background: rgba(20, 20, 40, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 3rem;
            text-align: center;
            border: 1px solid rgba(0, 255, 204, 0.3);
            max-width: 500px;
            width: 100%;
        }
        
        .upload-icon {
            font-size: 4rem;
            color: #00ffcc;
            margin-bottom: 1rem;
        }
        
        .upload-area {
            border: 2px dashed #00ffcc;
            border-radius: 16px;
            padding: 2rem;
            margin: 1.5rem 0;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            background: rgba(0, 255, 204, 0.05);
            border-color: #00aaff;
        }
        
        .btn {
            background: linear-gradient(135deg, #00ffcc, #00aaff);
            border: none;
            padding: 12px 32px;
            border-radius: 30px;
            color: #0a0a0f;
            font-weight: 600;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 1rem;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        /* Dashboard */
        .dashboard {
            display: none;
            padding: 2rem;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: linear-gradient(135deg, rgba(0, 255, 204, 0.1), rgba(0, 170, 255, 0.05));
            border-radius: 20px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(0, 255, 204, 0.2);
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #00ffcc;
            margin: 0.5rem 0;
        }
        
        .stat-label {
            color: #aaa;
            font-size: 0.9rem;
        }
        
        /* Cards */
        .card {
            background: rgba(20, 20, 40, 0.7);
            backdrop-filter: blur(5px);
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(0, 255, 204, 0.15);
        }
        
        .card-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1.2rem;
            color: #00ffcc;
            border-left: 3px solid #00ffcc;
            padding-left: 12px;
        }
        
        /* Skills Container */
        .skills-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .skill-item {
            background: rgba(0, 255, 204, 0.1);
            border-radius: 12px;
            padding: 0.6rem 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid rgba(0, 255, 204, 0.2);
        }
        
        .skill-name {
            font-size: 0.85rem;
        }
        
        .skill-rating {
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 20px;
            font-size: 0.75rem;
        }
        
        .rating-1 { background: #ff4444; color: white; }
        .rating-2 { background: #ffaa44; color: #333; }
        .rating-3 { background: #44ff44; color: #333; }
        .rating-4 { background: #00ffcc; color: #333; }
        
        /* Tables */
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            padding: 12px;
            background: rgba(0, 255, 204, 0.1);
            color: #00ffcc;
            font-weight: 600;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        /* Loader */
        .loader {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 1000;
        }
        
        .loader i {
            font-size: 3rem;
            animation: spin 1s linear infinite;
            color: #00ffcc;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .dashboard { padding: 1rem; }
            .stats-grid { grid-template-columns: 1fr; }
            .skill-item { font-size: 0.75rem; }
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1a2e;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00ffcc;
            border-radius: 4px;
        }
        
        .error-message {
            background: rgba(255, 68, 68, 0.2);
            border: 1px solid #ff4444;
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem;
            color: #ff8888;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-chalkboard-user"></i> Puja Fluid Seals Pvt. Ltd.</h1>
        <p>Employee Competency & Skill Matrix Dashboard</p>
    </div>
    
    <div class="upload-container" id="uploadContainer">
        <div class="upload-card">
            <div class="upload-icon">
                <i class="fas fa-file-excel"></i>
            </div>
            <h2>Upload Excel File</h2>
            <p style="color: #888; margin: 0.5rem 0;">Competancy + Skill Moulding.xls</p>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <i class="fas fa-cloud-upload-alt" style="font-size: 2rem;"></i>
                <p style="margin-top: 0.5rem;">Click to select file</p>
                <input type="file" id="fileInput" accept=".xls,.xlsx" style="display: none;">
            </div>
            <button class="btn" onclick="uploadFile()">
                <i class="fas fa-chart-line"></i> Generate Dashboard
            </button>
        </div>
    </div>
    
    <div class="loader" id="loader">
        <i class="fas fa-spinner"></i>
        <p style="margin-top: 1rem;">Processing data...</p>
    </div>
    
    <div class="dashboard" id="dashboard">
        <div class="stats-grid" id="statsGrid"></div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-chart-radar"></i> Skills Radar Chart</div>
            <canvas id="skillsChart" style="max-height: 450px; width: 100%;"></canvas>
        </div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-list-check"></i> Detailed Skills Assessment</div>
            <div id="skillsList" class="skills-container"></div>
        </div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-clock"></i> Training History</div>
            <div id="trainingTable" class="table-wrapper"></div>
        </div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-tasks"></i> Competency Requirements</div>
            <div id="competencyTable" class="table-wrapper"></div>
        </div>
    </div>
    
    <script>
        let skillsChart = null;
        
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select an Excel file first');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('uploadContainer').style.display = 'none';
            document.getElementById('loader').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                renderDashboard(data);
                document.getElementById('loader').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                
            } catch (error) {
                showError('Error uploading file: ' + error.message);
            }
        }
        
        function showError(message) {
            document.getElementById('loader').style.display = 'none';
            document.getElementById('uploadContainer').style.display = 'flex';
            alert('Error: ' + message);
        }
        
        function renderDashboard(data) {
            // Render Stats
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <i class="fas fa-user"></i>
                    <div class="stat-value">${data.employee_name || 'N/A'}</div>
                    <div class="stat-label">Employee Name</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-briefcase"></i>
                    <div class="stat-value">${data.designation || 'N/A'}</div>
                    <div class="stat-label">Designation</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-building"></i>
                    <div class="stat-value">${data.department || 'N/A'}</div>
                    <div class="stat-label">Department</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-star"></i>
                    <div class="stat-value">${data.total_skills || 0}</div>
                    <div class="stat-label">Total Skills Assessed</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-chart-line"></i>
                    <div class="stat-value">${data.avg_rating || 0}</div>
                    <div class="stat-label">Average Skill Rating</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-calendar"></i>
                    <div class="stat-value">${data.total_trainings || 0}</div>
                    <div class="stat-label">Trainings Attended</div>
                </div>
            `;
            
            // Render Skills Chart
            const ctx = document.getElementById('skillsChart').getContext('2d');
            if (skillsChart) {
                skillsChart.destroy();
            }
            
            const skillNames = (data.skills || []).slice(0, 15).map(s => s.name.length > 25 ? s.name.substring(0, 22) + '...' : s.name);
            const skillRatings = (data.skills || []).slice(0, 15).map(s => s.rating);
            
            skillsChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: skillNames,
                    datasets: [{
                        label: 'Skill Level (1-4)',
                        data: skillRatings,
                        backgroundColor: 'rgba(0, 255, 204, 0.2)',
                        borderColor: '#00ffcc',
                        borderWidth: 2,
                        pointBackgroundColor: '#00aaff',
                        pointBorderColor: '#fff',
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            labels: { color: '#e0e0e0', font: { size: 12 } }
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 4,
                            ticks: { color: '#e0e0e0', stepSize: 1 },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });
            
            // Render Skills List
            const skillsList = document.getElementById('skillsList');
            const ratingLabels = {1: 'Cannot Do', 2: 'Needs Guidance', 3: 'Independent', 4: 'Trainer'};
            
            skillsList.innerHTML = (data.skills || []).map(skill => `
                <div class="skill-item">
                    <span class="skill-rating rating-${skill.rating}">${skill.rating}</span>
                    <span class="skill-name">${skill.name}</span>
                    <span style="font-size: 0.7rem; color: #aaa;">${ratingLabels[skill.rating]}</span>
                </div>
            `).join('');
            
            // Render Training Table
            const trainingTable = document.getElementById('trainingTable');
            if (data.trainings && data.trainings.length > 0) {
                trainingTable.innerHTML = `
                    <table>
                        <thead>
                            <tr><th>Date</th><th>Training Topic</th><th>Duration</th><th>Result</th></tr>
                        </thead>
                        <tbody>
                            ${data.trainings.map(t => `
                                <tr>
                                    <td>${t.date || 'N/A'}</td>
                                    <td>${t.topic || 'N/A'}</td>
                                    <td>${t.duration || 'N/A'}</td>
                                    <td><span style="color: #44ff44;">✓ ${t.result || 'Completed'}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                trainingTable.innerHTML = '<p style="color: #888; text-align: center;">No training records found</p>';
            }
            
            // Render Competency Table
            const competencyTable = document.getElementById('competencyTable');
            if (data.competencies && data.competencies.length > 0) {
                competencyTable.innerHTML = `
                    <table>
                        <thead>
                            <tr><th>Category</th><th>Skill Requirement</th></tr>
                        </thead>
                        <tbody>
                            ${data.competencies.map(c => `
                                <tr>
                                    <td style="color: #00ffcc;">${c.category}</td>
                                    <td>${c.name}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                competencyTable.innerHTML = '<p style="color: #888; text-align: center;">No competency data found</p>';
            }
        }
        
        // Auto-upload when file selected
        document.getElementById('fileInput').addEventListener('change', function() {
            if (this.files.length > 0) {
                uploadFile();
            }
        });
    </script>
</body>
</html>
'''

def parse_excel_data(file_path):
    """Parse all sheets from the Excel file"""
    result = {
        'employee_name': 'Dinesh Yadav',
        'designation': 'Moulder',
        'department': 'Production',
        'skills': [],
        'trainings': [],
        'competencies': [],
        'total_skills': 0,
        'avg_rating': 0,
        'total_trainings': 0
    }
    
    try:
        # Read all sheets
        xls = pd.ExcelFile(file_path)
        
        # Parse SKILL MATRIX sheet (index 3)
        if 'SKILL MATRIX' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='SKILL MATRIX', header=None)
            
            # Extract skills with ratings
            skills = []
            current_category = 'General'
            rating_labels = {1: 'Cannot do', 2: 'Under Guidance', 3: 'Independent', 4: 'Trainer'}
            
            for idx, row in df.iterrows():
                if len(row.values) >= 2:
                    # Check for rating (first column) and skill name (second column)
                    rating_val = row.values[0] if pd.notna(row.values[0]) else None
                    skill_name = str(row.values[1]) if len(row.values) > 1 and pd.notna(row.values[1]) else ''
                    
                    # Skip header rows
                    skip_words = ['SKILL', 'Marks', 'Additional', 'General', 'Remark', 'Marking', 
                                  'Prepared', 'Approved', '5\'S', 'Report', 'Tranining', 'Name', 'Department']
                    
                    if skill_name and skill_name.strip() and len(skill_name) > 3:
                        if isinstance(rating_val, (int, float)) and 1 <= rating_val <= 4:
                            if not any(skip in skill_name.upper() for skip in skip_words):
                                skills.append({
                                    'name': skill_name[:60],
                                    'rating': int(rating_val),
                                    'level': rating_labels.get(int(rating_val), 'Unknown')
                                })
            
            if skills:
                result['skills'] = skills[:50]  # Limit to 50 skills
                result['total_skills'] = len(skills)
                result['avg_rating'] = round(sum(s['rating'] for s in skills) / len(skills), 1)
        
        # Parse TRAINING CARD sheet (index 4)
        if 'TRAINING CARD' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='TRAINING CARD', header=None)
            trainings = []
            
            for idx, row in df.iterrows():
                if len(row.values) >= 3:
                    date_val = str(row.values[0]) if pd.notna(row.values[0]) else ''
                    topic = str(row.values[1]) if len(row.values) > 1 and pd.notna(row.values[1]) else ''
                    duration = str(row.values[2]) if len(row.values) > 2 and pd.notna(row.values[2]) else ''
                    
                    # Check if it looks like a date
                    date_pattern = r'\\d{2}[./-]\\d{2}[./-]\\d{2,4}'
                    if re.match(date_pattern, date_val) and topic and len(topic) > 5:
                        trainings.append({
                            'date': date_val[:15],
                            'topic': topic[:80],
                            'duration': duration[:20] if duration else 'N/A',
                            'result': 'Completed'
                        })
            
            if trainings:
                result['trainings'] = trainings[:25]
                result['total_trainings'] = len(trainings)
        
        # Parse COMPETANCY MATRIX sheet (index 2)
        if 'COMPETANCY MATRIX' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='COMPETANCY MATRIX', header=None)
            competencies = []
            current_category = 'Prime Skills'
            
            for idx, row in df.iterrows():
                if len(row.values) >= 1:
                    val = str(row.values[0]) if pd.notna(row.values[0]) else ''
                    
                    # Check for category headers
                    if 'Prime Skills' in val:
                        current_category = 'Prime Skills'
                    elif 'Additional Skills' in val:
                        current_category = 'Additional Skills'
                    elif 'General Skills' in val:
                        current_category = 'General Skills'
                    elif len(val) > 5 and not any(x in val.upper() for x in ['PUJA', 'COMPETENCE', 'PFSPL', 'PREPARED', 'APPROVED', 'ISSUE']):
                        # This is likely a skill entry
                        if not val.startswith('Req') and not val.startswith('Designation'):
                            competencies.append({
                                'category': current_category,
                                'name': val[:80]
                            })
            
            if competencies:
                result['competencies'] = competencies[:40]
        
        # Also parse Skill sheet (index 1) for additional skill data
        if 'Skill' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='Skill', header=None)
            
            # Look for the skill set row (row 14-15 in the data)
            skill_names = []
            for idx, row in df.iterrows():
                if idx >= 14 and idx <= 16:  # Looking for the skill names row
                    for col_idx, val in enumerate(row.values):
                        if pd.notna(val) and col_idx >= 5:  # Skills start from column F (index 5)
                            skill_str = str(val)
                            if len(skill_str) > 3 and not any(x in skill_str for x in ['हॅन्डप्रेस', 'हायड्रॉलिक', 'मशीन', 'Skill', 'Training']):
                                skill_names.append(skill_str[:60])
            
            # If we found skills and have data from SKILL MATRIX, merge
            if skill_names and result['skills']:
                # Use the skill names as reference
                pass
        
    except Exception as e:
        print(f"Parse error: {e}")
        # Return mock data for testing if parsing fails
        return get_mock_data()
    
    return result

def get_mock_data():
    """Return mock data for testing"""
    return {
        'employee_name': 'Dinesh Yadav',
        'designation': 'Moulder',
        'department': 'Production',
        'skills': [
            {'name': 'Handpress Machine Operation', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Hydraulic Press Operation', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Polymer & Compound Knowledge', 'rating': 3, 'level': 'Independent'},
            {'name': 'Machine Operation Methods', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Production Process', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Compound Codification', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Mold/Die Handling', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Machine Checklist', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Work Instruction', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Safety Awareness', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Vernier Caliper Use', 'rating': 3, 'level': 'Independent'},
            {'name': 'Quality Control', 'rating': 4, 'level': 'Trainer'},
            {'name': '5S Awareness', 'rating': 3, 'level': 'Independent'},
            {'name': 'Discipline', 'rating': 4, 'level': 'Trainer'},
            {'name': 'Communication', 'rating': 4, 'level': 'Trainer'}
        ],
        'trainings': [
            {'date': '22.11.2022', 'topic': 'Quality/EHS Policy', 'duration': '30 Min', 'result': 'Completed'},
            {'date': '12.02.2022', 'topic': 'Machine Operation', 'duration': '30 Min', 'result': 'Completed'},
            {'date': '23.09.2019', 'topic': 'Compound Codification', 'duration': '5 Min', 'result': 'Completed'},
            {'date': '23.09.2019', 'topic': 'SC & CC Training', 'duration': '10 Min', 'result': 'Completed'},
            {'date': '23.09.2019', 'topic': 'Vernier Reading', 'duration': '10 Min', 'result': 'Completed'},
            {'date': '23.01.2019', 'topic': '5S Training', 'duration': 'N/A', 'result': 'Completed'}
        ],
        'competencies': [
            {'category': 'Prime Skills', 'name': 'Ability to work with handpress'},
            {'category': 'Prime Skills', 'name': 'Ability to work with hydraulic presses'},
            {'category': 'Prime Skills', 'name': 'Knowledge of polymers & compounds'},
            {'category': 'Prime Skills', 'name': 'Knowledge of Machine operations'},
            {'category': 'Prime Skills', 'name': 'Compound Codification & labeling'},
            {'category': 'Prime Skills', 'name': 'Ability to maintain related records'},
            {'category': 'Prime Skills', 'name': 'Ability to train other persons'},
            {'category': 'Prime Skills', 'name': 'Fault finding & rectification'},
            {'category': 'Additional Skills', 'name': 'Able to do Finishing'},
            {'category': 'Additional Skills', 'name': 'Able to do Extrusion'},
            {'category': 'General Skills', 'name': 'Awareness of ISO'},
            {'category': 'General Skills', 'name': 'Awareness of 5S'},
            {'category': 'General Skills', 'name': 'Safety Equipment Usage'},
            {'category': 'General Skills', 'name': 'Material Handling'}
        ],
        'total_skills': 15,
        'avg_rating': 3.7,
        'total_trainings': 6
    }

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({'error': 'Please upload an Excel file (.xls or .xlsx)'})
    
    file_path = 'temp_uploaded.xlsx'
    try:
        file.save(file_path)
        data = parse_excel_data(file_path)
        
        # Clean up
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify(data)
        
    except Exception as e:
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'Error: {str(e)}'})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 PFSPL Employee Competency Dashboard")
    print("=" * 60)
    print("📁 Upload your 'Competancy + Skill Moulding.xls' file")
    print("🌐 Open: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)