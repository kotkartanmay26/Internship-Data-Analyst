# filename: colored_headers_app.py
# Run with: python colored_headers_app.py

from flask import Flask, render_template_string, request, jsonify, send_file
import pandas as pd
import numpy as np
import webbrowser
import threading
import io
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Production Planning Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { padding: 20px; background: #f0f2f5; }
        .container { max-width: 1600px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .upload-area { border: 2px dashed #007bff; border-radius: 10px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.3s; background: #f8f9fa; }
        .upload-area:hover { background: #e7f1ff; border-color: #0056b3; }
        .upload-area.has-file { background: #d4edda; border-color: #28a745; }
        .btn-calc { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 40px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
        .btn-calc:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .btn-calc:disabled { opacity: 0.5; cursor: not-allowed; }
        .pending { background: #dc3545; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
        .sufficient { background: #28a745; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
        .table-responsive { max-height: 550px; overflow: auto; border-radius: 8px; }
        table { font-size: 11px; }
        th { 
            position: sticky; 
            top: 0; 
            z-index: 10; 
            padding: 10px 8px;
            font-weight: bold;
            text-align: center;
        }
        /* Individual column header colors */
        th:nth-child(1) { background: #4CAF50; color: white; }  /* # - Green */
        th:nth-child(2) { background: #2196F3; color: white; }  /* Customer - Blue */
        th:nth-child(3) { background: #9C27B0; color: white; }  /* Item No - Purple */
        th:nth-child(4) { background: #FF9800; color: white; }  /* Type - Orange */
        th:nth-child(5) { background: #795548; color: white; }  /* Description - Brown */
        th:nth-child(6) { background: #607D8B; color: white; }  /* Balance Qty - Blue Grey */
        th:nth-child(7) { background: #00BCD4; color: white; }  /* Stock Available - Cyan */
        th:nth-child(8) { background: #dc3545; color: white; }  /* Pending Qty - Red */
        th:nth-child(9) { background: #FF5722; color: white; }  /* Status - Deep Orange */
        
        /* Stock table headers */
        .stock-table th:nth-child(1) { background: #4CAF50; color: white; }  /* # */
        .stock-table th:nth-child(2) { background: #2196F3; color: white; }  /* Item No */
        .stock-table th:nth-child(3) { background: #9C27B0; color: white; }  /* Type */
        .stock-table th:nth-child(4) { background: #FF9800; color: white; }  /* Batch No */
        .stock-table th:nth-child(5) { background: #795548; color: white; }  /* Description */
        .stock-table th:nth-child(6) { background: #00BCD4; color: white; }  /* Stock Qty */
        .stock-table th:nth-child(7) { background: #607D8B; color: white; }  /* Unit */
        
        .metric-card { text-align: center; padding: 15px; border-radius: 10px; margin-bottom: 10px; transition: transform 0.3s; }
        .metric-card:hover { transform: translateY(-5px); }
        .loading { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); z-index: 1000; min-width: 350px; text-align: center; }
        .loading.show { display: block; }
        .progress-bar-custom { height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; margin-top: 15px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.3s; }
        .nav-tabs .nav-link { color: #495057; font-weight: 500; }
        .nav-tabs .nav-link.active { background: #007bff; color: white; border-color: #007bff; }
        .table-warning { background-color: #fff3cd !important; }
        
        /* Custom scrollbar */
        .table-responsive::-webkit-scrollbar { width: 8px; height: 8px; }
        .table-responsive::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
        .table-responsive::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
        .table-responsive::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
</head>
<body>
<div class="loading" id="loading">
    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
    <h5 id="loadingText">Processing Large Files...</h5>
    <div class="progress-bar-custom">
        <div class="progress-fill" id="progressFill"></div>
    </div>
    <p class="text-muted mt-2" id="loadingDetail">Reading all stock rows...</p>
</div>

<div class="container">
    <div class="card text-center">
        <h2>📊 Production Planning Dashboard</h2>
        <p class="lead">Planning Pending = Balance Qty - Stock Available</p>
        <p class="text-muted">📋 Shows ALL stock rows (each batch separately)</p>
    </div>

    <div class="card">
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="row">
                <div class="col-md-4 mb-3">
                    <div class="upload-area" id="bomArea" onclick="document.getElementById('bom').click()">
                        📁 <strong>1. BOM File</strong>
                        <input type="file" id="bom" name="bom" style="display:none" accept=".xlsx,.xls" required>
                        <div id="bom_name" class="mt-2"></div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="upload-area" id="pendingArea" onclick="document.getElementById('pending').click()">
                        📋 <strong>2. Pending Orders</strong>
                        <input type="file" id="pending" name="pending" style="display:none" accept=".xlsx,.xls" required>
                        <div id="pending_name" class="mt-2"></div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="upload-area" id="stockArea" onclick="document.getElementById('stock').click()">
                        📦 <strong>3. Stock Report</strong>
                        <input type="file" id="stock" name="stock" style="display:none" accept=".xlsx,.xls" required>
                        <div id="stock_name" class="mt-2"></div>
                    </div>
                </div>
            </div>
        </form>
        <div class="text-center mt-2">
            <button class="btn-calc" id="calcBtn" onclick="calculate()" disabled>▶ CALCULATE</button>
        </div>
    </div>

    <div id="results" style="display:none;"></div>
</div>

<script>
let fileStatus = { bom: false, pending: false, stock: false };
let resultData = null;

document.getElementById('bom').onchange = function(e) {
    document.getElementById('bom_name').innerHTML = '✅ ' + e.target.files[0].name;
    document.getElementById('bomArea').classList.add('has-file');
    fileStatus.bom = true;
    checkAllFiles();
};

document.getElementById('pending').onchange = function(e) {
    document.getElementById('pending_name').innerHTML = '✅ ' + e.target.files[0].name;
    document.getElementById('pendingArea').classList.add('has-file');
    fileStatus.pending = true;
    checkAllFiles();
};

document.getElementById('stock').onchange = function(e) {
    document.getElementById('stock_name').innerHTML = '✅ ' + e.target.files[0].name;
    document.getElementById('stockArea').classList.add('has-file');
    fileStatus.stock = true;
    checkAllFiles();
};

function checkAllFiles() {
    const allUploaded = fileStatus.bom && fileStatus.pending && fileStatus.stock;
    document.getElementById('calcBtn').disabled = !allUploaded;
}

async function calculate() {
    const formData = new FormData();
    formData.append('bom', document.getElementById('bom').files[0]);
    formData.append('pending', document.getElementById('pending').files[0]);
    formData.append('stock', document.getElementById('stock').files[0]);
    
    document.getElementById('loading').classList.add('show');
    document.getElementById('progressFill').style.width = '10%';
    
    try {
        document.getElementById('progressFill').style.width = '30%';
        document.getElementById('loadingDetail').innerHTML = 'Reading Excel files...';
        
        const response = await fetch('/calculate', { method: 'POST', body: formData });
        document.getElementById('progressFill').style.width = '80%';
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        if(data.success) {
            resultData = data;
            displayDashboard(data);
            document.getElementById('results').style.display = 'block';
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch(err) {
        alert('Error: ' + err.message);
    } finally {
        setTimeout(() => {
            document.getElementById('loading').classList.remove('show');
            document.getElementById('progressFill').style.width = '0%';
        }, 500);
    }
}

function displayDashboard(data) {
    const html = `
        <div class="card">
            <div class="row">
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white">
                        <h2>${data.total_stock_rows.toLocaleString()}</h2>
                        <small>Total Stock Rows</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white">
                        <h2>${data.total_stock_qty.toLocaleString()}</h2>
                        <small>📦 Total Stock Qty</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:white">
                        <h2>${data.total_pending_orders.toLocaleString()}</h2>
                        <small>📋 Pending Orders</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#43e97b 0%,#38f9d7 100%);color:white">
                        <h2>${data.planning_pending.toLocaleString()}</h2>
                        <small>⚠️ Planning Pending</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="row">
                <div class="col-md-6">
                    <canvas id="stockChart" style="max-height: 300px;"></canvas>
                </div>
                <div class="col-md-6">
                    <canvas id="pendingChart" style="max-height: 300px;"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card">
            <input type="text" id="search" class="form-control mb-3" placeholder="🔍 Search by Item No, Batch No, or Description...">
            <ul class="nav nav-tabs">
                <li class="nav-item"><button class="nav-link active" onclick="showTab('stock_all')">📦 ALL STOCK ROWS (${data.total_stock_rows.toLocaleString()})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('stock_fg')">🏭 FG STOCK ROWS (${data.fg_stock_rows.toLocaleString()})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('stock_sfg')">🔧 SFG STOCK ROWS (${data.sfg_stock_rows.toLocaleString()})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('pending_all')">📋 ALL PENDING (${data.total_pending_orders})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('pending_planning')">⚠️ NEED PLANNING (${data.planning_pending_count})</button></li>
            </ul>
            <div class="table-responsive mt-3" id="table_container"></div>
            <button class="btn btn-success mt-3" onclick="downloadReport()">📥 Download Excel Report</button>
        </div>
        
        <div class="card">
            <h6>Debug Information</h6>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; font-family:monospace; font-size:11px; max-height:300px; overflow:auto;">
                <pre>${data.debug}</pre>
            </div>
        </div>
    `;
    
    document.getElementById('results').innerHTML = html;
    
    // Stock distribution chart
    const ctx1 = document.getElementById('stockChart').getContext('2d');
    new Chart(ctx1, {
        type: 'pie',
        data: {
            labels: ['FG Stock Qty', 'SFG Stock Qty'],
            datasets: [{ data: [data.fg_stock_qty, data.sfg_stock_qty], backgroundColor: ['#007bff', '#17a2b8'] }]
        }
    });
    
    // Top pending items chart
    const ctx2 = document.getElementById('pendingChart').getContext('2d');
    const topItems = data.pending_data.filter(r => r.pending_qty > 0).slice(0, 10);
    new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: topItems.map(r => r.item_no),
            datasets: [{ label: 'Pending Qty', data: topItems.map(r => r.pending_qty), backgroundColor: '#dc3545' }]
        }
    });
    
    window.stockData = data.stock_data;
    window.pendingData = data.pending_data;
    renderTable('stock_all');
}

function renderTable(type) {
    let data = [];
    let title = '';
    let isStockTable = false;
    
    if(type === 'stock_all') {
        data = window.stockData;
        title = 'ALL STOCK ROWS (Each Batch Shown Separately)';
        isStockTable = true;
    } else if(type === 'stock_fg') {
        data = window.stockData.filter(r => r.item_type === 'FG');
        title = 'FG STOCK ROWS';
        isStockTable = true;
    } else if(type === 'stock_sfg') {
        data = window.stockData.filter(r => r.item_type === 'SFG');
        title = 'SFG STOCK ROWS';
        isStockTable = true;
    } else if(type === 'pending_all') {
        data = window.pendingData;
        title = 'ALL PENDING ORDERS';
        isStockTable = false;
    } else if(type === 'pending_planning') {
        data = window.pendingData.filter(r => r.pending_qty > 0);
        title = 'ITEMS NEEDING PLANNING';
        isStockTable = false;
    }
    
    if(data.length === 0) {
        document.getElementById('table_container').innerHTML = '<div class="alert alert-info">No records found</div>';
        return;
    }
    
    let html = `<h6 class="mb-2">${title} (${data.length.toLocaleString()} records)</h6>`;
    html += '<div class="table-responsive">';
    
    if(isStockTable) {
        // STOCK TABLE WITH COLORED HEADERS
        html += '<table class="table table-bordered table-hover table-sm stock-table"><thead>';
        html += '<tr>';
        html += '<th style="background:#4CAF50; color:white; text-align:center;">#</th>';
        html += '<th style="background:#2196F3; color:white; text-align:center;">Item No</th>';
        html += '<th style="background:#9C27B0; color:white; text-align:center;">Type</th>';
        html += '<th style="background:#FF9800; color:white; text-align:center;">Batch No</th>';
        html += '<th style="background:#795548; color:white; text-align:center;">Description</th>';
        html += '<th style="background:#00BCD4; color:white; text-align:center;">Stock Qty</th>';
        html += '<th style="background:#607D8B; color:white; text-align:center;">Unit</th>';
        html += '</tr></thead><tbody>';
        
        data.forEach((r, idx) => {
            const rowClass = r.stock_qty == 0 ? 'table-warning' : '';
            html += `<tr class="${rowClass}">
                <td style="text-align:center;">${idx + 1}</td>
                <td><strong>${r.item_no}</strong></td>
                <td style="text-align:center;"><span class="badge ${r.item_type === 'FG' ? 'bg-primary' : 'bg-info'}">${r.item_type}</span></td>
                <td><small>${r.batch_no || '-'}</small></td>
                <td>${escapeHtml((r.item_desc || '').substring(0, 60))}</td>
                <td style="text-align:right;"><strong>${r.stock_qty.toLocaleString()}</strong></td>
                <td>${r.unit || '-'}</td>
            </tr>`;
        });
    } else {
        // PENDING TABLE WITH COLORED HEADERS (Balance Qty, Stock Available, Pending Qty highlighted)
        html += '<table class="table table-bordered table-hover table-sm"><thead>';
        html += '<tr>';
        html += '<th style="background:#4CAF50; color:white; text-align:center;">#</th>';
        html += '<th style="background:#2196F3; color:white; text-align:center;">Customer</th>';
        html += '<th style="background:#9C27B0; color:white; text-align:center;">Item No</th>';
        html += '<th style="background:#FF9800; color:white; text-align:center;">Type</th>';
        html += '<th style="background:#795548; color:white; text-align:center;">Description</th>';
        html += '<th style="background:#607D8B; color:white; text-align:center;">Balance Qty</th>';
        html += '<th style="background:#00BCD4; color:white; text-align:center;">Stock Available</th>';
        html += '<th style="background:#dc3545; color:white; text-align:center;">Pending Qty</th>';
        html += '<th style="background:#FF5722; color:white; text-align:center;">Status</th>';
        html += '</tr></thead><tbody>';
        
        data.forEach((r, idx) => {
            const pendingClass = r.pending_qty > 0 ? 'pending' : 'sufficient';
            const statusText = r.pending_qty > 0 ? '⚠️ NEED PLANNING' : '✅ SUFFICIENT';
            
            html += `<tr>
                <td style="text-align:center;">${idx + 1}</td>
                <td>${escapeHtml(r.cust_name || '-')}</td>
                <td><strong>${r.item_no}</strong></td>
                <td style="text-align:center;"><span class="badge ${r.item_type === 'FG' ? 'bg-primary' : 'bg-info'}">${r.item_type}</span></td>
                <td>${escapeHtml((r.item_desc || '').substring(0, 50))}</td>
                <td style="text-align:right; background:#f8f9fa;"><strong>${r.bal_qty.toLocaleString()}</strong></td>
                <td style="text-align:right; background:#e3f2fd;"><strong>${r.stock_available.toLocaleString()}</strong></td>
                <td style="text-align:right; background:#ffebee;" class="${pendingClass}"><strong>${r.pending_qty.toLocaleString()}</strong></td>
                <td style="text-align:center;"><span class="${pendingClass}">${statusText}</span></td>
            </tr>`;
        });
    }
    
    html += '</tbody></table></div>';
    document.getElementById('table_container').innerHTML = html;
}

function showTab(type) {
    renderTable(type);
    document.querySelectorAll('.nav-link').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

document.getElementById('search').onkeyup = function() {
    const term = this.value.toLowerCase();
    if(!window.stockData) return;
    const filtered = window.stockData.filter(r => 
        (r.item_no && r.item_no.toLowerCase().includes(term)) ||
        (r.item_desc && r.item_desc.toLowerCase().includes(term)) ||
        (r.batch_no && r.batch_no.toLowerCase().includes(term))
    );
    window.stockDataFiltered = filtered;
    renderTable('stock_all');
};

function escapeHtml(str) {
    if(!str) return '';
    return String(str).replace(/[&<>]/g, function(m) {
        if(m === '&') return '&amp;';
        if(m === '<') return '&lt;';
        if(m === '>') return '&gt;';
        return m;
    });
}

function downloadReport() {
    if(!resultData) return alert('No data');
    
    fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            pending_data: resultData.pending_data,
            stock_data: resultData.stock_data 
        })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Complete_Stock_Planning_Report.xlsx';
        a.click();
        window.URL.revokeObjectURL(url);
    });
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/calculate', methods=['POST'])
def calculate():
    debug = []
    debug.append("="*80)
    debug.append("📊 COMPLETE STOCK & PLANNING - ALL ROWS (INCLUDING ZERO STOCK)")
    debug.append("="*80)
    
    try:
        # Read files
        bom_file = request.files.get('bom')
        pending_file = request.files.get('pending')
        stock_file = request.files.get('stock')
        
        debug.append("\n📁 Reading files...")
        
        # Read BOM
        bom_df = pd.read_excel(bom_file)
        debug.append(f"   BOM: {len(bom_df):,} rows")
        
        # Read Pending Orders
        pending_df = pd.read_excel(pending_file)
        debug.append(f"   Pending Orders: {len(pending_df):,} rows")
        
        # Read Stock File - Find headers
        stock_df = None
        for skip in range(0, 15):
            temp_df = pd.read_excel(stock_file, skiprows=skip, nrows=5)
            if 'ItemNo' in temp_df.columns:
                stock_df = pd.read_excel(stock_file, skiprows=skip)
                debug.append(f"   Stock Report: Found headers at row {skip + 1}")
                break
        
        if stock_df is None:
            raw_df = pd.read_excel(stock_file, header=None, nrows=20)
            for idx, row in raw_df.iterrows():
                row_str = ' '.join([str(x) for x in row.values if pd.notna(x)])
                if 'ItemNo' in row_str:
                    stock_df = pd.read_excel(stock_file, skiprows=idx)
                    debug.append(f"   Stock Report: Found headers at row {idx + 1}")
                    break
        
        if stock_df is None:
            stock_df = pd.read_excel(stock_file)
            debug.append(f"   Stock Report: Using default headers")
        
        debug.append(f"   Stock Report: {len(stock_df):,} rows, {len(stock_df.columns)} columns")
        
        # Find closing stock column
        closing_col = None
        for col in stock_df.columns:
            col_lower = str(col).lower()
            if 'closing' in col_lower:
                closing_col = col
                break
        
        if closing_col is None:
            if 'Closing Stock' in stock_df.columns:
                closing_col = 'Closing Stock'
            elif 'Stock' in stock_df.columns:
                closing_col = 'Stock'
        
        debug.append(f"   Using closing stock column: '{closing_col}'")
        
        # READ ALL STOCK ROWS - NO FILTERING
        debug.append("\n📦 READING ALL STOCK ROWS (KEEPING EVERY ROW)...")
        
        stock_rows = []
        fg_rows = 0
        sfg_rows = 0
        total_stock_qty = 0
        fg_stock_qty = 0
        sfg_stock_qty = 0
        zero_stock_count = 0
        
        for idx, row in stock_df.iterrows():
            item_no = str(row.get('ItemNo', '')).strip()
            if not item_no or item_no == 'nan' or item_no == '':
                continue
            
            # Get stock quantity
            try:
                if closing_col:
                    stock_qty = float(row.get(closing_col, 0)) if pd.notna(row.get(closing_col, 0)) else 0
                else:
                    stock_qty = 0
            except (ValueError, TypeError):
                stock_qty = 0
            
            if stock_qty == 0:
                zero_stock_count += 1
            
            item_type = 'FG' if str(item_no).startswith('FG') else 'SFG'
            
            batch_no = str(row.get('BatchNo', '')) if 'BatchNo' in row else ''
            if batch_no == 'nan':
                batch_no = ''
            
            item_desc = str(row.get('ItemDesc', '')) if 'ItemDesc' in row else ''
            if item_desc == 'nan':
                item_desc = ''
            
            unit = str(row.get('UnitCode', '')) if 'UnitCode' in row else ''
            if unit == 'nan':
                unit = ''
            
            stock_rows.append({
                'item_no': item_no,
                'item_type': item_type,
                'batch_no': batch_no,
                'item_desc': item_desc[:150],
                'stock_qty': round(stock_qty, 2),
                'unit': unit
            })
            
            total_stock_qty += stock_qty
            
            if item_type == 'FG':
                fg_rows += 1
                fg_stock_qty += stock_qty
            else:
                sfg_rows += 1
                sfg_stock_qty += stock_qty
            
            if (idx + 1) % 5000 == 0:
                debug.append(f"   Processed {idx + 1:,} rows...")
        
        debug.append(f"\n📊 STOCK SUMMARY:")
        debug.append(f"   Total Stock Rows: {len(stock_rows):,}")
        debug.append(f"   Rows with Zero Stock: {zero_stock_count:,}")
        debug.append(f"   Rows with Positive Stock: {len(stock_rows) - zero_stock_count:,}")
        debug.append(f"   FG Rows: {fg_rows:,} (Total Qty: {fg_stock_qty:,.2f})")
        debug.append(f"   SFG Rows: {sfg_rows:,} (Total Qty: {sfg_stock_qty:,.2f})")
        debug.append(f"   Total Stock Quantity: {total_stock_qty:,.2f}")
        
        # Create aggregated stock dictionary for pending calculation
        stock_aggregated = {}
        for row in stock_rows:
            if row['stock_qty'] > 0:
                item_no = row['item_no']
                stock_aggregated[item_no] = stock_aggregated.get(item_no, 0) + row['stock_qty']
        
        debug.append(f"\n📦 Aggregated for Pending: {len(stock_aggregated):,} unique items")
        
        # BOM Mapping
        debug.append("\n📋 PROCESSING BOM MAPPING...")
        bom_mapping = {}
        for _, row in bom_df.iterrows():
            part_type = str(row.get('PartType', '')).upper()
            if part_type == 'BOM':
                fg_item = str(row.get('ItemNo', '')).strip()
                sfg_code = str(row.get('BOM_ItemCode', '')).strip()
                if fg_item and fg_item != 'nan' and sfg_code and sfg_code != 'nan' and sfg_code:
                    if fg_item not in bom_mapping:
                        bom_mapping[fg_item] = sfg_code
        
        debug.append(f"   BOM Mappings: {len(bom_mapping):,}")
        
        # Process Pending Orders
        debug.append("\n📋 PROCESSING PENDING ORDERS...")
        
        balance_col = None
        for col in pending_df.columns:
            if 'bal' in str(col).lower():
                balance_col = col
                break
        
        if balance_col is None:
            if 'Bal_Qty' in pending_df.columns:
                balance_col = 'Bal_Qty'
            elif 'BalQty' in pending_df.columns:
                balance_col = 'BalQty'
        
        debug.append(f"   Using balance column: '{balance_col}'")
        
        pending_list = []
        total_balance = 0
        total_pending = 0
        pending_count = 0
        
        for idx, row in pending_df.iterrows():
            item_no = str(row.get('ItemNo', '')).strip()
            if not item_no or item_no == 'nan':
                continue
            
            try:
                if balance_col:
                    bal_qty = float(row.get(balance_col, 0)) if pd.notna(row.get(balance_col, 0)) else 0
                else:
                    bal_qty = 0
            except (ValueError, TypeError):
                bal_qty = 0
            
            if bal_qty <= 0:
                continue
            
            cust_name = str(row.get('CustName', '')) if 'CustName' in row else ''
            if cust_name == 'nan':
                cust_name = ''
            
            item_desc = str(row.get('ItemDesc', '')) if 'ItemDesc' in row else ''
            if item_desc == 'nan':
                item_desc = ''
            
            item_type = 'FG' if item_no.startswith('FG') else 'SFG'
            stock_qty = stock_aggregated.get(item_no, 0)
            pending_qty = max(0, bal_qty - stock_qty)
            
            if pending_qty > 0:
                pending_count += 1
            
            total_balance += bal_qty
            total_pending += pending_qty
            
            pending_list.append({
                'cust_name': cust_name,
                'item_no': item_no,
                'item_type': item_type,
                'item_desc': item_desc[:150],
                'bal_qty': round(bal_qty, 2),
                'stock_available': round(stock_qty, 2),
                'pending_qty': round(pending_qty, 2),
                'sfg_mapping': bom_mapping.get(item_no, '') if item_type == 'FG' else ''
            })
        
        debug.append(f"\n📊 PENDING SUMMARY:")
        debug.append(f"   Total Pending Orders: {len(pending_list):,}")
        debug.append(f"   Total Balance Quantity: {total_balance:,.2f}")
        debug.append(f"   Total Stock Available: {sum(p['stock_available'] for p in pending_list):,.2f}")
        debug.append(f"   🔴 TOTAL PLANNING PENDING: {total_pending:,.2f}")
        debug.append(f"   Items Needing Planning: {pending_count:,}")
        
        debug.append(f"\n{'='*80}")
        debug.append(f"✅ ANALYSIS COMPLETE!")
        debug.append(f"{'='*80}")
        
        return jsonify({
            'success': True,
            'debug': '\n'.join(debug),
            'stock_data': stock_rows,
            'pending_data': pending_list,
            'total_stock_rows': len(stock_rows),
            'total_stock_qty': round(total_stock_qty, 2),
            'fg_stock_rows': fg_rows,
            'fg_stock_qty': round(fg_stock_qty, 2),
            'sfg_stock_rows': sfg_rows,
            'sfg_stock_qty': round(sfg_stock_qty, 2),
            'total_pending_orders': len(pending_list),
            'total_balance': round(total_balance, 2),
            'planning_pending': round(total_pending, 2),
            'planning_pending_count': pending_count
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e) + '\n' + traceback.format_exc()
        debug.append(f"\n❌ ERROR: {error_msg}")
        return jsonify({'success': False, 'error': str(e), 'debug': '\n'.join(debug)})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    pending_data = data.get('pending_data', [])
    stock_data = data.get('stock_data', [])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(stock_data).to_excel(writer, sheet_name='All Stock Rows', index=False)
        pd.DataFrame(pending_data).to_excel(writer, sheet_name='Pending Orders', index=False)
        
        summary = pd.DataFrame({
            'Metric': [
                'Total Stock Rows', 'Total Stock Quantity', 'FG Stock Rows', 'FG Stock Quantity',
                'SFG Stock Rows', 'SFG Stock Quantity', 'Total Pending Orders', 'Total Balance', 'Planning Pending'
            ],
            'Value': [
                len(stock_data), round(sum(s['stock_qty'] for s in stock_data), 2),
                len([s for s in stock_data if s['item_type'] == 'FG']), round(sum(s['stock_qty'] for s in stock_data if s['item_type'] == 'FG'), 2),
                len([s for s in stock_data if s['item_type'] == 'SFG']), round(sum(s['stock_qty'] for s in stock_data if s['item_type'] == 'SFG'), 2),
                len(pending_data), round(sum(p['bal_qty'] for p in pending_data), 2), round(sum(p['pending_qty'] for p in pending_data), 2)
            ]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return send_file(output, download_name='Complete_Stock_Planning_Report.xlsx', as_attachment=True)

def open_browser():
    import time
    time.sleep(2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 PRODUCTION PLANNING DASHBOARD - COLORED HEADERS")
    print("="*80)
    print("\n📌 Opening browser at: http://127.0.0.1:5000")
    print("\n⚠️  Keep this terminal open!")
    print("="*80 + "\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, host='127.0.0.1', port=5000)