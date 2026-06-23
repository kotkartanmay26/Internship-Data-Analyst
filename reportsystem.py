import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import io
import base64
from datetime import datetime
import tempfile
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import PDF libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("ERROR: reportlab not installed. Run: pip install reportlab")

# Try to import image libraries
try:
    import plotly.io as pio
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False
    print("WARNING: kaleido not installed. Run: pip install kaleido")

# Initial data
initial_data = {
    "Total Compounding Weight": 556.24,
    "Total Chemlok Applied Qty": 23814,
    "Total Metal Bush Production Qty": 790,
    "Total Production Qty-Molding": 37615,
    "Total Production Qty-CELLP": 210,
    "Total Online Deflashing Qty": 38247,
    "Total Parts Buffing Qty": 28790,
    "Total Parts Trimming Qty": 1180,
    "Total Cord Joining Qty": 3553,
    "Total Finishing Material Qty": 43042,
    "Total Employment": 211,
    "Present": 190,
    "Absent": 21,
    "Late": 22,
    "Efficiency Overall": 95.8,
    "Efficiency-Chemlok": 67,
    "Efficiency-Compounding": 95,
    "Efficiency-Toolroom": 99,
    "Efficiency-Molding": 92.53,
    "Total Energy Units Consumption": 1678.45,
    "Total Scrap-Rubber Weight": 171.72,
    "Total Km of Vehicles Run": 503,
    "Total Visitors": 2,
    "No Rubber Cutting Available": 15,
    "Die Cleaning Time": 15,
    "Machine Problem": 120,
    "Die Heating Delay": 30,
    "Machine Heating Delay": 60,
    "Machine Allotment Delay": 30,
    "Other": 245,
    "Inprocess Production-Molding": 583,
    "Inprocess Production-Chinmay": 7,
}

app = dash.Dash(__name__)

# Dark theme CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Production Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: #0a0c10;
                font-family: 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
            }
            .main-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                background: linear-gradient(135deg, #fff, #64ffda);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                text-align: center;
                color: #8b92a8;
                margin-bottom: 30px;
            }
            .input-group {
                margin-bottom: 15px;
            }
            .input-group label {
                display: block;
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 5px;
                font-weight: 500;
            }
            .input-group input {
                width: 100%;
                padding: 8px 12px;
                background: #1e1f2c;
                border: 1px solid #334155;
                color: #eef2ff;
                border-radius: 6px;
                font-size: 14px;
            }
            .grid-2 {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }
            .custom-tabs {
                background: #13161c;
                border-radius: 12px;
                padding: 10px;
                margin-bottom: 20px;
                border: 1px solid #2a2f3a;
            }
            .custom-tab {
                background: #1f2a3a !important;
                color: #94a3b8 !important;
                border: none !important;
                padding: 10px 20px !important;
                border-radius: 8px !important;
                margin: 0 5px !important;
            }
            .custom-tab--selected {
                background: #64ffda20 !important;
                color: #64ffda !important;
                border: 1px solid #64ffda !important;
            }
            .section-title {
                color: #64ffda;
                margin-bottom: 20px;
                font-size: 20px;
                border-left: 3px solid #64ffda;
                padding-left: 15px;
            }
            .upload-download-bar {
                background: #13161c;
                border-radius: 12px;
                padding: 15px 20px;
                margin-bottom: 20px;
                border: 1px solid #2a2f3a;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .upload-area {
                border: 2px dashed #64ffda;
                border-radius: 8px;
                padding: 10px;
                text-align: center;
                cursor: pointer;
                background: #1a1f2e;
            }
            .upload-area:hover {
                background: #64ffda10;
            }
            .btn-download {
                background: #64ffda20;
                color: #64ffda;
                border: 1px solid #64ffda;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                text-decoration: none;
                display: inline-block;
                margin-left: 10px;
            }
            .btn-download:hover {
                background: #64ffda40;
            }
            .file-name {
                color: #94a3b8;
                font-size: 12px;
                margin-top: 5px;
            }
            .btn-pdf {
                background: #ff444420;
                color: #ff4444;
                border: 1px solid #ff4444;
            }
            .loading-message {
                color: #64ffda;
                text-align: center;
                padding: 20px;
                font-size: 14px;
            }
        </style>
        {%app_entry%}
        {%config%}
        {%scripts%}
        {%renderer%}
    </head>
    <body>
    </body>
