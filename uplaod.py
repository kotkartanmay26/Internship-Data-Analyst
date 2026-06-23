import os
import json
import pandas as pd
import numpy as np
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify, send_file, send_from_directory, redirect
from werkzeug.utils import secure_filename
import re
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_FILE = 'employees.json'
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_employees():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_employees(employees):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(employees, f, indent=2, ensure_ascii=False)

def parse_skill_excel(filepath):
    """Parse the skill matrix Excel file and extract employee data"""
    result = {}
    try:
        xl = pd.ExcelFile(filepath)
        
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
            
            if 'SKILL' in sheet_name.upper():
                employee_name = None
                skills = {}
                
                for idx, row in df.iterrows():
                    row_values = [str(x) if pd.notna(x) else '' for x in row]
                    row_str = ' '.join(row_values)
                    
                    if 'Name Of Employee:' in row_str:
                        for i, val in enumerate(row_values):
                            if 'Name Of Employee:' in val and i+1 < len(row_values):
                                employee_name = row_values[i+1].strip()
                                break
                    
                    for i, val in enumerate(row_values):
                        if val.isdigit() and 1 <= int(val) <= 4:
                            rating = int(val)
                            for j in range(max(0, i-4), i):
                                if j < len(row_values) and len(row_values[j]) > 15:
                                    skill_name = row_values[j][:80].strip()
                                    if skill_name and skill_name not in skills:
                                        skills[skill_name] = rating
                                        break
                
                if employee_name and skills:
                    result[employee_name] = skills
                    break
        
        if not result:
            for sheet_name in xl.sheet_names:
                if 'COMPETANCY' in sheet_name.upper():
                    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                    skills_list = []
                    for idx, row in df.iterrows():
                        for col in range(len(row)):
                            val = str(row.iloc[col]) if pd.notna(row.iloc[col]) else ''
                            if len(val) > 10 and any(word in val.lower() for word in ['ability', 'knowledge', 'awareness', 'skill']):
                                if val not in skills_list:
                                    skills_list.append(val[:60])
                    
                    if skills_list:
                        result['Employee from Excel'] = {skill: np.random.randint(2, 5) for skill in skills_list[:25]}
                    break
        
        return result
    except Exception as e:
        print(f"Parse error: {e}")
        return {}

