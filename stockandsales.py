# app.py - Complete Stock Analysis Web Application
# Run: python app.py

from flask import Flask, render_template_string, request, jsonify, send_file, session
from flask_cors import CORS
import pandas as pd
import re
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = 'stock_analysis_secret_key_2024'
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_code(text):
    if pd.isna(text):
        return None
    text_str = str(text).strip()
    match = re.match(r"^(\d{4,6})", text_str)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{4,6})\b", text_str)
    if match:
        return match.group(1)
    match = re.search(r"(\d+)", text_str)
    if match:
        return match.group(1)
    return None

def categorize_department(op_name):
    if pd.isna(op_name):
        return "Other"
    op_name_str = str(op_name).upper()
    if "PACKING" in op_name_str:
        return "PACKING"
    elif "MOULDING" in op_name_str or "MOLDING" in op_name_str:
        return "MOULDING"
    elif "FINISHING" in op_name_str:
        return "FINISHING"
    elif "FINAL INSPECTION" in op_name_str:
        return "FINAL INSPECTION"
    elif "BORING" in op_name_str:
        return "BORING"
    elif "INWARD" in op_name_str:
        return "INWARD"
    elif "PHOSPHATING" in op_name_str:
        return "PHOSPHATING"
    elif "CHEMLOK" in op_name_str or "CA_" in op_name_str:
        return "CHEMLOK"
    elif "EXTRUSION" in op_name_str:
        return "EXTRUSION"
    elif "PLATING" in op_name_str:
        return "PLATING"
    else:
        return "WIP"