</html>
'''

# Main layout
app.layout = html.Div([
    html.Div([
        html.H1("🔧 Puja Fluid Seals Pvt. Ltd."),
        html.Div("Real-time Production Dashboard", className="subtitle"),
        
        # Upload/Download Bar
        html.Div([
            html.Div([
                dcc.Upload(
                    id="upload-excel",
                    children=html.Div([
                        html.Div("📂 Drag and Drop or Click to Upload Excel File"),
                        html.Div("Upload .xlsx or .xls file", style={"fontSize": "11px", "color": "#94a3b8"})
                    ]),
                    className="upload-area",
                    multiple=False,
                ),
                html.Div(id="upload-filename", className="file-name")
            ], style={"flex": "1"}),
            html.Div([
                html.A("📥 Download Excel", id="download-link", className="btn-download", href=""),
                html.Button("📄 Generate PDF Report", id="btn-generate-pdf", className="btn-download btn-pdf", n_clicks=0),
                html.Div(id="pdf-status", className="loading-message", style={"display": "none"})
            ])
        ], className="upload-download-bar"),
        
        dcc.Store(id="data-store", data=initial_data),
        dcc.Download(id="download-pdf"),
        
        # Tabs
        dcc.Tabs(id="tabs", value="tab-production", className="custom-tabs", children=[
            dcc.Tab(label="🏭 Production", value="tab-production", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="👥 Employment", value="tab-employment", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="📈 Efficiency", value="tab-efficiency", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="🔋 Utility", value="tab-utility", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="⏱️ Time Loss", value="tab-timeloss", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="⚠️ Rejection", value="tab-rejection", className="custom-tab", selected_className="custom-tab--selected"),
        ]),
        
        html.Div(id="tabs-content")
    ], className="main-container")
])

# Function to create all figures for PDF
def create_production_figure(data):
    fig = go.Figure(data=[
        go.Bar(name="Compounding", x=["Compounding"], y=[data.get("Total Compounding Weight", 0)], marker_color="#00b4d8"),
        go.Bar(name="Chemlok", x=["Chemlok"], y=[data.get("Total Chemlok Applied Qty", 0)], marker_color="#48cae4"),
        go.Bar(name="Metal Bush", x=["Metal Bush"], y=[data.get("Total Metal Bush Production Qty", 0)], marker_color="#90e0ef"),
        go.Bar(name="Molding", x=["Molding"], y=[data.get("Total Production Qty-Molding", 0)], marker_color="#64ffda"),
        go.Bar(name="CELLP", x=["CELLP"], y=[data.get("Total Production Qty-CELLP", 0)], marker_color="#ffb86b"),
        go.Bar(name="Deflashing", x=["Deflashing"], y=[data.get("Total Online Deflashing Qty", 0)], marker_color="#ff79c6"),
        go.Bar(name="Buffing", x=["Buffing"], y=[data.get("Total Parts Buffing Qty", 0)], marker_color="#8be9fd"),
        go.Bar(name="Finishing", x=["Finishing"], y=[data.get("Total Finishing Material Qty", 0)], marker_color="#50fa7b"),
    ])
    fig.update_layout(
        title="Production Metrics",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        showlegend=True,
        barmode='group',
        margin=dict(t=50, l=50, r=50, b=50)
    )
    return fig

def create_employment_figure(data):
    present = data.get("Present", 0)
    absent = data.get("Absent", 0)
    late = data.get("Late", 0)
    total = present + absent + late
    fig = go.Figure(data=[go.Pie(
        labels=['Present', 'Absent', 'Late'],
        values=[present, absent, late],
        hole=0.35,
        marker=dict(colors=['#2ecc71', '#e74c3c', '#f39c12']),
        textinfo="label+percent",
        textposition="inside"
    )])
    fig.update_layout(
        title=f"Employment Distribution (Total: {total})",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    return fig

def create_efficiency_figure(data):
    fig = go.Figure(data=[go.Bar(
        x=['Overall', 'Chemlok', 'Compounding', 'Toolroom', 'Molding'],
        y=[data.get("Efficiency Overall", 0), data.get("Efficiency-Chemlok", 0), 
           data.get("Efficiency-Compounding", 0), data.get("Efficiency-Toolroom", 0), 
           data.get("Efficiency-Molding", 0)],
        marker_color=['#64ffda', '#ffb86b', '#ff79c6', '#8be9fd', '#50fa7b'],
        text=[f"{data.get('Efficiency Overall', 0):.1f}%", f"{data.get('Efficiency-Chemlok', 0):.1f}%",
              f"{data.get('Efficiency-Compounding', 0):.1f}%", f"{data.get('Efficiency-Toolroom', 0):.1f}%",
              f"{data.get('Efficiency-Molding', 0):.1f}%"],
        textposition="outside",
        textfont=dict(color="black")
    )])
    fig.update_layout(
        title="Efficiency Metrics (%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        yaxis=dict(range=[0, 100], title="Percentage (%)", gridcolor="#e0e0e0"),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    return fig

def create_utility_figure(data):
    energy = data.get("Total Energy Units Consumption", 0)
    vehicle = data.get("Total Km of Vehicles Run", 0)
    visitors = data.get("Total Visitors", 0)
    scrap = data.get("Total Scrap-Rubber Weight", 0)
    comp_weight = data.get("Total Compounding Weight", 1)
    good_weight = max(comp_weight - scrap, 0)
    scrap_rate = (scrap / comp_weight * 100) if comp_weight > 0 else 0
    
    fig1 = go.Figure(data=[go.Bar(
        x=['Energy (kWh)', 'Vehicle (Km)', 'Visitors'],
        y=[energy, vehicle, visitors],
        marker_color=['#ffb347', '#9b59b6', '#1abc9c'],
        text=[f"{energy:.1f}", f"{vehicle}", f"{visitors}"],
        textposition="outside"
    )])
    fig1.update_layout(
        title="Resource Consumption",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    
    fig2 = go.Figure(data=[go.Pie(
        labels=['Good Parts (Kg)', 'Scrap (Kg)'],
        values=[good_weight, scrap],
        hole=0.4,
        marker=dict(colors=['#2ecc71', '#e74c3c']),
        textinfo="label+percent",
        textposition="inside"
    )])
    fig2.update_layout(
        title=f"Scrap Analysis (Rate: {scrap_rate:.1f}%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    
    return fig1, fig2

def create_timeloss_figure(data):
    labels = ['No Rubber', 'Die Clean', 'Machine', 'Die Heat', 'Machine Heat', 'Allotment', 'Other']
    values = [data.get("No Rubber Cutting Available", 0), data.get("Die Cleaning Time", 0),
              data.get("Machine Problem", 0), data.get("Die Heating Delay", 0),
              data.get("Machine Heating Delay", 0), data.get("Machine Allotment Delay", 0),
              data.get("Other", 0)]
    total = sum(values)
    
    fig = go.Figure(data=[go.Bar(
        x=labels, 
        y=values, 
        marker_color='#ff6b6b', 
        text=values, 
        textposition="outside",
        textfont=dict(color="black")
    )])
    fig.update_layout(
        title=f"Time Loss by Category (Total: {total} minutes / {total/60:.1f} hours)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50),
        xaxis=dict(tickangle=45)
    )
    return fig

def create_rejection_figure(data):
    molding_rej = data.get("Inprocess Production-Molding", 0)
    cellp_rej = data.get("Inprocess Production-Chinmay", 0)
    prod_qty = data.get("Total Production Qty-Molding", 1)
    good_parts = max(prod_qty - molding_rej, 0)
    rejection_rate = (molding_rej / prod_qty * 100) if prod_qty > 0 else 0
    
    fig1 = go.Figure(data=[go.Bar(
        x=['Molding', 'CELLP'],
        y=[molding_rej, cellp_rej],
        marker_color=['#ff4444', '#ff8888'],
        text=[f"{molding_rej:,}", f"{cellp_rej}"],
        textposition="outside"
    )])
    fig1.update_layout(
        title="Rejection by Process",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    
    fig2 = go.Figure(data=[go.Bar(
        x=['Production', 'Good Parts', 'Rejection'],
        y=[prod_qty, good_parts, molding_rej],
        marker_color=['#00b4d8', '#2ecc71', '#ff4444'],
        text=[f"{prod_qty:,}", f"{good_parts:,}", f"{molding_rej:,}"],
        textposition="outside"
    )])
    fig2.update_layout(
        title=f"Molding Analysis (Rejection Rate: {rejection_rate:.1f}%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", size=12),
        height=400,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    
    return fig1, fig2

# Function to save figure as image
def save_figure_as_image(fig, filename, width=800, height=400):
    """Save plotly figure as image using kaleido"""
    try:
        if KALEIDO_AVAILABLE:
            fig.write_image(filename, width=width, height=height, scale=2)
            return True
        else:
            print(f"Kaleido not available for {filename}")
            return False
    except Exception as e:
        print(f"Error saving {filename}: {str(e)}")
        return False

# PDF Generation Function with Graphs
def generate_pdf_with_graphs(data):
    """Generate PDF report with tables and graphs"""
    if not PDF_AVAILABLE:
        return None
    
    # Create temp directory for images
    temp_dir = tempfile.mkdtemp()
    images = {}
    
    try:
        print("Generating PDF with graphs...")
        
        # Create and save Production figure
        print("  - Creating production chart...")
        fig_prod = create_production_figure(data)
        prod_path = os.path.join(temp_dir, 'production.png')
        if save_figure_as_image(fig_prod, prod_path, 900, 450):
            images['production'] = prod_path
        
        # Create and save Employment figure
        print("  - Creating employment chart...")
        fig_emp = create_employment_figure(data)
        emp_path = os.path.join(temp_dir, 'employment.png')
        if save_figure_as_image(fig_emp, emp_path, 900, 450):
            images['employment'] = emp_path
        
        # Create and save Efficiency figure
        print("  - Creating efficiency chart...")
        fig_eff = create_efficiency_figure(data)
        eff_path = os.path.join(temp_dir, 'efficiency.png')
        if save_figure_as_image(fig_eff, eff_path, 900, 450):
            images['efficiency'] = eff_path
        
        # Create and save Utility figures
        print("  - Creating utility charts...")
        fig_util1, fig_util2 = create_utility_figure(data)
        util1_path = os.path.join(temp_dir, 'utility1.png')
        util2_path = os.path.join(temp_dir, 'utility2.png')
        save_figure_as_image(fig_util1, util1_path, 450, 400)
        save_figure_as_image(fig_util2, util2_path, 450, 400)
        if os.path.exists(util1_path):
            images['utility1'] = util1_path
        if os.path.exists(util2_path):
            images['utility2'] = util2_path
        
        # Create and save Time Loss figure
        print("  - Creating timeloss chart...")
        fig_loss = create_timeloss_figure(data)
        loss_path = os.path.join(temp_dir, 'timeloss.png')
        if save_figure_as_image(fig_loss, loss_path, 900, 450):
            images['timeloss'] = loss_path
        
        # Create and save Rejection figures
        print("  - Creating rejection charts...")
        fig_rej1, fig_rej2 = create_rejection_figure(data)
        rej1_path = os.path.join(temp_dir, 'rejection1.png')
        rej2_path = os.path.join(temp_dir, 'rejection2.png')
        save_figure_as_image(fig_rej1, rej1_path, 450, 400)
        save_figure_as_image(fig_rej2, rej2_path, 450, 400)
        if os.path.exists(rej1_path):
            images['rejection1'] = rej1_path
        if os.path.exists(rej2_path):
            images['rejection2'] = rej2_path
        
        # Create PDF
        print("  - Building PDF document...")
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4), 
                               rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, 
                                     textColor=colors.HexColor('#1a5f7a'), alignment=TA_CENTER, spaceAfter=20)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, 
                                       textColor=colors.HexColor('#1a5f7a'), spaceAfter=10, spaceBefore=15)
        section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=14, 
                                       textColor=colors.HexColor('#ff6b6b'), spaceAfter=8)
        
        story = []
        
        # Title Page
        story.append(Paragraph("PUJA FLUID SEALS PVT. LTD.", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Production Performance Report", 
                              ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER)))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y %H:%M:%S')}", 
                              ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)))
        story.append(Spacer(1, 30))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        
        total_emp = data.get("Total Employment", 0)
        present = data.get("Present", 0)
        attendance_rate = (present / total_emp * 100) if total_emp > 0 else 0
        overall_eff = data.get("Efficiency Overall", 0)
        scrap_rate = (data.get("Total Scrap-Rubber Weight", 0) / data.get("Total Compounding Weight", 1) * 100)
        rejection_rate = (data.get("Inprocess Production-Molding", 0) / data.get("Total Production Qty-Molding", 1) * 100)
        
        summary_data = [
            ['Key Performance Indicator', 'Value', 'Status'],
            ['Total Employment', f"{total_emp}", ''],
            ['Attendance Rate', f"{attendance_rate:.1f}%", '✓ Good' if attendance_rate >= 85 else '⚠️ Low'],
            ['Overall Efficiency', f"{overall_eff:.1f}%", '✓ Good' if overall_eff >= 90 else '⚠️ Low'],
            ['Scrap Rate', f"{scrap_rate:.1f}%", '✓ Good' if scrap_rate < 5 else '⚠️ High'],
            ['Rejection Rate', f"{rejection_rate:.1f}%", '✓ Good' if rejection_rate < 2 else '⚠️ High'],
            ['Total Production', f"{data.get('Total Production Qty-Molding', 0):,}", 'Units'],
            ['Energy Consumption', f"{data.get('Total Energy Units Consumption', 0):.1f}", 'kWh'],
        ]
        
        summary_table = Table(summary_data, colWidths=[160, 120, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Section 1: Production Activity
        story.append(PageBreak())
        story.append(Paragraph("1. PRODUCTION ACTIVITY REPORT", heading_style))
        story.append(Spacer(1, 10))
        
        prod_data = [
            ['Parameter', 'Quantity', 'Unit'],
            ['Total Compounding Weight', f"{data.get('Total Compounding Weight', 0):.2f}", 'Kg'],
            ['Total Chemlok Applied', f"{data.get('Total Chemlok Applied Qty', 0):,}", 'Nos'],
            ['Metal Bush Production', f"{data.get('Total Metal Bush Production Qty', 0):,}", 'Nos'],
            ['Molding Production', f"{data.get('Total Production Qty-Molding', 0):,}", 'Nos'],
            ['CELLP Production', f"{data.get('Total Production Qty-CELLP', 0):,}", 'Mtr'],
            ['Online Deflashing', f"{data.get('Total Online Deflashing Qty', 0):,}", 'Nos'],
            ['Parts Buffing', f"{data.get('Total Parts Buffing Qty', 0):,}", 'Nos'],
            ['Parts Trimming', f"{data.get('Total Parts Trimming Qty', 0):,}", 'Nos'],
            ['Cord Joining', f"{data.get('Total Cord Joining Qty', 0):,}", 'Nos'],
            ['Finishing Material', f"{data.get('Total Finishing Material Qty', 0):,}", 'Nos'],
        ]
        
        prod_table = Table(prod_data, colWidths=[180, 130, 80])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(prod_table)
        story.append(Spacer(1, 20))
        
        # Add Production Graph
        if 'production' in images:
            story.append(Paragraph("Production Visualization", section_style))
            story.append(Spacer(1, 5))
            story.append(Image(images['production'], width=750, height=350))
            story.append(Spacer(1, 20))
        
        # Section 2: Employment Status
        story.append(PageBreak())
        story.append(Paragraph("2. EMPLOYMENT & WORKFORCE", heading_style))
        story.append(Spacer(1, 10))
        
        absent = data.get("Absent", 0)
        late = data.get("Late", 0)
        emp_data = [
            ['Category', 'Count', 'Percentage'],
            ['Total Employment', f"{total_emp}", '100%'],
            ['Present', f"{present}", f"{(present/total_emp*100):.1f}%" if total_emp > 0 else '0%'],
            ['Absent', f"{absent}", f"{(absent/total_emp*100):.1f}%" if total_emp > 0 else '0%'],
            ['Late', f"{late}", f"{(late/total_emp*100):.1f}%" if total_emp > 0 else '0%'],
        ]
        
        emp_table = Table(emp_data, colWidths=[150, 100, 120])
        emp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(emp_table)
        story.append(Spacer(1, 20))
        
        # Add Employment Graph
        if 'employment' in images:
            story.append(Paragraph("Workforce Distribution", section_style))
            story.append(Spacer(1, 5))
            story.append(Image(images['employment'], width=750, height=350))
            story.append(Spacer(1, 20))
        
        # Section 3: Efficiency Metrics
        story.append(PageBreak())
        story.append(Paragraph("3. PERFORMANCE EFFICIENCY", heading_style))
        story.append(Spacer(1, 10))
        
        eff_data = [
            ['Department', 'Current Efficiency (%)', 'Target (%)', 'Gap'],
            ['Overall', f"{data.get('Efficiency Overall', 0):.1f}", '90', f"{data.get('Efficiency Overall', 0) - 90:.1f}"],
            ['Chemlok', f"{data.get('Efficiency-Chemlok', 0):.1f}", '85', f"{data.get('Efficiency-Chemlok', 0) - 85:.1f}"],
            ['Compounding', f"{data.get('Efficiency-Compounding', 0):.1f}", '90', f"{data.get('Efficiency-Compounding', 0) - 90:.1f}"],
            ['Toolroom', f"{data.get('Efficiency-Toolroom', 0):.1f}", '95', f"{data.get('Efficiency-Toolroom', 0) - 95:.1f}"],
            ['Molding', f"{data.get('Efficiency-Molding', 0):.1f}", '90', f"{data.get('Efficiency-Molding', 0) - 90:.1f}"],
        ]
        
        eff_table = Table(eff_data, colWidths=[140, 120, 80, 80])
        eff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(eff_table)
        story.append(Spacer(1, 20))
        
        # Add Efficiency Graph
        if 'efficiency' in images:
            story.append(Paragraph("Efficiency Comparison Chart", section_style))
            story.append(Spacer(1, 5))
            story.append(Image(images['efficiency'], width=750, height=350))
            story.append(Spacer(1, 20))
        
        # Section 4: Utility & Resources
        story.append(PageBreak())
        story.append(Paragraph("4. UTILITY & RESOURCES", heading_style))
        story.append(Spacer(1, 10))
        
        util_data = [
            ['Resource', 'Consumption', 'Unit/Notes'],
            ['Energy', f"{data.get('Total Energy Units Consumption', 0):.2f}", 'kWh'],
            ['Scrap Rubber', f"{data.get('Total Scrap-Rubber Weight', 0):.2f}", f'Kg (Rate: {scrap_rate:.1f}%)'],
            ['Vehicle Run', f"{data.get('Total Km of Vehicles Run', 0):,}", 'Km'],
            ['Visitors', f"{data.get('Total Visitors', 0)}", 'Persons'],
        ]
        
        util_table = Table(util_data, colWidths=[150, 120, 150])
        util_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(util_table)
        story.append(Spacer(1, 20))
        
        # Add Utility Graphs side by side
        if 'utility1' in images and 'utility2' in images:
            story.append(Paragraph("Resource Analysis Charts", section_style))
            story.append(Spacer(1, 5))
            from reportlab.platypus import Table as ReportLabTable
            side_by_side = ReportLabTable([[Image(images['utility1'], width=370, height=330), 
                                            Image(images['utility2'], width=370, height=330)]], 
                                           colWidths=[380, 380])
            story.append(side_by_side)
            story.append(Spacer(1, 20))
        
        # Section 5: Time Loss Analysis
        story.append(PageBreak())
        story.append(Paragraph("5. PRODUCTION TIME LOSS ANALYSIS", heading_style))
        story.append(Spacer(1, 10))
        
        total_loss = sum([
            data.get('No Rubber Cutting Available', 0),
            data.get('Die Cleaning Time', 0),
            data.get('Machine Problem', 0),
            data.get('Die Heating Delay', 0),
            data.get('Machine Heating Delay', 0),
            data.get('Machine Allotment Delay', 0),
            data.get('Other', 0)
        ])
        
        loss_data = [
            ['Loss Category', 'Minutes', 'Hours', '% of Total'],
            ['No Rubber/Cutting', f"{data.get('No Rubber Cutting Available', 0)}", f"{data.get('No Rubber Cutting Available', 0)/60:.1f}", ''],
            ['Die Cleaning', f"{data.get('Die Cleaning Time', 0)}", f"{data.get('Die Cleaning Time', 0)/60:.1f}", ''],
            ['Machine Problem', f"{data.get('Machine Problem', 0)}", f"{data.get('Machine Problem', 0)/60:.1f}", ''],
            ['Die Heating Delay', f"{data.get('Die Heating Delay', 0)}", f"{data.get('Die Heating Delay', 0)/60:.1f}", ''],
            ['Machine Heating Delay', f"{data.get('Machine Heating Delay', 0)}", f"{data.get('Machine Heating Delay', 0)/60:.1f}", ''],
            ['Machine Allotment', f"{data.get('Machine Allotment Delay', 0)}", f"{data.get('Machine Allotment Delay', 0)/60:.1f}", ''],
            ['Other', f"{data.get('Other', 0)}", f"{data.get('Other', 0)/60:.1f}", ''],
        ]
        
        for row in loss_data[1:]:
            if total_loss > 0:
                row[3] = f"{(int(row[1])/total_loss*100):.1f}%"
            else:
                row[3] = '0%'
        
        loss_data.append(['TOTAL', f"{total_loss}", f"{total_loss/60:.1f}", '100%'])
        
        loss_table = Table(loss_data, colWidths=[140, 80, 80, 80])
        loss_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFE5E5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-2, -2), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(loss_table)
        story.append(Spacer(1, 20))
        
        # Add Time Loss Graph
        if 'timeloss' in images:
            story.append(Paragraph("Time Loss Distribution", section_style))
            story.append(Spacer(1, 5))
            story.append(Image(images['timeloss'], width=750, height=350))
            story.append(Spacer(1, 20))
        
        # Section 6: Rejection Analysis
        story.append(PageBreak())
        story.append(Paragraph("6. REJECTION ANALYSIS", heading_style))
        story.append(Spacer(1, 10))
        
        molding_prod = data.get('Total Production Qty-Molding', 1)
        molding_rej = data.get('Inprocess Production-Molding', 0)
        good_parts = molding_prod - molding_rej
        rej_rate = (molding_rej / molding_prod * 100) if molding_prod > 0 else 0
        
        rej_data = [
            ['Parameter', 'Quantity', 'Percentage', 'Status'],
            ['Total Production', f"{molding_prod:,}", '100%', '-'],
            ['Good Parts', f"{good_parts:,}", f"{(good_parts/molding_prod*100):.1f}%" if molding_prod > 0 else '0%', 
             '✓ Good' if rej_rate < 2 else '⚠️ High'],
            ['Rejection', f"{molding_rej:,}", f"{rej_rate:.1f}%", '⚠️ High' if rej_rate > 2 else '✓ Good'],
            ['CELLP Rejection', f"{data.get('Inprocess Production-Chinmay', 0)}", '-', '-'],
        ]
        
        rej_table = Table(rej_data, colWidths=[150, 120, 100, 100])
        rej_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(rej_table)
        story.append(Spacer(1, 20))
        
        # Add Rejection Graphs side by side
        if 'rejection1' in images and 'rejection2' in images:
            story.append(Paragraph("Rejection Analysis Charts", section_style))
            story.append(Spacer(1, 5))
            from reportlab.platypus import Table as ReportLabTable
            rej_side_by_side = ReportLabTable([[Image(images['rejection1'], width=370, height=330), 
                                                Image(images['rejection2'], width=370, height=330)]], 
                                               colWidths=[380, 380])
            story.append(rej_side_by_side)
            story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"""
        <para alignment="center" fontSize="8" textColor="grey">
        Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Puja Fluid Seals Pvt. Ltd.<br/>
        This is a system-generated report. For queries, contact production department.
        </para>
        """
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        print("✅ PDF generated successfully with graphs!")
        return pdf_buffer
        
    except Exception as e:
        print(f"❌ PDF Generation Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Cleanup temp directory
        try:
            for file in images.values():
                if os.path.exists(file):
                    os.remove(file)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass

# PDF Generation Callback
@app.callback(
    Output("download-pdf", "data"),
    Output("pdf-status", "children"),
    Output("pdf-status", "style"),
    Input("btn-generate-pdf", "n_clicks"),
    State("data-store", "data"),
    prevent_initial_call=True
)
def generate_pdf_callback(n_clicks, data):
    if n_clicks and n_clicks > 0:
        if not PDF_AVAILABLE:
            return None, "❌ Error: reportlab not installed. Run: pip install reportlab", {"display": "block", "color": "#ff4444", "background": "#1a1f2e", "borderRadius": "8px", "padding": "10px", "marginTop": "10px"}
        
        if not KALEIDO_AVAILABLE:
            return None, "⚠️ Warning: kaleido not installed. Install with: pip install kaleido", {"display": "block", "color": "#ffb86b", "background": "#1a1f2e", "borderRadius": "8px", "padding": "10px", "marginTop": "10px"}
        
        try:
            print(f"\n{'='*50}")
            print(f"PDF Generation Started at {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*50}")
            
            pdf_buffer = generate_pdf_with_graphs(data)
            
            if pdf_buffer:
                filename = f"Production_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                print(f"✅ PDF Ready: {filename}")
                return dcc.send_bytes(pdf_buffer.getvalue(), filename), "✅ PDF Generated Successfully with Charts!", {"display": "block", "color": "#64ffda", "background": "#1a1f2e", "borderRadius": "8px", "padding": "10px", "marginTop": "10px"}
            else:
                return None, "❌ Error: Failed to generate PDF", {"display": "block", "color": "#ff4444", "background": "#1a1f2e", "borderRadius": "8px", "padding": "10px", "marginTop": "10px"}
                
        except Exception as e:
            print(f"❌ PDF Callback Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, f"❌ Error: {str(e)[:100]}", {"display": "block", "color": "#ff4444", "background": "#1a1f2e", "borderRadius": "8px", "padding": "10px", "marginTop": "10px"}
    
    return None, "", {"display": "none"}

# Excel Upload Callback
@app.callback(
    [Output("data-store", "data"), Output("upload-filename", "children")],
    Input("upload-excel", "contents"),
    State("upload-excel", "filename"),
    prevent_initial_call=True
)
def upload_excel(contents, filename):
    if contents:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_excel(io.BytesIO(decoded))
            
            uploaded_data = {}
            for col in df.columns:
                if len(df) > 0:
                    value = df.iloc[0][col]
                    if pd.notna(value):
                        uploaded_data[str(col)] = float(value) if isinstance(value, (int, float)) else value
            
            merged_data = initial_data.copy()
            merged_data.update(uploaded_data)
            return merged_data, f"✅ Loaded: {filename}"
        except Exception as e:
            return initial_data, f"❌ Error loading file: {str(e)[:50]}"
    return initial_data, "No file uploaded"

# Excel Download Callback
@app.callback(
    Output("download-link", "href"),
    Input("data-store", "data")
)
def download_excel(data):
    df = pd.DataFrame(list(data.items()), columns=['Parameter', 'Value'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Production Data', index=False)
    output.seek(0)
    excel_data = base64.b64encode(output.getvalue()).decode()
    return f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_data}"

# Tab Content Callback
@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value"),
    State("data-store", "data")
)
def render_content(tab, data):
    if not data:
        data = initial_data
    
    if tab == "tab-production":
        return html.Div([
            html.H3("Production Activity", className="section-title"),
            html.Div([
                html.Div([html.Label("Compounding Weight (Kg)"), dcc.Input(id="p1", type="number", value=data.get("Total Compounding Weight", 0))], className="input-group"),
                html.Div([html.Label("Chemlok Applied"), dcc.Input(id="p2", type="number", value=data.get("Total Chemlok Applied Qty", 0))], className="input-group"),
                html.Div([html.Label("Metal Bush"), dcc.Input(id="p3", type="number", value=data.get("Total Metal Bush Production Qty", 0))], className="input-group"),
                html.Div([html.Label("Molding Production"), dcc.Input(id="p4", type="number", value=data.get("Total Production Qty-Molding", 0))], className="input-group"),
                html.Div([html.Label("CELLP Production"), dcc.Input(id="p5", type="number", value=data.get("Total Production Qty-CELLP", 0))], className="input-group"),
                html.Div([html.Label("Deflashing Qty"), dcc.Input(id="p6", type="number", value=data.get("Total Online Deflashing Qty", 0))], className="input-group"),
                html.Div([html.Label("Buffing Qty"), dcc.Input(id="p7", type="number", value=data.get("Total Parts Buffing Qty", 0))], className="input-group"),
                html.Div([html.Label("Finishing Material"), dcc.Input(id="p8", type="number", value=data.get("Total Finishing Material Qty", 0))], className="input-group"),
            ], className="grid-2"),
            dcc.Graph(id="prod-graph")
        ])
    
    elif tab == "tab-employment":
        return html.Div([
            html.H3("Employment Status", className="section-title"),
            html.Div([
                html.Div([html.Label("Total Employment"), dcc.Input(id="e1", type="number", value=data.get("Total Employment", 0))], className="input-group"),
                html.Div([html.Label("Present"), dcc.Input(id="e2", type="number", value=data.get("Present", 0))], className="input-group"),
                html.Div([html.Label("Absent"), dcc.Input(id="e3", type="number", value=data.get("Absent", 0))], className="input-group"),
                html.Div([html.Label("Late"), dcc.Input(id="e4", type="number", value=data.get("Late", 0))], className="input-group"),
            ], className="grid-2"),
            dcc.Graph(id="emp-graph")
        ])
    
    elif tab == "tab-efficiency":
        return html.Div([
            html.H3("Efficiency Metrics", className="section-title"),
            html.Div([
                html.Div([html.Label("Overall Efficiency (%)"), dcc.Input(id="ef1", type="number", value=data.get("Efficiency Overall", 0))], className="input-group"),
                html.Div([html.Label("Chemlok Efficiency (%)"), dcc.Input(id="ef2", type="number", value=data.get("Efficiency-Chemlok", 0))], className="input-group"),
                html.Div([html.Label("Compounding Efficiency (%)"), dcc.Input(id="ef3", type="number", value=data.get("Efficiency-Compounding", 0))], className="input-group"),
                html.Div([html.Label("Toolroom Efficiency (%)"), dcc.Input(id="ef4", type="number", value=data.get("Efficiency-Toolroom", 0))], className="input-group"),
                html.Div([html.Label("Molding Efficiency (%)"), dcc.Input(id="ef5", type="number", value=data.get("Efficiency-Molding", 0))], className="input-group"),
            ], className="grid-2"),
            dcc.Graph(id="eff-graph")
        ])
    
    elif tab == "tab-utility":
        return html.Div([
            html.H3("Utility & Resources", className="section-title"),
            html.Div([
                html.Div([html.Label("Energy (kWh)"), dcc.Input(id="u1", type="number", value=data.get("Total Energy Units Consumption", 0))], className="input-group"),
                html.Div([html.Label("Scrap Weight (Kg)"), dcc.Input(id="u2", type="number", value=data.get("Total Scrap-Rubber Weight", 0))], className="input-group"),
                html.Div([html.Label("Vehicle Run (Km)"), dcc.Input(id="u3", type="number", value=data.get("Total Km of Vehicles Run", 0))], className="input-group"),
                html.Div([html.Label("Visitors"), dcc.Input(id="u4", type="number", value=data.get("Total Visitors", 0))], className="input-group"),
            ], className="grid-2"),
            dcc.Graph(id="util-graph")
        ])
    
    elif tab == "tab-timeloss":
        return html.Div([
            html.H3("Time Loss Analysis", className="section-title"),
            html.Div([
                html.Div([html.Label("No Rubber (min)"), dcc.Input(id="t1", type="number", value=data.get("No Rubber Cutting Available", 0))], className="input-group"),
                html.Div([html.Label("Die Cleaning (min)"), dcc.Input(id="t2", type="number", value=data.get("Die Cleaning Time", 0))], className="input-group"),
                html.Div([html.Label("Machine Problem (min)"), dcc.Input(id="t3", type="number", value=data.get("Machine Problem", 0))], className="input-group"),
                html.Div([html.Label("Die Heating (min)"), dcc.Input(id="t4", type="number", value=data.get("Die Heating Delay", 0))], className="input-group"),
                html.Div([html.Label("Machine Heating (min)"), dcc.Input(id="t5", type="number", value=data.get("Machine Heating Delay", 0))], className="input-group"),
                html.Div([html.Label("Allotment Delay (min)"), dcc.Input(id="t6", type="number", value=data.get("Machine Allotment Delay", 0))], className="input-group"),
                html.Div([html.Label("Other (min)"), dcc.Input(id="t7", type="number", value=data.get("Other", 0))], className="input-group"),
            ], className="grid-2"),
            dcc.Graph(id="loss-graph")
        ])
    
    else:
        return html.Div([
            html.H3("Rejection Analysis", className="section-title"),
            html.Div([
                html.Div([html.Label("Molding Rejection"), dcc.Input(id="r1", type="number", value=data.get("Inprocess Production-Molding", 0))], className="input-group"),
                html.Div([html.Label("CELLP Rejection"), dcc.Input(id="r2", type="number", value=data.get("Inprocess Production-Chinmay", 0))], className="input-group"),
                html.Div([html.Label("Total Production"), dcc.Input(id="r3", type="number", value=data.get("Total Production Qty-Molding", 0))], className="input-group"),
            ], className="grid-2"),
            dcc.Graph(id="rej-graph")
        ])

# Graph Callbacks
@app.callback(
    Output("prod-graph", "figure"),
    [Input("p1", "value"), Input("p2", "value"), Input("p3", "value"),
     Input("p4", "value"), Input("p5", "value"), Input("p6", "value"),
     Input("p7", "value"), Input("p8", "value")]
)
def update_prod(p1,p2,p3,p4,p5,p6,p7,p8):
    fig = go.Figure(data=[
        go.Bar(name="Compounding", x=["Compounding"], y=[p1 or 0], marker_color="#64ffda"),
        go.Bar(name="Chemlok", x=["Chemlok"], y=[p2 or 0], marker_color="#48cae4"),
        go.Bar(name="Metal Bush", x=["Metal Bush"], y=[p3 or 0], marker_color="#90e0ef"),
        go.Bar(name="Molding", x=["Molding"], y=[p4 or 0], marker_color="#ffb86b"),
        go.Bar(name="CELLP", x=["CELLP"], y=[p5 or 0], marker_color="#ff79c6"),
        go.Bar(name="Deflashing", x=["Deflashing"], y=[p6 or 0], marker_color="#8be9fd"),
        go.Bar(name="Buffing", x=["Buffing"], y=[p7 or 0], marker_color="#50fa7b"),
        go.Bar(name="Finishing", x=["Finishing"], y=[p8 or 0], marker_color="#f1fa8c"),
    ])
    fig.update_layout(title="Production Metrics", plot_bgcolor="#13161c", paper_bgcolor="#13161c", font=dict(color="white"), height=500)
    return fig

@app.callback(
    Output("emp-graph", "figure"),
    [Input("e1", "value"), Input("e2", "value"), Input("e3", "value"), Input("e4", "value")]
)
def update_emp(e1,e2,e3,e4):
    fig = go.Figure(data=[go.Pie(labels=['Present', 'Absent', 'Late'], values=[e2 or 0, e3 or 0, e4 or 0], hole=0.3)])
    fig.update_layout(title=f"Employment (Total: {e1 or 0})", plot_bgcolor="#13161c", paper_bgcolor="#13161c", font=dict(color="white"), height=500)
    return fig

@app.callback(
    Output("eff-graph", "figure"),
    [Input("ef1", "value"), Input("ef2", "value"), Input("ef3", "value"), Input("ef4", "value"), Input("ef5", "value")]
)
def update_eff(ef1,ef2,ef3,ef4,ef5):
    fig = go.Figure(data=[go.Bar(x=['Overall', 'Chemlok', 'Compounding', 'Toolroom', 'Molding'], 
                                 y=[ef1 or 0, ef2 or 0, ef3 or 0, ef4 or 0, ef5 or 0],
                                 marker_color=['#64ffda', '#ffb86b', '#ff79c6', '#8be9fd', '#50fa7b'])])
    fig.update_layout(title="Efficiency Metrics (%)", plot_bgcolor="#13161c", paper_bgcolor="#13161c", 
                      font=dict(color="white"), yaxis=dict(range=[0, 100]), height=500)
    return fig

@app.callback(
    Output("util-graph", "figure"),
    [Input("u1", "value"), Input("u2", "value"), Input("u3", "value"), Input("u4", "value")]
)
def update_util(u1,u2,u3,u4):
    fig = go.Figure(data=[
        go.Bar(x=['Energy (kWh)', 'Vehicle (Km)', 'Visitors'], y=[u1 or 0, u3 or 0, u4 or 0], 
               marker_color=['#ffb347', '#9b59b6', '#1abc9c'])
    ])
    fig.update_layout(title="Resource Consumption", plot_bgcolor="#13161c", paper_bgcolor="#13161c", 
                      font=dict(color="white"), height=500)
    return fig

@app.callback(
    Output("loss-graph", "figure"),
    [Input("t1", "value"), Input("t2", "value"), Input("t3", "value"),
     Input("t4", "value"), Input("t5", "value"), Input("t6", "value"), Input("t7", "value")]
)
def update_loss(t1,t2,t3,t4,t5,t6,t7):
    labels = ['No Rubber', 'Die Clean', 'Machine', 'Die Heat', 'Machine Heat', 'Allotment', 'Other']
    values = [t1 or 0, t2 or 0, t3 or 0, t4 or 0, t5 or 0, t6 or 0, t7 or 0]
    fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color='#ff6b6b')])
    fig.update_layout(title="Time Loss Analysis", plot_bgcolor="#13161c", paper_bgcolor="#13161c", font=dict(color="white"), height=500)
    return fig

@app.callback(
    Output("rej-graph", "figure"),
    [Input("r1", "value"), Input("r2", "value"), Input("r3", "value")]
)
def update_rej(r1,r2,r3):
    fig = go.Figure(data=[go.Bar(x=['Molding Rejection', 'CELLP Rejection'], y=[r1 or 0, r2 or 0], 
                                  marker_color=['#ff4444', '#ff8888'])])
    fig.update_layout(title="Rejection Analysis", plot_bgcolor="#13161c", paper_bgcolor="#13161c", 
                      font=dict(color="white"), height=500)
    return fig

# Update data store when inputs change
@app.callback(
    Output("data-store", "data", allow_duplicate=True),
    [Input("p1", "value"), Input("p2", "value"), Input("p3", "value"), Input("p4", "value"),
     Input("p5", "value"), Input("p6", "value"), Input("p7", "value"), Input("p8", "value"),
     Input("e1", "value"), Input("e2", "value"), Input("e3", "value"), Input("e4", "value"),
     Input("ef1", "value"), Input("ef2", "value"), Input("ef3", "value"), Input("ef4", "value"), Input("ef5", "value"),
     Input("u1", "value"), Input("u2", "value"), Input("u3", "value"), Input("u4", "value"),
     Input("t1", "value"), Input("t2", "value"), Input("t3", "value"), Input("t4", "value"),
     Input("t5", "value"), Input("t6", "value"), Input("t7", "value"),
     Input("r1", "value"), Input("r2", "value"), Input("r3", "value")],
    State("data-store", "data"),
    prevent_initial_call=True
)
def update_store(p1,p2,p3,p4,p5,p6,p7,p8,e1,e2,e3,e4,ef1,ef2,ef3,ef4,ef5,
                 u1,u2,u3,u4,t1,t2,t3,t4,t5,t6,t7,r1,r2,r3, current_data):
    current_data.update({
        "Total Compounding Weight": p1 or 0, "Total Chemlok Applied Qty": p2 or 0,
        "Total Metal Bush Production Qty": p3 or 0, "Total Production Qty-Molding": p4 or 0,
        "Total Production Qty-CELLP": p5 or 0, "Total Online Deflashing Qty": p6 or 0,
        "Total Parts Buffing Qty": p7 or 0, "Total Finishing Material Qty": p8 or 0,
        "Total Employment": e1 or 0, "Present": e2 or 0, "Absent": e3 or 0, "Late": e4 or 0,
        "Efficiency Overall": ef1 or 0, "Efficiency-Chemlok": ef2 or 0, "Efficiency-Compounding": ef3 or 0,
        "Efficiency-Toolroom": ef4 or 0, "Efficiency-Molding": ef5 or 0,
        "Total Energy Units Consumption": u1 or 0, "Total Scrap-Rubber Weight": u2 or 0,
        "Total Km of Vehicles Run": u3 or 0, "Total Visitors": u4 or 0,
        "No Rubber Cutting Available": t1 or 0, "Die Cleaning Time": t2 or 0, "Machine Problem": t3 or 0,
        "Die Heating Delay": t4 or 0, "Machine Heating Delay": t5 or 0, "Machine Allotment Delay": t6 or 0,
        "Other": t7 or 0, "Inprocess Production-Molding": r1 or 0, "Inprocess Production-Chinmay": r2 or 0,
    })
    return current_data

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 PRODUCTION DASHBOARD STARTING...")
    print("📊 Open: http://127.0.0.1:8050")
    print("=" * 60)
    print("\n🔧 Required packages for PDF with graphs:")
    print("   pip install reportlab kaleido")
    print("=" * 60)
    
    if not KALEIDO_AVAILABLE:
        print("⚠️ WARNING: kaleido not installed - PDF charts will NOT work")
        print("   Fix: pip install kaleido")
    if not PDF_AVAILABLE:
        print("⚠️ WARNING: reportlab not installed - PDF generation disabled")
        print("   Fix: pip install reportlab")
    
    print("\n✅ All dashboard features working!")
    print("📄 PDF button will generate report with both tables AND graphs")
    print("=" * 60)
    
    app.run(debug=True, port=8050)