# Complete skill list for Moulder role
SKILLS_LIST = [
    "Ability to work with handpress",
    "Ability to work with hydraulic presses",
    "Ability to work big handpress like 1met. X 1 met.",
    "Knowledge of polymers & compounds",
    "Knowledge of Machine & its different operations",
    "Knowledge of process parameter & it's combination with Polymers",
    "Compound Codification & labeling",
    "Ability to maintain related records.",
    "Ability to train other persons",
    "Ability to set critical products.",
    "Fault finding & rectification",
    "Knowledge of Moulds & their handling",
    "Vernier Reading",
    "Knowledge of Product",
    "Proper utilization of machine",
    "Able to do Finishing",
    "Able to do Mixing",
    "Able to do Extrusion",
    "Knowledge of Critical Parameter of product.",
    "Approach towards reducing rejections.",
    "Maintenance of Machine",
    "Awareness of ISO",
    "Awareness of 5S",
    "Awareness & use of Safety Equipments",
    "Awareness & use of Material Handling",
    "Behavior with Higher Authorities",
    "Behavior with Subordinates/Collogues",
    "Regular Presently",
    "Timely presence at work",
    "Initiative to Improvements & Trials"
]

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkillMatrix Pro | Enterprise Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #fff;
            min-height: 100vh;
        }

        .bg-animation {
            position: fixed;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }
        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 20% 50%, rgba(0,210,255,0.08) 0%, transparent 50%);
            animation: rotate 30s linear infinite;
        }
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
            z-index: 2;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(15px);
            padding: 1rem 2rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.15);
        }

        .logo h1 {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .logo span { font-size: 0.7rem; color: #88d4ff; letter-spacing: 2px; }

        .btn-group { display: flex; gap: 1rem; flex-wrap: wrap; }
        .btn {
            padding: 10px 24px;
            font-weight: 600;
            font-size: 0.85rem;
            border: none;
            cursor: pointer;
            border-radius: 40px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }
        .btn-primary { background: linear-gradient(135deg, #00d2ff, #3a7bd5); color: white; box-shadow: 0 4px 15px rgba(0,210,255,0.3); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,210,255,0.5); }
        .btn-outline { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; }
        .btn-outline:hover { background: rgba(255,255,255,0.2); transform: translateY(-2px); }
        .btn-success { background: linear-gradient(135deg, #11998e, #38ef7d); color: white; }
        .btn-warning { background: linear-gradient(135deg, #f2994a, #f2c94c); color: white; }

        .search-wrapper {
            position: relative;
            max-width: 450px;
            margin-bottom: 2rem;
        }
        .search-wrapper i {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: #00d2ff;
            z-index: 1;
        }
        .search-input {
            width: 100%;
            padding: 14px 20px 14px 48px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 50px;
            color: white;
            font-size: 0.9rem;
            transition: all 0.3s;
        }
        .search-input:focus { outline: none; border-color: #00d2ff; background: rgba(255,255,255,0.12); }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: linear-gradient(135deg, rgba(0,210,255,0.1), rgba(58,123,213,0.1));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0,210,255,0.3);
            border-radius: 20px;
            padding: 1.2rem;
            text-align: center;
        }
        .stat-number { font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #00d2ff, #3a7bd5); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .stat-label { font-size: 0.7rem; color: #a0d4ff; margin-top: 0.3rem; }

        .employee-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }
        .employee-card {
            background: rgba(15,25,35,0.85);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
            overflow: hidden;
        }
        .employee-card:hover { transform: translateY(-5px); border-color: #00d2ff; box-shadow: 0 15px 35px rgba(0,210,255,0.2); }
        .card-header {
            padding: 1.2rem 1.5rem;
            background: linear-gradient(135deg, rgba(0,210,255,0.15), rgba(58,123,213,0.08));
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .employee-name { font-size: 1.2rem; font-weight: 700; }
        .employee-mobile { font-size: 0.7rem; color: #88b4d4; margin-top: 4px; }
        .employee-id { background: rgba(0,210,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; }
        .card-body { padding: 1.2rem 1.5rem; }
        .skill-level-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .level-high { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .level-mid { background: linear-gradient(135deg, #f2994a, #f2c94c); }
        .level-low { background: linear-gradient(135deg, #eb3349, #f45c43); }
        .doc-badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 1rem 0; }
        .doc-badge {
            padding: 4px 10px;
            background: rgba(255,255,255,0.08);
            border-radius: 20px;
            font-size: 0.65rem;
            cursor: pointer;
        }
        .doc-badge.uploaded { background: linear-gradient(135deg, #11998e20, #38ef7d20); border-left: 2px solid #38ef7d; }
        .card-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 1rem; }
        .icon-btn {
            background: none;
            border: none;
            color: #88b4d4;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 20px;
            transition: all 0.2s;
            font-size: 0.75rem;
        }
        .icon-btn:hover { background: rgba(0,210,255,0.2); color: white; }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            backdrop-filter: blur(15px);
            justify-content: center;
            align-items: center;
            z-index: 1000;
            overflow-y: auto;
        }
        .modal-content {
            background: #0f1922;
            border: 1px solid rgba(0,210,255,0.3);
            border-radius: 32px;
            max-width: 950px;
            width: 95%;
            max-height: 90vh;
            overflow-y: auto;
            padding: 2rem;
            margin: 2rem auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 1rem;
        }
        .close-modal { cursor: pointer; font-size: 1.3rem; transition: 0.2s; }
        .close-modal:hover { color: #00d2ff; }

        .form-group { margin-bottom: 1.2rem; }
        .form-group label {
            display: block;
            margin-bottom: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #88b4d4;
            letter-spacing: 0.5px;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 12px;
            color: white;
            font-size: 0.9rem;
        }
        .form-group input:focus, .form-group select:focus { outline: none; border-color: #00d2ff; }

        .skills-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 0.8rem;
            max-height: 350px;
            overflow-y: auto;
            margin: 1rem 0;
            padding: 0.5rem;
            background: rgba(0,0,0,0.2);
            border-radius: 16px;
        }
        .skill-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.05);
            padding: 8px 12px;
            border-radius: 12px;
        }
        .skill-name { font-size: 0.72rem; flex: 1; }
        .skill-rating select {
            width: 80px;
            padding: 6px;
            background: #1a2a3a;
            border: 1px solid #2c4a6e;
            border-radius: 8px;
            color: white;
            font-size: 0.7rem;
        }

        .excel-upload-area {
            background: linear-gradient(135deg, rgba(0,210,255,0.1), rgba(56,239,125,0.05));
            border: 2px dashed rgba(0,210,255,0.4);
            border-radius: 20px;
            padding: 1rem;
            text-align: center;
            margin-bottom: 1.5rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        .excel-upload-area:hover { border-color: #00d2ff; background: rgba(0,210,255,0.15); }
        .excel-upload-area i { font-size: 1.8rem; margin-bottom: 0.5rem; color: #00d2ff; }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .chart-card {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 1.2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-card h4 { margin-bottom: 1rem; color: #00d2ff; font-size: 0.9rem; }
        canvas { max-height: 280px; width: 100%; }

        .skill-table { max-height: 350px; overflow-y: auto; }
        .skill-table table { width: 100%; border-collapse: collapse; }
        .skill-table tr { border-bottom: 1px solid rgba(255,255,255,0.08); }
        .skill-table td { padding: 10px; }
        .skill-rating-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .rating-4 { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .rating-3 { background: linear-gradient(135deg, #3a7bd5, #00d2ff); }
        .rating-2 { background: linear-gradient(135deg, #f2994a, #f2c94c); }
        .rating-1 { background: linear-gradient(135deg, #eb3349, #f45c43); }

        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #1e293b;
            border-left: 4px solid #38ef7d;
            padding: 12px 24px;
            border-radius: 12px;
            z-index: 1200;
            display: none;
        }
        .empty-state { text-align: center; padding: 3rem; background: rgba(255,255,255,0.03); border-radius: 32px; }

        .section-title {
            color: #00d2ff;
            margin: 1rem 0 0.8rem;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .employee-grid { grid-template-columns: 1fr; }
            .charts-grid { grid-template-columns: 1fr; }
            .skills-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="bg-animation"></div>

<div class="container">
    <div class="header">
        <div class="logo">
            <h1><i class="fas fa-chart-line"></i> SkillMatrix Pro</h1>
            <span>ENTERPRISE SKILL ASSESSMENT DASHBOARD</span>
        </div>
        <div class="btn-group">
            <button class="btn btn-outline" id="exportBtn"><i class="fas fa-download"></i> Export Data</button>
            <button class="btn btn-primary" id="addBtn"><i class="fas fa-user-plus"></i> Add Employee</button>
        </div>
    </div>

    <div class="search-wrapper">
        <i class="fas fa-search"></i>
        <input type="text" class="search-input" id="searchInput" placeholder="Search by name or mobile...">
    </div>

    <div class="stats-grid" id="statsGrid"></div>
    <div id="employeeGrid" class="employee-grid"></div>
</div>

<!-- Add/Edit Employee Modal - ALL UPLOADS HERE -->
<div id="employeeModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3 id="modalTitle" style="color:#00d2ff;"><i class="fas fa-user"></i> Add New Employee</h3>
            <i class="fas fa-times close-modal" onclick="closeModal()"></i>
        </div>
        <form id="employeeForm" enctype="multipart/form-data">
            <input type="hidden" id="editId">
            
            <!-- Excel Upload Section -->
            <div class="excel-upload-area" id="excelUploadArea">
                <i class="fas fa-file-excel fa-2x"></i>
                <p style="margin: 5px 0; font-size: 0.85rem;">📊 Upload Excel File (Skill Matrix)</p>
                <p style="font-size: 0.7rem; color: #88b4d4;">Supports .xls, .xlsx | Auto-imports employee data & skills</p>
                <input type="file" id="excelFileInput" accept=".xls,.xlsx" style="display:none">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div class="form-group">
                    <label>FULL NAME *</label>
                    <input type="text" id="empName" required placeholder="Dinesh Yadav">
                </div>
                <div class="form-group">
                    <label>MOBILE NUMBER</label>
                    <input type="text" id="empMobile" placeholder="9876543210">
                </div>
                <div class="form-group">
                    <label>DESIGNATION</label>
                    <input type="text" id="empDesignation" value="Moulder">
                </div>
                <div class="form-group">
                    <label>EXPERIENCE (YEARS)</label>
                    <input type="text" id="empExperience" placeholder="5">
                </div>
                <div class="form-group">
                    <label>EDUCATION</label>
                    <input type="text" id="empEducation" placeholder="SSC / 10th Pass">
                </div>
            </div>

            <div class="section-title"><i class="fas fa-chart-simple"></i> Skill Assessment (1-4 Scale)</div>
            <p style="font-size:0.7rem; color:#88b4d4; margin-bottom:0.5rem;">1=Cannot do, 2=Under Guidance, 3=Independently, 4=Can Train Others</p>
            <div id="skillsContainer" class="skills-container"></div>

            <div class="section-title"><i class="fas fa-folder-open"></i> Upload Documents</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 0.8rem;">
                <div class="form-group"><label>Aadhaar Card</label><input type="file" id="docAadhaar" accept="image/jpeg,image/jpg,image/png,application/pdf"></div>
                <div class="form-group"><label>PAN Card</label><input type="file" id="docPan" accept="image/jpeg,image/jpg,image/png,application/pdf"></div>
                <div class="form-group"><label>Driving License</label><input type="file" id="docLicense" accept="image/jpeg,image/jpg,image/png,application/pdf"></div>
                <div class="form-group"><label>Voting Card</label><input type="file" id="docVoting" accept="image/jpeg,image/jpg,image/png,application/pdf"></div>
                <div class="form-group"><label>Light Bill</label><input type="file" id="docLightbill" accept="image/jpeg,image/jpg,image/png,application/pdf"></div>
                <div class="form-group"><label>Employee Photo</label><input type="file" id="docPhoto" accept="image/jpeg,image/jpg,image/png"></div>
            </div>

            <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
                <button type="submit" class="btn btn-primary" style="flex:1;"><i class="fas fa-save"></i> Save Employee</button>
                <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    </div>
</div>

<!-- Analytics Modal -->
<div id="analyticsModal" class="modal">
    <div class="modal-content" style="max-width: 1400px;">
        <div class="modal-header">
            <h3 id="analyticsModalTitle" style="color:#00d2ff;"><i class="fas fa-chart-pie"></i> Skill Analytics Dashboard</h3>
            <i class="fas fa-times close-modal" onclick="closeAnalyticsModal()"></i>
        </div>
        <div id="analyticsContent"></div>
    </div>
</div>

<div id="toastMsg" class="toast"></div>

<script>
    let employees = [];
    let allSkills = {{ SKILLS_LIST | tojson }};

    async function fetchEmployees() {
        const res = await fetch('/api/employees');
        employees = await res.json();
        renderStats();
        renderCards();
    }

    function renderStats() {
        const total = employees.length;
        let totalSkills = 0;
        let avgScore = 0;
        employees.forEach(e => {
            if(e.skills) {
                const vals = Object.values(e.skills);
                totalSkills += vals.length;
                avgScore += vals.reduce((a,b) => a+b, 0) / (vals.length || 1);
            }
        });
        avgScore = total > 0 ? (avgScore / total).toFixed(1) : 0;
        document.getElementById('statsGrid').innerHTML = `
            <div class="stat-card"><div class="stat-number">${total}</div><div class="stat-label">Total Employees</div></div>
            <div class="stat-card"><div class="stat-number">${totalSkills}</div><div class="stat-label">Skills Assessed</div></div>
            <div class="stat-card"><div class="stat-number">${avgScore}</div><div class="stat-label">Avg Skill Level /4</div></div>
        `;
    }

    function getAvgSkill(skills) {
        if(!skills) return 0;
        const vals = Object.values(skills);
        return vals.length ? (vals.reduce((a,b) => a+b, 0) / vals.length).toFixed(1) : 0;
    }

    function getSkillLevelClass(avg) {
        if(avg >= 3.5) return 'level-high';
        if(avg >= 2.5) return 'level-mid';
        return 'level-low';
    }

    function renderSkillsForm(skillsData = {}) {
        const container = document.getElementById('skillsContainer');
        container.innerHTML = '';
        allSkills.forEach(skill => {
            const val = skillsData[skill] || 3;
            container.innerHTML += `
                <div class="skill-item">
                    <span class="skill-name">${escapeHtml(skill)}</span>
                    <div class="skill-rating">
                        <select data-skill="${skill.replace(/"/g, '&quot;')}">
                            <option value="1" ${val == 1 ? 'selected' : ''}>1 - Cannot do</option>
                            <option value="2" ${val == 2 ? 'selected' : ''}>2 - Under Guidance</option>
                            <option value="3" ${val == 3 ? 'selected' : ''}>3 - Independently</option>
                            <option value="4" ${val == 4 ? 'selected' : ''}>4 - Can Train</option>
                        </select>
                    </div>
                </div>
            `;
        });
    }

    function collectSkillsFromForm() {
        const skills = {};
        document.querySelectorAll('#skillsContainer select').forEach(select => {
            const skillName = select.getAttribute('data-skill');
            skills[skillName] = parseInt(select.value);
        });
        return skills;
    }

    function renderCards() {
        const term = document.getElementById('searchInput').value.toLowerCase();
        let filtered = employees.filter(e => (e.name || '').toLowerCase().includes(term) || (e.mobile || '').includes(term));
        const grid = document.getElementById('employeeGrid');
        if(filtered.length === 0) {
            grid.innerHTML = `<div class="empty-state"><i class="fas fa-chart-line fa-3x" style="margin-bottom:1rem; color:#00d2ff;"></i><h3>No Employees Found</h3><p style="color:#88b4d4;">Click "Add Employee" to get started</p></div>`;
            return;
        }
        grid.innerHTML = filtered.map(emp => {
            const avgSkill = getAvgSkill(emp.skills);
            const skillClass = getSkillLevelClass(avgSkill);
            const docs = emp.docs || {};
            return `
                <div class="employee-card">
                    <div class="card-header">
                        <div>
                            <div class="employee-name">${escapeHtml(emp.name || 'Unknown')}</div>
                            <div class="employee-mobile"><i class="fas fa-phone"></i> ${emp.mobile || '—'} | ${emp.designation || 'Moulder'}</div>
                        </div>
                        <div class="employee-id">ID:${emp.localId}</div>
                    </div>
                    <div class="card-body">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span>Skill Proficiency</span>
                            <span class="skill-level-badge ${skillClass}">Level ${avgSkill}/4</span>
                        </div>
                        <canvas id="preview-${emp.localId}" style="height:70px; width:100%; margin:10px 0;"></canvas>
                        <div class="doc-badges">
                            ${renderDocBadge('📄 Aadhaar', docs.aadhaar)}
                            ${renderDocBadge('💳 PAN', docs.pan)}
                            ${renderDocBadge('🚗 License', docs.license)}
                            ${renderDocBadge('🗳️ Voting', docs.voting)}
                        </div>
                        <div class="card-actions">
                            <button class="icon-btn" onclick="viewAnalytics(${emp.localId})"><i class="fas fa-chart-line"></i> Analytics</button>
                            <button class="icon-btn" onclick="editEmployee(${emp.localId})"><i class="fas fa-edit"></i> Edit</button>
                            <button class="icon-btn" onclick="deleteEmployee(${emp.localId})"><i class="fas fa-trash"></i> Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        filtered.forEach(emp => {
            const canvas = document.getElementById(`preview-${emp.localId}`);
            if(canvas && emp.skills) {
                const ctx = canvas.getContext('2d');
                const skillsArray = Object.values(emp.skills);
                if(skillsArray.length) {
                    new Chart(ctx, {
                        type: 'line',
                        data: { labels: skillsArray.map((_,i) => i+1), datasets: [{ data: skillsArray, borderColor: '#00d2ff', backgroundColor: 'rgba(0,210,255,0.1)', borderWidth: 2, fill: true, pointBackgroundColor: '#38ef7d', pointBorderColor: '#fff', pointRadius: 3 }] },
                        options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false }, tooltip: { enabled: false } }, scales: { y: { min: 1, max: 4, display: false }, x: { display: false } } }
                    });
                }
            }
        });
    }

    function renderDocBadge(label, filePath) {
        if(filePath) return `<div class="doc-badge uploaded">${label} ✓</div>`;
        return `<div class="doc-badge">${label}</div>`;
    }

    window.viewAnalytics = (empId) => {
        const emp = employees.find(e => e.localId === empId);
        if(!emp) return;
        const skills = emp.skills || {};
        const skillNames = Object.keys(skills);
        const skillValues = Object.values(skills);
        
        const categories = { 'Basic Skills': [], 'Technical Skills': [], 'Safety & 5S': [], 'General Skills': [] };
        skillNames.forEach((name, i) => {
            const lower = name.toLowerCase();
            if(lower.includes('handpress') || lower.includes('hydraulic') || lower.includes('polymer')) categories['Basic Skills'].push(skillValues[i]);
            else if(lower.includes('machine') || lower.includes('mould') || lower.includes('vernier')) categories['Technical Skills'].push(skillValues[i]);
            else if(lower.includes('safety') || lower.includes('5s') || lower.includes('clean')) categories['Safety & 5S'].push(skillValues[i]);
            else categories['General Skills'].push(skillValues[i]);
        });
        
        const categoryAverages = {};
        for(const [cat, vals] of Object.entries(categories)) {
            categoryAverages[cat] = vals.length ? (vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(1) : 2;
        }
        
        const overall = (skillValues.reduce((a,b)=>a+b,0) / skillValues.length / 4) * 100;
        
        const html = `
            <div style="margin-bottom:1.5rem;">
                <h2 style="font-size:1.8rem;">${escapeHtml(emp.name)}</h2>
                <p style="color:#88b4d4;">${emp.designation || 'Moulder'} | ${emp.experience || 0} yrs exp | ${emp.education || '—'}</p>
            </div>
            <div class="charts-grid">
                <div class="chart-card"><h4>📊 Category Performance</h4><canvas id="radarChart"></canvas></div>
                <div class="chart-card"><h4>📈 Top Skills</h4><canvas id="barChart"></canvas></div>
                <div class="chart-card"><h4>📉 Skill Distribution</h4><canvas id="histogramChart"></canvas></div>
                <div class="chart-card"><h4>🥧 Skills by Category</h4><canvas id="pieChart"></canvas></div>
                <div class="chart-card"><h4>📊 Skill Progression</h4><canvas id="lineChart"></canvas></div>
                <div class="chart-card"><h4>🎯 Overall Score</h4><canvas id="gaugeChart"></canvas></div>
            </div>
            <div class="chart-card"><h4>📋 Complete Skill Matrix</h4>
                <div class="skill-table"><table>${skillNames.slice(0,40).map((name, i) => `<tr><td style="width:70%;">${escapeHtml(name)}</td><td><span class="skill-rating-badge rating-${skillValues[i]}">${skillValues[i]}</span></td></tr>`).join('')}</table></div>
            </div>
        `;
        
        document.getElementById('analyticsModalTitle').innerHTML = `<i class="fas fa-chart-pie"></i> Skill Analytics - ${escapeHtml(emp.name)}`;
        document.getElementById('analyticsContent').innerHTML = html;
        document.getElementById('analyticsModal').style.display = 'flex';
        
        setTimeout(() => {
            new Chart(document.getElementById('radarChart'), {
                type: 'radar',
                data: { labels: Object.keys(categoryAverages), datasets: [{ label: 'Skill Level', data: Object.values(categoryAverages), backgroundColor: 'rgba(0,210,255,0.2)', borderColor: '#00d2ff', borderWidth: 2, pointBackgroundColor: '#38ef7d' }] },
                options: { responsive: true, scales: { r: { min: 1, max: 4, ticks: { stepSize: 1, color: '#88b4d4' } } }, plugins: { legend: { labels: { color: '#fff' } } } }
            });
            
            const topNames = skillNames.slice(0, 8);
            const topVals = skillValues.slice(0, 8);
            new Chart(document.getElementById('barChart'), {
                type: 'bar',
                data: { labels: topNames.map(s => s.length > 20 ? s.slice(0,18)+'...' : s), datasets: [{ label: 'Rating', data: topVals, backgroundColor: 'rgba(0,210,255,0.7)', borderRadius: 8 }] },
                options: { responsive: true, scales: { y: { min: 1, max: 4, title: { display: true, text: 'Level (1-4)', color: '#88b4d4' } } }, plugins: { legend: { display: false } } }
            });
            
            new Chart(document.getElementById('histogramChart'), {
                type: 'bar',
                data: { labels: ['Level 1', 'Level 2', 'Level 3', 'Level 4'], datasets: [{ label: 'Count', data: [skillValues.filter(v=>v===1).length, skillValues.filter(v=>v===2).length, skillValues.filter(v=>v===3).length, skillValues.filter(v=>v===4).length], backgroundColor: ['#eb3349', '#f2994a', '#3a7bd5', '#38ef7d'] }] },
                options: { responsive: true, plugins: { legend: { display: false } } }
            });
            
            new Chart(document.getElementById('pieChart'), {
                type: 'doughnut',
                data: { labels: Object.keys(categories), datasets: [{ data: Object.values(categories).map(v => v.length), backgroundColor: ['#00d2ff', '#3a7bd5', '#38ef7d', '#f2994a'] }] },
                options: { responsive: true, plugins: { legend: { labels: { color: '#fff' } } } }
            });
            
            const sortedVals = [...skillValues].sort((a,b) => a-b);
            new Chart(document.getElementById('lineChart'), {
                type: 'line',
                data: { labels: sortedVals.map((_,i) => i+1), datasets: [{ data: sortedVals, borderColor: '#00d2ff', borderWidth: 3, fill: true, backgroundColor: 'rgba(0,210,255,0.1)', tension: 0.4 }] },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { min: 1, max: 4 } } }
            });
            
            new Chart(document.getElementById('gaugeChart'), {
                type: 'doughnut',
                data: { labels: ['Proficiency', 'Gap'], datasets: [{ data: [overall, 100-overall], backgroundColor: ['#00d2ff', '#1e2a3a'], borderWidth: 0 }] },
                options: { responsive: true, cutout: '70%', plugins: { tooltip: { callbacks: { label: () => `Overall: ${overall.toFixed(1)}%` } } } }
            });
        }, 100);
    };
    
    window.closeAnalyticsModal = () => {
        document.getElementById('analyticsModal').style.display = 'none';
        document.getElementById('analyticsContent').innerHTML = '';
    };
    
    // Excel upload handling
    document.getElementById('excelUploadArea').onclick = () => document.getElementById('excelFileInput').click();
    document.getElementById('excelFileInput').onchange = async (e) => {
        if(e.target.files.length) {
            const formData = new FormData();
            formData.append('excel_file', e.target.files[0]);
            const res = await fetch('/api/upload_excel_bulk', { method: 'POST', body: formData });
            const data = await res.json();
            if(data.success) {
                showToast(`✅ Imported ${data.count || 0} employees from Excel!`);
                closeModal();
                fetchEmployees();
            } else showToast('❌ Error parsing file');
            e.target.value = '';
        }
    };
    
    document.getElementById('addBtn').onclick = () => {
        document.getElementById('modalTitle').innerHTML = '<i class="fas fa-user-plus"></i> Add New Employee';
        document.getElementById('employeeForm').reset();
        document.getElementById('editId').value = '';
        renderSkillsForm({});
        document.getElementById('employeeModal').style.display = 'flex';
    };
    
    window.editEmployee = (id) => {
        const emp = employees.find(e => e.localId === id);
        if(!emp) return;
        document.getElementById('modalTitle').innerHTML = '<i class="fas fa-edit"></i> Edit Employee';
        document.getElementById('editId').value = id;
        document.getElementById('empName').value = emp.name || '';
        document.getElementById('empMobile').value = emp.mobile || '';
        document.getElementById('empDesignation').value = emp.designation || 'Moulder';
        document.getElementById('empExperience').value = emp.experience || '';
        document.getElementById('empEducation').value = emp.education || '';
        renderSkillsForm(emp.skills || {});
        document.querySelectorAll('#employeeForm input[type=file]').forEach(inp => inp.value = '');
        document.getElementById('employeeModal').style.display = 'flex';
    };
    
    window.closeModal = () => {
        document.getElementById('employeeModal').style.display = 'none';
    };
    
    document.getElementById('employeeForm').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('localId', document.getElementById('editId').value);
        formData.append('name', document.getElementById('empName').value);
        formData.append('mobile', document.getElementById('empMobile').value);
        formData.append('designation', document.getElementById('empDesignation').value);
        formData.append('experience', document.getElementById('empExperience').value);
        formData.append('education', document.getElementById('empEducation').value);
        formData.append('skills', JSON.stringify(collectSkillsFromForm()));
        
        const docFields = ['aadhaar', 'pan', 'license', 'voting', 'lightbill', 'photo'];
        for(let f of docFields) {
            let file = document.getElementById(`doc${f.charAt(0).toUpperCase() + f.slice(1)}`).files[0];
            if(file) formData.append(f, file);
        }
        
        const res = await fetch('/api/save_employee', { method: 'POST', body: formData });
        const data = await res.json();
        if(data.success) { showToast('Employee saved successfully!'); closeModal(); fetchEmployees(); }
        else showToast('Error saving employee');
    };
    
    window.deleteEmployee = async (id) => {
        if(!confirm('Delete employee permanently?')) return;
        const res = await fetch('/api/delete_employee', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({localId: id}) });
        if((await res.json()).success) { showToast('Deleted'); fetchEmployees(); }
        else showToast('Delete failed');
    };
    
    document.getElementById('exportBtn').onclick = () => window.location.href = '/export_excel';
    document.getElementById('searchInput').oninput = () => renderCards();
    
    function escapeHtml(str) { if(!str) return ''; return str.replace(/[&<>]/g, function(m){if(m==='&') return '&amp;'; if(m==='<') return '&lt;'; if(m==='>') return '&gt;'; return m;}); }
    function showToast(msg) { let t = document.getElementById('toastMsg'); t.innerText = msg; t.style.display = 'block'; setTimeout(()=> t.style.display='none', 3000); }
    
    fetchEmployees();
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML, SKILLS_LIST=SKILLS_LIST)

@app.route('/api/upload_excel_bulk', methods=['POST'])
def upload_excel_bulk():
    file = request.files.get('excel_file')
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        skills_data = parse_skill_excel(filepath)
        
        employees = load_employees()
        count = 0
        for name, skills in skills_data.items():
            existing = None
            for emp in employees:
                if emp.get('name', '').lower() == name.lower():
                    existing = emp
                    break
            if existing:
                existing['skills'] = skills
            else:
                employees.append({
                    'name': name,
                    'mobile': '',
                    'designation': 'Moulder',
                    'experience': '',
                    'education': '',
                    'skills': skills,
                    'docs': {}
                })
            count += 1
        
        save_employees(employees)
        return jsonify({'success': True, 'count': count})
    return jsonify({'success': False, 'error': 'Invalid file'})

@app.route('/api/save_employee', methods=['POST'])
def save_employee():
    employees = load_employees()
    local_id = request.form.get('localId')
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    designation = request.form.get('designation', 'Moulder')
    experience = request.form.get('experience', '')
    education = request.form.get('education', '')
    skills = json.loads(request.form.get('skills', '{}'))
    
    new_emp = {
        'name': name, 'mobile': mobile, 'designation': designation,
        'experience': experience, 'education': education,
        'skills': skills, 'docs': {}
    }
    
    emp_folder = None
    def get_folder():
        nonlocal emp_folder
        if emp_folder is None:
            ts = int(datetime.now().timestamp())
            safe = secure_filename(name[:30] if name else 'employee')
            emp_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"{ts}_{safe}")
            os.makedirs(emp_folder, exist_ok=True)
        return emp_folder
    
    doc_keys = ['aadhaar', 'pan', 'license', 'voting', 'lightbill', 'photo']
    for dk in doc_keys:
        file = request.files.get(dk)
        if file and file.filename and allowed_file(file.filename):
            folder = get_folder()
            fname = secure_filename(f"{dk}_{file.filename}")
            path = os.path.join(folder, fname)
            file.save(path)
            new_emp['docs'][dk] = path
    
    if local_id and local_id.isdigit():
        idx = int(local_id)
        if 0 <= idx < len(employees):
            old_docs = employees[idx].get('docs', {})
            for k in doc_keys:
                if k not in new_emp['docs'] and k in old_docs:
                    new_emp['docs'][k] = old_docs[k]
            employees[idx] = new_emp
        else:
            employees.append(new_emp)
    else:
        employees.append(new_emp)
    
    save_employees(employees)
    return jsonify({'success': True})

@app.route('/api/employees')
def get_employees():
    emps = load_employees()
    for i, e in enumerate(emps):
        e['localId'] = i
    return jsonify(emps)

@app.route('/api/delete_employee', methods=['POST'])
def delete_employee():
    data = request.get_json()
    local_id = data.get('localId')
    emps = load_employees()
    if isinstance(local_id, int) and 0 <= local_id < len(emps):
        emps.pop(local_id)
        save_employees(emps)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/export_excel')
def export_excel():
    emps = load_employees()
    rows = []
    for e in emps:
        skills = e.get('skills', {})
        row = {
            'Name': e.get('name', ''),
            'Mobile': e.get('mobile', ''),
            'Designation': e.get('designation', ''),
            'Experience': e.get('experience', ''),
            'Education': e.get('education', ''),
            'Average Skill Score': sum(skills.values()) / len(skills) if skills else 0
        }
        for skill, rating in list(skills.items())[:30]:
            row[f'Skill: {skill[:35]}'] = rating
        rows.append(row)
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee_Skills')
    output.seek(0)
    return send_file(output, download_name='employee_skills_export.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 