def process_files(sales_file_path, stock_file_path):
    """Process both files and return analysis results"""
    
    # Read sales file
    sales_df = pd.read_excel(sales_file_path, engine="xlrd")
    sales_df.columns = [str(col).strip() for col in sales_df.columns]
    sales_df["Item_Code"] = sales_df["ItemDesc"].apply(extract_code)
    sales_df = sales_df[sales_df["Item_Code"].notna()].copy()
    
    # Find header row in stock file
    raw_stock = pd.read_excel(stock_file_path, engine="xlrd", header=None)
    header_row = None
    for i in range(len(raw_stock)):
        row_values = (raw_stock.iloc[i].fillna("").astype(str).str.strip().str.lower().tolist())
        if "itemdesc" in row_values:
            header_row = i
            break
    
    if header_row is None:
        raise Exception("Could not find header row containing 'ItemDesc'")
    
    # Read stock file
    stock_df = pd.read_excel(stock_file_path, engine="xlrd", header=header_row)
    stock_df.columns = [str(col).strip() for col in stock_df.columns]
    
    # Find columns
    stock_item_col = None
    for col in stock_df.columns:
        if "itemdesc" in col.lower():
            stock_item_col = col
            break
    
    closing_col = None
    for col in stock_df.columns:
        if "closing" in col.lower() and "stock" in col.lower():
            closing_col = col
            break
    
    dept_col = None
    for col in stock_df.columns:
        if "opname" in col.lower():
            dept_col = col
            break
    
    if stock_item_col is None or closing_col is None:
        raise Exception("Required columns not found in stock file")
    
    # Process stock data
    stock_df["Item_Code"] = stock_df[stock_item_col].apply(extract_code)
    stock_df = stock_df[stock_df["Item_Code"].notna()].copy()
    stock_df[closing_col] = pd.to_numeric(stock_df[closing_col], errors="coerce").fillna(0)
    
    # Add department
    if dept_col:
        stock_df["Department"] = stock_df[dept_col].apply(categorize_department)
    else:
        stock_df["Department"] = "STORE"
    
    # Create department-wise summary
    dept_summary = stock_df.pivot_table(
        index="Item_Code",
        columns="Department",
        values=closing_col,
        aggfunc="sum",
        fill_value=0
    )
    total_stock = stock_df.groupby("Item_Code")[closing_col].sum().rename("Total_Closing_Stock")
    dept_summary = dept_summary.join(total_stock)
    dept_summary.reset_index(inplace=True)
    
    # Merge
    sales_df["Item_Code"] = sales_df["Item_Code"].astype(str)
    dept_summary["Item_Code"] = dept_summary["Item_Code"].astype(str)
    final_df = sales_df.merge(dept_summary, on="Item_Code", how="left")
    
    # Fill missing values
    stock_cols = [col for col in dept_summary.columns if col != "Item_Code"]
    for col in stock_cols:
        if col in final_df.columns:
            final_df[col] = final_df[col].fillna(0)
        else:
            final_df[col] = 0
    
    # Calculations
    final_df["Bal_Qty"] = pd.to_numeric(final_df["Bal_Qty"], errors="coerce").fillna(0)
    final_df["InvoiceQty"] = pd.to_numeric(final_df["InvoiceQty"], errors="coerce").fillna(0)
    final_df["SO_Qty"] = pd.to_numeric(final_df["SO_Qty"], errors="coerce").fillna(0)
    final_df["Pending_Qty"] = abs(final_df["Bal_Qty"])
    final_df["Shortage"] = final_df.apply(lambda row: max(0, row["Pending_Qty"] - row["Total_Closing_Stock"]), axis=1)
    final_df["Excess_Stock"] = final_df.apply(lambda row: max(0, row["Total_Closing_Stock"] - row["Pending_Qty"]), axis=1)
    
    def get_status(row):
        if row["Total_Closing_Stock"] >= row["Pending_Qty"]:
            return "SUFFICIENT"
        elif row["Total_Closing_Stock"] > 0:
            return "PARTIAL"
        else:
            return "NO STOCK"
    
    final_df["Stock_Status"] = final_df.apply(get_status, axis=1)
    final_df["Fulfillment_%"] = final_df.apply(
        lambda row: min(100, (row["Total_Closing_Stock"] / row["Pending_Qty"] * 100)) if row["Pending_Qty"] > 0 else 100,
        axis=1
    )
    
    # Prepare results
    results = []
    for _, row in final_df.iterrows():
        departments = {}
        for col in stock_cols:
            if col != "Total_Closing_Stock" and row[col] > 0:
                departments[col] = float(row[col])
        
        results.append({
            'item_no': str(row['Item_Code']),
            'customer': str(row.get('CustName', 'Unknown')),
            'city': str(row.get('City', 'Unknown')),
            'so_no': str(row.get('SO_No', 'Unknown')),
            'sales_desc': str(row['ItemDesc'])[:150],
            'so_qty': float(row['SO_Qty']),
            'invoiced_qty': float(row['InvoiceQty']),
            'balance_qty': float(row['Bal_Qty']),
            'pending_qty': float(row['Pending_Qty']),
            'total_stock': float(row['Total_Closing_Stock']),
            'shortage': float(row['Shortage']),
            'excess': float(row['Excess_Stock']),
            'fulfillment': float(row['Fulfillment_%']),
            'status': row['Stock_Status'],
            'departments': departments
        })
    
    # Sort by pending quantity
    results.sort(key=lambda x: x['pending_qty'], reverse=True)
    
    # Statistics
    stats = {
        'total_items': len(results),
        'total_pending': sum(r['pending_qty'] for r in results),
        'total_stock': sum(r['total_stock'] for r in results),
        'total_shortage': sum(r['shortage'] for r in results),
        'sufficient_count': len([r for r in results if r['status'] == 'SUFFICIENT']),
        'partial_count': len([r for r in results if r['status'] == 'PARTIAL']),
        'no_stock_count': len([r for r in results if r['status'] == 'NO STOCK'])
    }
    
    return results, stats

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Analysis System | Puja Fluid Seals</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            background: white;
            border-radius: 20px;
            padding: 20px 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .logo h1 {
            font-size: 24px;
            color: #1a1a2e;
        }

        .logo h1 i {
            color: #667eea;
            margin-right: 10px;
        }

        .logo p {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }

        .date-time {
            text-align: right;
            color: #666;
            font-size: 12px;
        }

        /* Upload Section */
        .upload-section {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .upload-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1a1a2e;
        }

        .upload-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 25px;
        }

        .upload-card {
            border: 2px dashed #e0e0e0;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }

        .upload-card:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }

        .upload-card.dragover {
            border-color: #667eea;
            background: #f0f2ff;
        }

        .upload-card i {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 15px;
        }

        .upload-card h3 {
            font-size: 16px;
            margin-bottom: 8px;
        }

        .upload-card p {
            color: #999;
            font-size: 12px;
        }

        .file-name {
            font-size: 12px;
            color: #667eea;
            margin-top: 10px;
            word-break: break-all;
        }

        .upload-status {
            font-size: 12px;
            margin-top: 10px;
        }

        .upload-status.success {
            color: #10b981;
        }

        .upload-status.error {
            color: #ef4444;
        }

        .btn-analyze {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 40px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .btn-analyze:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .btn-analyze:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card .icon {
            font-size: 32px;
            margin-bottom: 10px;
        }

        .stat-card .label {
            font-size: 13px;
            color: #666;
            margin-bottom: 5px;
        }

        .stat-card .value {
            font-size: 28px;
            font-weight: 700;
            color: #1a1a2e;
        }

        .stat-card.sufficient .icon { color: #10b981; }
        .stat-card.partial .icon { color: #f59e0b; }
        .stat-card.nostock .icon { color: #ef4444; }

        /* Charts Section */
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        .chart-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .chart-card h3 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #1a1a2e;
        }

        canvas {
            max-height: 250px;
        }

        /* Results Section */
        .results-section {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: none;
        }

        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .results-header h2 {
            font-size: 18px;
        }

        .btn-export {
            background: #10b981;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.2s;
        }

        .btn-export:hover {
            background: #059669;
        }

        .search-box {
            padding: 10px 15px;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            width: 250px;
            font-size: 14px;
        }

        .filter-select {
            padding: 10px 15px;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }

        .table-wrapper {
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
            border-radius: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #1a1a2e;
            position: sticky;
            top: 0;
            cursor: pointer;
            z-index: 10;
        }

        th:hover {
            background: #e8e9ea;
        }

        tr:hover {
            background: #f8f9ff;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }

        .status-sufficient {
            background: #d1fae5;
            color: #065f46;
        }

        .status-partial {
            background: #fed7aa;
            color: #92400e;
        }

        .status-nostock {
            background: #fee2e2;
            color: #991b1b;
        }

        .progress-bar {
            width: 80px;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: #10b981;
            border-radius: 3px;
            transition: width 0.3s;
        }

        .expand-btn {
            background: none;
            border: none;
            cursor: pointer;
            color: #667eea;
            font-size: 14px;
        }

        .detail-row {
            display: none;
            background: #f9fafb;
        }

        .detail-row.show {
            display: table-row;
        }

        .detail-cell {
            padding: 15px 20px;
        }

        .dept-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .dept-tag {
            background: #e0e7ff;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            color: #3730a3;
        }

        .loading {
            text-align: center;
            padding: 40px;
        }

        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: white;
            font-size: 12px;
        }

        @media (max-width: 768px) {
            .upload-grid, .charts-section {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 15px;
            }
            th, td {
                padding: 8px 10px;
                font-size: 12px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <h1><i class="fas fa-chart-line"></i> Stock Analysis System</h1>
                <p>Puja Fluid Seals Pvt. Ltd.</p>
            </div>
            <div class="date-time" id="datetime"></div>
        </div>

        <div class="upload-section">
            <div class="upload-title">
                <i class="fas fa-cloud-upload-alt"></i> Upload Files
            </div>
            <div class="upload-grid">
                <div class="upload-card" id="salesUploadCard">
                    <i class="fas fa-file-invoice"></i>
                    <h3>Sales Order Book Balance</h3>
                    <p>Upload .xls, .xlsx, or .csv file</p>
                    <input type="file" id="salesFile" accept=".xls,.xlsx,.csv" style="display: none;">
                    <div id="salesFileName" class="file-name"></div>
                    <div id="salesStatus" class="upload-status"></div>
                </div>

                <div class="upload-card" id="stockUploadCard">
                    <i class="fas fa-warehouse"></i>
                    <h3>Stock FG + SFG Report</h3>
                    <p>Upload .xls, .xlsx, or .csv file</p>
                    <input type="file" id="stockFile" accept=".xls,.xlsx,.csv" style="display: none;">
                    <div id="stockFileName" class="file-name"></div>
                    <div id="stockStatus" class="upload-status"></div>
                </div>
            </div>

            <button class="btn-analyze" id="analyzeBtn" disabled>
                <i class="fas fa-search"></i> Analyze Stock Availability
            </button>
        </div>

        <div class="stats-grid" id="statsGrid" style="display: none;"></div>

        <div class="charts-section" id="chartsSection" style="display: none;">
            <div class="chart-card">
                <h3><i class="fas fa-chart-pie"></i> Stock Status Distribution</h3>
                <canvas id="statusChart"></canvas>
            </div>
            <div class="chart-card">
                <h3><i class="fas fa-chart-bar"></i> Quantity Overview</h3>
                <canvas id="quantityChart"></canvas>
            </div>
        </div>

        <div class="results-section" id="resultsSection">
            <div class="results-header">
                <h2><i class="fas fa-list"></i> Analysis Results</h2>
                <div>
                    <input type="text" id="searchInput" class="search-box" placeholder="Search by item, customer...">
                    <select id="statusFilter" class="filter-select">
                        <option value="all">All Status</option>
                        <option value="SUFFICIENT">Sufficient Stock</option>
                        <option value="PARTIAL">Partial Stock</option>
                        <option value="NO STOCK">No Stock</option>
                    </select>
                    <button class="btn-export" id="exportBtn"><i class="fas fa-download"></i> Export Excel</button>
                </div>
            </div>
            <div class="table-wrapper">
                <table id="resultsTable">
                    <thead>
                        <tr>
                            <th>Item No</th>
                            <th>Customer</th>
                            <th>SO No</th>
                            <th>Description</th>
                            <th>Pending</th>
                            <th>Stock</th>
                            <th>Shortage</th>
                            <th>Fulfillment</th>
                            <th>Status</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody id="resultsBody"></tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Puja Fluid Seals Pvt. Ltd. - Stock Analysis System</p>
        </div>
    </div>

    <script>
        let salesFile = null;
        let stockFile = null;
        let analysisData = null;
        let statusChart = null;
        let quantityChart = null;

        // Update date/time
        function updateDateTime() {
            const now = new Date();
            document.getElementById('datetime').innerHTML = now.toLocaleString();
        }
        setInterval(updateDateTime, 1000);
        updateDateTime();

        // File upload handlers
        document.getElementById('salesUploadCard').addEventListener('click', () => {
            document.getElementById('salesFile').click();
        });

        document.getElementById('stockUploadCard').addEventListener('click', () => {
            document.getElementById('stockFile').click();
        });

        document.getElementById('salesFile').addEventListener('change', (e) => {
            salesFile = e.target.files[0];
            const fileNameSpan = document.getElementById('salesFileName');
            const statusSpan = document.getElementById('salesStatus');
            if (salesFile) {
                fileNameSpan.innerHTML = `<i class="fas fa-check-circle"></i> ${salesFile.name}`;
                statusSpan.innerHTML = '<span class="success">File selected</span>';
            } else {
                fileNameSpan.innerHTML = '';
                statusSpan.innerHTML = '';
            }
            checkFiles();
        });

        document.getElementById('stockFile').addEventListener('change', (e) => {
            stockFile = e.target.files[0];
            const fileNameSpan = document.getElementById('stockFileName');
            const statusSpan = document.getElementById('stockStatus');
            if (stockFile) {
                fileNameSpan.innerHTML = `<i class="fas fa-check-circle"></i> ${stockFile.name}`;
                statusSpan.innerHTML = '<span class="success">File selected</span>';
            } else {
                fileNameSpan.innerHTML = '';
                statusSpan.innerHTML = '';
            }
            checkFiles();
        });

        // Drag and drop
        function setupDragDrop(cardId, inputId) {
            const card = document.getElementById(cardId);
            card.addEventListener('dragover', (e) => {
                e.preventDefault();
                card.classList.add('dragover');
            });
            card.addEventListener('dragleave', () => {
                card.classList.remove('dragover');
            });
            card.addEventListener('drop', (e) => {
                e.preventDefault();
                card.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const input = document.getElementById(inputId);
                    const dt = new DataTransfer();
                    dt.items.add(files[0]);
                    input.files = dt.files;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }

        setupDragDrop('salesUploadCard', 'salesFile');
        setupDragDrop('stockUploadCard', 'stockFile');

        function checkFiles() {
            const analyzeBtn = document.getElementById('analyzeBtn');
            analyzeBtn.disabled = !(salesFile && stockFile);
        }

        document.getElementById('analyzeBtn').addEventListener('click', async () => {
            if (!salesFile || !stockFile) return;

            const analyzeBtn = document.getElementById('analyzeBtn');
            const originalText = analyzeBtn.innerHTML;
            analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> Analyzing...';
            analyzeBtn.disabled = true;

            const formData = new FormData();
            formData.append('sales_file', salesFile);
            formData.append('stock_file', stockFile);

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    analysisData = data;
                    displayStats(data.stats);
                    displayCharts(data);
                    displayResults(data.results);
                    document.getElementById('resultsSection').style.display = 'block';
                    document.getElementById('chartsSection').style.display = 'grid';
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                analyzeBtn.innerHTML = originalText;
                analyzeBtn.disabled = false;
            }
        });

        function displayStats(stats) {
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-boxes"></i></div>
                    <div class="label">Items Analyzed</div>
                    <div class="value">${stats.total_items}</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-clipboard-list"></i></div>
                    <div class="label">Pending Orders</div>
                    <div class="value">${stats.total_pending.toLocaleString()}</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-warehouse"></i></div>
                    <div class="label">Stock Available</div>
                    <div class="value">${stats.total_stock.toLocaleString()}</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-exclamation-triangle"></i></div>
                    <div class="label">Shortage</div>
                    <div class="value">${stats.total_shortage.toLocaleString()}</div>
                </div>
                <div class="stat-card sufficient">
                    <div class="icon"><i class="fas fa-check-circle"></i></div>
                    <div class="label">Sufficient Stock</div>
                    <div class="value">${stats.sufficient_count}</div>
                </div>
                <div class="stat-card partial">
                    <div class="icon"><i class="fas fa-chart-line"></i></div>
                    <div class="label">Partial Stock</div>
                    <div class="value">${stats.partial_count}</div>
                </div>
                <div class="stat-card nostock">
                    <div class="icon"><i class="fas fa-times-circle"></i></div>
                    <div class="label">No Stock</div>
                    <div class="value">${stats.no_stock_count}</div>
                </div>
            `;
            statsGrid.style.display = 'grid';
        }

        function displayCharts(data) {
            // Status Distribution Chart
            const ctx1 = document.getElementById('statusChart').getContext('2d');
            if (statusChart) statusChart.destroy();
            statusChart = new Chart(ctx1, {
                type: 'doughnut',
                data: {
                    labels: ['Sufficient Stock', 'Partial Stock', 'No Stock'],
                    datasets: [{
                        data: [data.stats.sufficient_count, data.stats.partial_count, data.stats.no_stock_count],
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });

            // Quantity Overview Chart
            const ctx2 = document.getElementById('quantityChart').getContext('2d');
            if (quantityChart) quantityChart.destroy();
            quantityChart = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: ['Pending Orders', 'Stock Available', 'Shortage'],
                    datasets: [{
                        label: 'Quantity',
                        data: [data.stats.total_pending, data.stats.total_stock, data.stats.total_shortage],
                        backgroundColor: ['#667eea', '#10b981', '#ef4444'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        function displayResults(results) {
            const tbody = document.getElementById('resultsBody');
            tbody.innerHTML = '';

            if (!results || results.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 40px;">No matching items found</td></tr>';
                return;
            }

            results.forEach((item, index) => {
                const row = tbody.insertRow();
                const statusClass = item.status === 'SUFFICIENT' ? 'status-sufficient' : (item.status === 'PARTIAL' ? 'status-partial' : 'status-nostock');
                const fulfillmentColor = item.fulfillment >= 100 ? '#10b981' : (item.fulfillment >= 50 ? '#f59e0b' : '#ef4444');
                
                row.innerHTML = `
                    <td><strong>${escapeHtml(item.item_no)}</strong></td>
                    <td>${escapeHtml(item.customer)}</td>
                    <td>${item.so_no}</td>
                    <td title="${escapeHtml(item.sales_desc)}">${escapeHtml(item.sales_desc.substring(0, 50))}${item.sales_desc.length > 50 ? '...' : ''}</td>
                    <td>${item.pending_qty.toLocaleString()}</td>
                    <td>${item.total_stock.toLocaleString()}</td>
                    <td style="color: ${item.shortage > 0 ? '#ef4444' : '#10b981'}; font-weight: 600;">${item.shortage > 0 ? item.shortage.toLocaleString() : '0'}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${item.fulfillment}%; background: ${fulfillmentColor};"></div>
                        </div>
                        <span style="font-size: 11px;">${item.fulfillment.toFixed(1)}%</span>
                    </td>
                    <td><span class="status-badge ${statusClass}">${item.status}</span></td>
                    <td><button class="expand-btn" onclick="toggleDetail(${index})"><i class="fas fa-chevron-down"></i></button></td>
                `;

                // Detail row
                const detailRow = tbody.insertRow();
                detailRow.className = 'detail-row';
                detailRow.id = `detail-${index}`;
                
                let deptHtml = '';
                if (item.departments && Object.keys(item.departments).length > 0) {
                    for (const [dept, qty] of Object.entries(item.departments)) {
                        deptHtml += `<span class="dept-tag"><strong>${dept}:</strong> ${qty.toLocaleString()} nos</span>`;
                    }
                } else {
                    deptHtml = '<span>No department data available</span>';
                }

                detailRow.innerHTML = `
                    <td colspan="10" class="detail-cell">
                        <div style="margin-bottom: 10px;"><strong><i class="fas fa-building"></i> Department-wise Stock Breakup:</strong></div>
                        <div class="dept-tags">${deptHtml}</div>
                        <div style="margin-top: 10px; font-size: 12px; color: #666;">
                            <strong>Order Details:</strong> SO Qty: ${item.so_qty.toLocaleString()} | Invoiced: ${item.invoiced_qty.toLocaleString()} | Balance: ${item.balance_qty.toLocaleString()}
                        </div>
                    </td>
                `;
            });
        }

        function toggleDetail(index) {
            const detailRow = document.getElementById(`detail-${index}`);
            if (detailRow) {
                detailRow.classList.toggle('show');
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Search and filter
        document.getElementById('searchInput').addEventListener('input', filterResults);
        document.getElementById('statusFilter').addEventListener('change', filterResults);

        function filterResults() {
            if (!analysisData) return;
            
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const statusFilter = document.getElementById('statusFilter').value;
            
            let filtered = analysisData.results;
            
            if (searchTerm) {
                filtered = filtered.filter(item => 
                    item.item_no.toLowerCase().includes(searchTerm) ||
                    item.customer.toLowerCase().includes(searchTerm) ||
                    item.sales_desc.toLowerCase().includes(searchTerm)
                );
            }
            
            if (statusFilter !== 'all') {
                filtered = filtered.filter(item => item.status === statusFilter);
            }
            
            displayResults(filtered);
        }

        // Export to Excel
        document.getElementById('exportBtn').addEventListener('click', async () => {
            if (!analysisData) return;

            const exportBtn = document.getElementById('exportBtn');
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> Exporting...';
            exportBtn.disabled = true;

            try {
                const response = await fetch('/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ results: analysisData.results, stats: analysisData.stats })
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `stock_analysis_${new Date().toISOString().slice(0,19)}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                } else {
                    alert('Export failed');
                }
            } catch (error) {
                alert('Export error: ' + error.message);
            } finally {
                exportBtn.innerHTML = '<i class="fas fa-download"></i> Export Excel';
                exportBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'sales_file' not in request.files or 'stock_file' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400
        
        sales_file = request.files['sales_file']
        stock_file = request.files['stock_file']
        
        if sales_file.filename == '' or stock_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        sales_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(sales_file.filename))
        stock_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(stock_file.filename))
        
        sales_file.save(sales_path)
        stock_file.save(stock_path)
        
        results, stats = process_files(sales_path, stock_path)
        
        os.remove(sales_path)
        os.remove(stock_path)
        
        return jsonify({
            'success': True,
            'results': results,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST'])
def export():
    try:
        data = request.json
        results = data.get('results', [])
        stats = data.get('stats', {})
        
        # Create DataFrame
        df = pd.DataFrame([{
            'Item No': r['item_no'],
            'Customer': r['customer'],
            'City': r['city'],
            'SO No': r['so_no'],
            'Description': r['sales_desc'],
            'SO Qty': r['so_qty'],
            'Invoiced Qty': r['invoiced_qty'],
            'Balance Qty': r['balance_qty'],
            'Pending Qty': r['pending_qty'],
            'Total Stock': r['total_stock'],
            'Shortage': r['shortage'],
            'Excess': r['excess'],
            'Fulfillment %': r['fulfillment'],
            'Status': r['status']
        } for r in results])
        
        # Department breakdown
        dept_data = []
        for r in results:
            for dept, qty in r['departments'].items():
                dept_data.append({
                    'Item No': r['item_no'],
                    'Customer': r['customer'],
                    'Department': dept,
                    'Stock Qty': qty
                })
        df_dept = pd.DataFrame(dept_data)
        
        # Statistics
        df_stats = pd.DataFrame([
            ['Total Items Analyzed', stats.get('total_items', 0)],
            ['Total Pending Quantity', stats.get('total_pending', 0)],
            ['Total Stock Available', stats.get('total_stock', 0)],
            ['Total Shortage', stats.get('total_shortage', 0)],
            ['Sufficient Stock Items', stats.get('sufficient_count', 0)],
            ['Partial Stock Items', stats.get('partial_count', 0)],
            ['No Stock Items', stats.get('no_stock_count', 0)]
        ], columns=['Metric', 'Value'])
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'stock_analysis_{timestamp}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Summary', index=False)
            df_dept.to_excel(writer, sheet_name='Department Stock', index=False)
            df_stats.to_excel(writer, sheet_name='Statistics', index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("STOCK ANALYSIS SYSTEM - Puja Fluid Seals Pvt. Ltd.")
    print("=" * 60)
    print("\nStarting server...")
    print("Please open http://localhost:5000 in your browser")
    print("\n" + "=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)