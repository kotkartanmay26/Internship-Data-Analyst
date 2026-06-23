# filename: planning_app_complete.py
# Run with: python planning_app_complete.py

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
    <title>Production Planning Dashboard - Complete SFG View</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { padding: 20px; background: #f0f2f5; font-family: 'Segoe UI', sans-serif; }
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
        th { background: #343a40; color: white; position: sticky; top: 0; z-index: 10; padding: 8px; }
        .matched { background: #d4edda; }
        .unmatched { background: #fff3cd; }
        .metric-card { text-align: center; padding: 15px; border-radius: 10px; margin-bottom: 10px; transition: transform 0.3s; }
        .metric-card:hover { transform: translateY(-5px); }
        .loading { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); z-index: 1000; min-width: 350px; text-align: center; }
        .loading.show { display: block; }
        .progress-bar-custom { height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; margin-top: 15px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.3s; }
        .nav-tabs .nav-link { color: #495057; font-weight: 500; }
        .nav-tabs .nav-link.active { background: #007bff; color: white; border-color: #007bff; }
        .badge-large { font-size: 14px; padding: 8px 15px; }
    </style>
</head>
<body>
<div class="loading" id="loading">
    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
    <h5 id="loadingText">Processing Files...</h5>
    <div class="progress-bar-custom">
        <div class="progress-fill" id="progressFill"></div>
    </div>
    <p class="text-muted mt-2" id="loadingDetail">Please wait, analyzing large files...</p>
</div>

<div class="container">
    <div class="card text-center">
        <h2>📊 Production Planning Dashboard</h2>
        <p class="lead">Planning Pending = Balance Qty - (FG Stock + SFG Stock)</p>
        <p class="text-muted"><small>🔗 Matching Logic: Same BatchNo between FG and SFG items</small></p>
    </div>

    <div class="card">
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="row">
                <div class="col-md-4 mb-3">
                    <div class="upload-area" id="bomArea" onclick="document.getElementById('bom').click()">
                        📁 <strong>1. BOM File</strong><br>
                        <small>Bom_Details_List.xlsx</small>
                        <input type="file" id="bom" name="bom" style="display:none" accept=".xlsx,.xls" required>
                        <div id="bom_name" class="mt-2"></div>
                        <div id="bom_status" class="mt-1"><span class="badge bg-secondary">Pending</span></div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="upload-area" id="pendingArea" onclick="document.getElementById('pending').click()">
                        📋 <strong>2. Pending Orders</strong><br>
                        <small>pending qty erp all.xlsx</small>
                        <input type="file" id="pending" name="pending" style="display:none" accept=".xlsx,.xls" required>
                        <div id="pending_name" class="mt-2"></div>
                        <div id="pending_status" class="mt-1"><span class="badge bg-secondary">Pending</span></div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="upload-area" id="stockArea" onclick="document.getElementById('stock').click()">
                        📦 <strong>3. Stock Report</strong><br>
                        <small>Stock_Report_FG+WIP_Lot_Wise.xlsx</small>
                        <input type="file" id="stock" name="stock" style="display:none" accept=".xlsx,.xls" required>
                        <div id="stock_name" class="mt-2"></div>
                        <div id="stock_status" class="mt-1"><span class="badge bg-secondary">Pending</span></div>
                    </div>
                </div>
            </div>
        </form>
        <div class="text-center mt-2">
            <button class="btn-calc" id="calcBtn" onclick="calculate()" disabled>▶ CALCULATE PLANNING PENDING</button>
        </div>
    </div>

    <div id="results" style="display:none;"></div>
</div>

<script>
let fileStatus = { bom: false, pending: false, stock: false };
let resultData = null;

document.getElementById('bom').onchange = function(e) {
    let fileName = e.target.files[0].name;
    document.getElementById('bom_name').innerHTML = '✅ ' + fileName;
    document.getElementById('bom_status').innerHTML = '<span class="badge bg-success">Uploaded</span>';
    document.getElementById('bomArea').classList.add('has-file');
    fileStatus.bom = true;
    checkAllFiles();
};

document.getElementById('pending').onchange = function(e) {
    let fileName = e.target.files[0].name;
    document.getElementById('pending_name').innerHTML = '✅ ' + fileName;
    document.getElementById('pending_status').innerHTML = '<span class="badge bg-success">Uploaded</span>';
    document.getElementById('pendingArea').classList.add('has-file');
    fileStatus.pending = true;
    checkAllFiles();
};

document.getElementById('stock').onchange = function(e) {
    let fileName = e.target.files[0].name;
    document.getElementById('stock_name').innerHTML = '✅ ' + fileName;
    document.getElementById('stock_status').innerHTML = '<span class="badge bg-success">Uploaded</span>';
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
        document.getElementById('loadingDetail').innerHTML = 'Reading and processing files...';
        
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
            if(data.debug) console.error(data.debug);
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
                        <h2>${data.total_orders.toLocaleString()}</h2>
                        <small>Total Orders</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white">
                        <h2>${data.total_pending.toLocaleString()}</h2>
                        <small>📦 Planning Pending</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:white">
                        <h2>${data.total_balance.toLocaleString()}</h2>
                        <small>⚖️ Total Balance</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card" style="background:linear-gradient(135deg,#43e97b 0%,#38f9d7 100%);color:white">
                        <h2>${data.total_stock.toLocaleString()}</h2>
                        <small>📊 Total Stock (FG+SFG)</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h5>🔗 SFG Matching Results (By BatchNo)</h5>
            <div class="row">
                <div class="col-md-4">
                    <div class="alert alert-success text-center">
                        <h4>${data.matched_by_batch}</h4>
                        <small>✅ Items with SFG Stock (Batch Match)</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="alert alert-warning text-center">
                        <h4>${data.no_match}</h4>
                        <small>⚠️ Items with NO SFG Stock</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="alert alert-info text-center">
                        <h4>${data.sfg_batch_count.toLocaleString()}</h4>
                        <small>🔧 Total SFG Batches Available</small>
                    </div>
                </div>
            </div>
            <div class="progress mt-2" style="height: 30px;">
                <div class="progress-bar bg-success" style="width: ${(data.matched_by_batch/data.total_orders*100)}%">Matched: ${data.matched_by_batch}</div>
                <div class="progress-bar bg-warning" style="width: ${(data.no_match/data.total_orders*100)}%">No Match: ${data.no_match}</div>
            </div>
            <p class="text-muted mt-2 small">Coverage: ${data.match_percentage}% of orders have SFG stock available</p>
        </div>
        
        <div class="card">
            <div class="row">
                <div class="col-md-6">
                    <canvas id="pendingChart" style="max-height: 300px;"></canvas>
                </div>
                <div class="col-md-6">
                    <h6>📊 SFG Stock Distribution (Top 10 SFG Items)</h6>
                    <canvas id="sfgChart" style="max-height: 300px;"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card">
            <input type="text" id="search" class="form-control mb-3" placeholder="🔍 Search by Customer, Item No, or Description...">
            <ul class="nav nav-tabs">
                <li class="nav-item"><button class="nav-link active" onclick="showTab('pending')">⚠️ Pending Items (${data.pending_count})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('all')">📋 All Items (${data.total_orders})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('no_sfg')">🔧 No SFG Stock (${data.no_match})</button></li>
                <li class="nav-item"><button class="nav-link" onclick="showTab('has_sfg')">✅ Has SFG Stock (${data.matched_by_batch})</button></li>
            </ul>
            <div class="table-responsive mt-3" id="table_container"></div>
            <button class="btn btn-success mt-3" onclick="downloadReport()">📥 Download Excel Report</button>
        </div>
        
        <div class="card">
            <h6>🐛 Debug Information - Check FG Batch Numbers</h6>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; font-family:monospace; font-size:11px; max-height:300px; overflow:auto;">
                <pre>${data.debug}</pre>
            </div>
        </div>
    `;
    
    document.getElementById('results').innerHTML = html;
    
    // Create charts
    const ctx1 = document.getElementById('pendingChart').getContext('2d');
    const topItems = data.data.filter(r => r.pending_qty > 0).slice(0, 10);
    new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: topItems.map(r => r.item_no),
            datasets: [{ label: 'Pending Quantity', data: topItems.map(r => r.pending_qty), backgroundColor: '#dc3545' }]
        },
        options: { responsive: true, maintainAspectRatio: true }
    });
    
    // SFG Chart
    if(data.top_sfg_items && data.top_sfg_items.length > 0) {
        const ctx2 = document.getElementById('sfgChart').getContext('2d');
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: data.top_sfg_items.map(r => r.item_no),
                datasets: [{ label: 'SFG Stock Quantity', data: data.top_sfg_items.map(r => r.stock), backgroundColor: '#17a2b8' }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
    }
    
    window.allData = data.data;
    renderTable('pending');
}

function renderTable(type) {
    let data = window.allData;
    if(type === 'pending') data = data.filter(r => r.pending_qty > 0);
    else if(type === 'no_sfg') data = data.filter(r => r.sfg_stock === 0 && r.bal_qty > 0);
    else if(type === 'has_sfg') data = data.filter(r => r.sfg_stock > 0);
    
    if(data.length === 0) {
        document.getElementById('table_container').innerHTML = '<div class="alert alert-info">No records found</div>';
        return;
    }
    
    let html = '<table class="table table-bordered table-hover"><thead><tr>';
    html += '<th>Customer</th><th>Item No</th><th>Description</th><th>SFG Code/Item</th><th>FG Batch No</th><th>SFG Batch No</th><th>Balance</th><th>FG Stock</th><th>SFG Stock</th><th>Total Stock</th><th>Pending</th><th>Status</th>';
    html += '</thead><tbody>';
    
    data.forEach(r => {
        const pendingClass = r.pending_qty > 0 ? 'pending' : 'sufficient';
        const statusText = r.pending_qty > 0 ? '⚠️ NEED PLANNING' : '✅ SUFFICIENT';
        const rowClass = r.sfg_stock > 0 ? 'matched' : 'unmatched';
        
        html += `<tr class="${rowClass}">
            <td>${escapeHtml(r.cust_name || '-')}</td>
            <td><strong>${r.item_no || '-'}</strong></td>
            <td>${escapeHtml((r.item_desc || '').substring(0, 50))}</td>
            <td>${r.sfg_code || '-'}</td>
            <td><small>${r.fg_batch || '-'}</small></td>
            <td><small>${r.sfg_batch || '-'}</small></td>
            <td>${(r.bal_qty || 0).toLocaleString()}</td>
            <td>${(r.fg_stock || 0).toLocaleString()}</td>
            <td><strong>${(r.sfg_stock || 0).toLocaleString()}</strong></td>
            <td>${((r.fg_stock || 0) + (r.sfg_stock || 0)).toLocaleString()}</td>
            <td class="${pendingClass}"><strong>${(r.pending_qty || 0).toLocaleString()}</strong></td>
            <td><span class="${pendingClass}">${statusText}</span></td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    document.getElementById('table_container').innerHTML = html;
}

function showTab(type) {
    renderTable(type);
    document.querySelectorAll('.nav-link').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

document.getElementById('search').onkeyup = function() {
    const term = this.value.toLowerCase();
    if(!window.allData) return;
    const filtered = window.allData.filter(r => 
        (r.cust_name && r.cust_name.toLowerCase().includes(term)) ||
        (r.item_no && r.item_no.toLowerCase().includes(term)) ||
        (r.item_desc && r.item_desc.toLowerCase().includes(term))
    );
    window.allData = filtered;
    renderTable('all');
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
    if(!resultData || !resultData.data) {
        alert('No data to download');
        return;
    }
    
    fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: resultData.data })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Planning_Pending_Report.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    })
    .catch(err => alert('Download error: ' + err.message));
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
    debug.append("📊 PRODUCTION PLANNING - COMPLETE SFG ANALYSIS")
    debug.append("="*80)
    
    try:
        # Read files
        bom_file = request.files.get('bom')
        pending_file = request.files.get('pending')
        stock_file = request.files.get('stock')
        
        debug.append("\n📁 Reading files...")
        bom_df = pd.read_excel(bom_file)
        pending_df = pd.read_excel(pending_file)
        stock_df = pd.read_excel(stock_file)
        
        debug.append(f"   BOM: {len(bom_df):,} rows, {len(bom_df.columns)} columns")
        debug.append(f"   Pending Orders: {len(pending_df):,} rows")
        debug.append(f"   Stock Report: {len(stock_df):,} rows, {len(stock_df.columns)} columns")
        
        # Clean column names
        stock_df.columns = [str(c).strip() for c in stock_df.columns]
        debug.append(f"\n📋 Stock Report Columns: {', '.join(stock_df.columns[:15])}")
        
        # Separate FG and SFG
        if 'ItemSubGroup' in stock_df.columns:
            fg_df = stock_df[stock_df['ItemSubGroup'].astype(str).str.upper() == 'FG'].copy()
            sfg_df = stock_df[stock_df['ItemSubGroup'].astype(str).str.upper() == 'SFG'].copy()
        else:
            fg_df = stock_df[stock_df['ItemNo'].astype(str).str.startswith('FG', na=False)].copy()
            sfg_df = stock_df[~stock_df['ItemNo'].astype(str).str.startswith('FG', na=False)].copy()
        
        debug.append(f"\n📊 Stock Separation:")
        debug.append(f"   FG Items: {len(fg_df):,} rows")
        debug.append(f"   SFG Items: {len(sfg_df):,} rows")
        
        # Build FG Stock with Batch numbers
        fg_stock = {}
        fg_batch_map = {}  # ItemNo -> BatchNo
        
        for _, row in fg_df.iterrows():
            item_no = str(row.get('ItemNo', '')).strip()
            closing = float(row.get('Closing Stock', 0)) if pd.notna(row.get('Closing Stock', 0)) else 0
            batch_no = str(row.get('BatchNo', '')).strip()
            
            if item_no and item_no != 'nan' and item_no != '':
                fg_stock[item_no] = fg_stock.get(item_no, 0) + closing
                if batch_no and batch_no != 'nan' and batch_no != '':
                    fg_batch_map[item_no] = batch_no
        
        debug.append(f"\n🏭 FG Stock Analysis:")
        debug.append(f"   Unique FG Items: {len(fg_stock):,}")
        debug.append(f"   FG Items with Batch Numbers: {len([k for k,v in fg_batch_map.items() if v]):,}")
        
        # Show sample of FG batches
        debug.append(f"\n📋 Sample FG Items with Batch Numbers:")
        for i, (item, batch) in enumerate(list(fg_batch_map.items())[:15]):
            debug.append(f"   {item} → Batch: '{batch}'")
        
        # Build SFG Stock by BatchNo (THIS IS KEY)
        sfg_by_batch = {}
        sfg_by_itemno = {}  # Also store by SFG ItemNo
        sfg_batch_details = {}  # Store batch details
        
        for _, row in sfg_df.iterrows():
            batch_no = str(row.get('BatchNo', '')).strip()
            closing = float(row.get('Closing Stock', 0)) if pd.notna(row.get('Closing Stock', 0)) else 0
            item_no = str(row.get('ItemNo', '')).strip()
            item_code = str(row.get('ItemCode', '')).strip()
            item_desc = str(row.get('ItemDesc', ''))
            
            if closing > 0:
                # Store by BatchNo
                if batch_no and batch_no != 'nan' and batch_no != '':
                    sfg_by_batch[batch_no] = sfg_by_batch.get(batch_no, 0) + closing
                    if batch_no not in sfg_batch_details:
                        sfg_batch_details[batch_no] = {
                            'item_no': item_no,
                            'item_code': item_code,
                            'item_desc': item_desc
                        }
                
                # Store by SFG ItemNo
                if item_no and item_no != 'nan' and item_no != '':
                    sfg_by_itemno[item_no] = sfg_by_itemno.get(item_no, 0) + closing
        
        debug.append(f"\n🔧 SFG Stock Analysis:")
        debug.append(f"   Unique SFG Batches: {len(sfg_by_batch):,}")
        debug.append(f"   Unique SFG Item Numbers: {len(sfg_by_itemno):,}")
        debug.append(f"   Total SFG Stock Quantity: {sum(sfg_by_batch.values()):,.0f}")
        
        # Show sample of SFG batches
        debug.append(f"\n📋 Sample SFG Batches Available:")
        for i, (batch, qty) in enumerate(list(sfg_by_batch.items())[:15]):
            details = sfg_batch_details.get(batch, {})
            debug.append(f"   Batch: '{batch}' → Qty: {qty:,.0f} (SFG Item: {details.get('item_no', 'N/A')})")
        
        # CRITICAL: Check which FG batches exist in SFG
        fg_batches_set = set(fg_batch_map.values())
        sfg_batches_set = set(sfg_by_batch.keys())
        common_batches = fg_batches_set & sfg_batches_set
        
        debug.append(f"\n🔗 Batch Matching Analysis:")
        debug.append(f"   Unique FG Batches: {len(fg_batches_set):,}")
        debug.append(f"   Unique SFG Batches: {len(sfg_batches_set):,}")
        debug.append(f"   Common Batches (FG batch exists in SFG): {len(common_batches):,}")
        
        if common_batches:
            debug.append(f"\n✅ Common Batches Sample (first 10):")
            for batch in list(common_batches)[:10]:
                fg_qty = sum([fg_stock.get(item, 0) for item, b in fg_batch_map.items() if b == batch])
                sfg_qty = sfg_by_batch.get(batch, 0)
                debug.append(f"   Batch '{batch}': FG Stock: {fg_qty:,.0f}, SFG Stock: {sfg_qty:,.0f}")
        
        # Process pending orders
        results = []
        matched_count = 0
        no_match_count = 0
        
        for _, row in pending_df.iterrows():
            item_no = str(row.get('ItemNo', '')).strip()
            bal_qty = float(row.get('BalQty', 0)) if pd.notna(row.get('BalQty', 0)) else 0
            cust_name = str(row.get('CustName', ''))
            item_desc = str(row.get('ItemDesc', ''))
            
            if item_no == 'nan' or not item_no:
                continue
            
            # Get FG stock
            fg_qty = fg_stock.get(item_no, 0)
            
            # Get batch for this FG
            fg_batch = fg_batch_map.get(item_no, '')
            
            # Find SFG stock by batch
            sfg_qty = sfg_by_batch.get(fg_batch, 0)
            sfg_item = ''
            sfg_batch_used = fg_batch if sfg_qty > 0 else ''
            
            if sfg_qty > 0:
                matched_count += 1
                details = sfg_batch_details.get(fg_batch, {})
                sfg_item = details.get('item_no', '')
            else:
                no_match_count += 1
            
            pending_qty = max(0, bal_qty - (fg_qty + sfg_qty))
            
            results.append({
                'cust_name': cust_name if cust_name != 'nan' else '',
                'item_no': item_no,
                'item_desc': item_desc[:150] if item_desc != 'nan' else '',
                'sfg_code': sfg_item,
                'fg_batch': fg_batch,
                'sfg_batch': sfg_batch_used,
                'bal_qty': int(bal_qty),
                'fg_stock': int(fg_qty),
                'sfg_stock': int(sfg_qty),
                'pending_qty': int(pending_qty)
            })
        
        # Statistics
        total_balance = sum(r['bal_qty'] for r in results)
        total_fg = sum(r['fg_stock'] for r in results)
        total_sfg = sum(r['sfg_stock'] for r in results)
        total_pending = sum(r['pending_qty'] for r in results)
        total_orders = len(results)
        
        # Top SFG items
        top_sfg = sorted([{'item_no': k, 'stock': v} for k, v in sfg_by_itemno.items()], 
                        key=lambda x: x['stock'], reverse=True)[:10]
        
        debug.append(f"\n{'='*80}")
        debug.append(f"📊 FINAL SUMMARY")
        debug.append(f"{'='*80}")
        debug.append(f"   ✅ FG Items with SFG Stock (Batch Match): {matched_count} ({matched_count/total_orders*100:.1f}%)")
        debug.append(f"   ❌ FG Items with NO SFG Stock: {no_match_count} ({no_match_count/total_orders*100:.1f}%)")
        debug.append(f"\n📈 INVENTORY:")
        debug.append(f"   Total Balance: {total_balance:,.0f}")
        debug.append(f"   Total FG Stock: {total_fg:,.0f}")
        debug.append(f"   Total SFG Stock: {total_sfg:,.0f}")
        debug.append(f"   🔴 PLANNING PENDING: {total_pending:,.0f}")
        
        debug.append(f"\n🔥 TOP SFG ITEMS BY STOCK:")
        for item in top_sfg[:10]:
            debug.append(f"   {item['item_no']}: {item['stock']:,.0f}")
        
        debug.append(f"\n{'='*80}")
        
        return jsonify({
            'success': True,
            'data': results,
            'debug': '\n'.join(debug),
            'total_orders': total_orders,
            'total_pending': total_pending,
            'total_balance': total_balance,
            'total_stock': total_fg + total_sfg,
            'matched_by_batch': matched_count,
            'no_match': no_match_count,
            'pending_count': len([r for r in results if r['pending_qty'] > 0]),
            'match_percentage': round((matched_count / total_orders) * 100, 1),
            'sfg_batch_count': len(sfg_by_batch),
            'top_sfg_items': top_sfg
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e) + '\n' + traceback.format_exc()
        debug.append(f"\n❌ ERROR: {error_msg}")
        return jsonify({'success': False, 'error': str(e), 'debug': '\n'.join(debug)})

@app.route('/download', methods=['POST'])
def download():
    data = request.json.get('data', [])
    df = pd.DataFrame(data)
    
    columns_order = ['cust_name', 'item_no', 'item_desc', 'sfg_code', 'fg_batch', 'sfg_batch', 
                     'bal_qty', 'fg_stock', 'sfg_stock', 'pending_qty']
    df = df[[c for c in columns_order if c in df.columns]]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Planning Pending', index=False)
        
        summary = pd.DataFrame({
            'Metric': ['Total Orders', 'Total Balance', 'Total FG Stock', 'Total SFG Stock', 'Total Planning Pending'],
            'Value': [len(df), df['bal_qty'].sum(), df['fg_stock'].sum(), df['sfg_stock'].sum(), df['pending_qty'].sum()]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return send_file(output, download_name='Planning_Pending_Report.xlsx', as_attachment=True)

def open_browser():
    import time
    time.sleep(2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 PRODUCTION PLANNING DASHBOARD - COMPLETE SFG VIEW")
    print("="*80)
    print("\n📌 Opening browser at: http://127.0.0.1:5000")
    print("\n⚠️  Keep this terminal open!")
    print("="*80 + "\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, host='127.0.0.1', port=5000)