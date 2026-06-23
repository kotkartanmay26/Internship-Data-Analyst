
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(
    page_title="Puja Fluid Seals - Enterprise Analytics",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #04152D 0%, #0A2A66 100%) !important;
}

[data-testid="stHeader"] {
    background: white !important;
    border-bottom: 1px solid #E5E7EB !important;
}

[data-testid="block-container"] {
    padding: 24px 32px !important;
    max-width: 100% !important;
}

.main {
    background-color: #F8FAFC !important;
}

.kpi-card {
    background: white;
    border-radius: 20px;
    padding: 28px 24px;
    border: 1px solid #F1F5F9;
    box-shadow: 0 8px 24px rgba(10,42,102,0.06);
}

.kpi-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 40px rgba(10,42,102,0.12);
    border-color: #DBEAFE;
}

.kpi-value {
    font-size: 40px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0A2A66 0%, #1E40AF 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
}

.kpi-label {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #475569 !important;
}

.chart-card {
    background: white;
    border-radius:20px;
    padding:32px;
    border:1px solid #F1F5F9;
    box-shadow:0 8px 24px rgba(10,42,102,0.06);
    margin-bottom:28px;
}

div.stButton > button {
    font-size:14px !important;
    font-weight:700 !important;
    padding:12px 20px !important;
    border-radius:12px !important;
    white-space: nowrap !important;
    width:100% !important;
}
</style>
""", unsafe_allow_html=True)

if 'selected_page' not in st.session_state:
    st.session_state.selected_page = 'home'
if 'processed_df' not in st.session_state:
    dates = pd.date_range(start='2026-05-24', end='2026-06-23', freq='D')
    data = {
        "Date": dates,
        "EmployeeID": [f"E{i:03d}" for i in range(1, len(dates)+1)],
        "Name": [f"Employee {i}" for i in range(1, len(dates)+1)],
        "Department": np.random.choice(["Production", "Quality", "Maintenance", "Toolroom", "HR", "Purchase"], size=len(dates)),
        "Present": np.random.randint(180, 220, len(dates)),
        "Absent": np.random.randint(5, 30, len(dates)),
        "Production": np.random.randint(1000, 5000, len(dates)),
        "Efficiency": np.random.uniform(75, 95, len(dates)),
        "SkillLevel": np.random.randint(50, 100, len(dates)),
        "Stock": np.random.randint(500, 2000, len(dates)),
    }
    st.session_state.processed_df = pd.DataFrame(data)

df = st.session_state.processed_df

with st.sidebar:
    st.markdown("<h2 style='color:white; text-align:center;'>🏭 Puja Fluid Seals</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; text-align:center; font-size:14px;'>Enterprise Analytics</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:24px 0;'>", unsafe_allow_html=True)
    
    nav_items = [
        ("home", "🏠", "Dashboard Overview"),
        ("employees", "👥", "Employee Dashboard"),
        ("attendance", "📊", "Attendance Dashboard"),
        ("production", "🏭", "Production Dashboard"),
        ("skills", "🎯", "Skill Matrix"),
        ("stock", "📦", "Stock Analysis"),
    ]
    
    for page_id, icon, text in nav_items:
        is_active = st.session_state.selected_page == page_id
        if st.button(
            f"{icon} {text}",
            key=f"nav_{page_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.selected_page = page_id
            st.rerun()

st.markdown("<h1 style='color:#0A2A66; font-size:36px; font-weight:900; margin-bottom:28px;'>Dashboard Overview</h1>", unsafe_allow_html=True)

top_cols = st.columns([2, 1, 1, 1, 1, 1])

with top_cols[0]:
    search_query = st.text_input("🔍 Search...", placeholder="Search employees, departments, skills...", key="search")
with top_cols[1]:
    uploaded_file = st.file_uploader("📤 Upload File", type=['xlsx', 'csv'], key="uploader")
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df_new = pd.read_csv(uploaded_file)
        else:
            df_new = pd.read_excel(uploaded_file)
        st.session_state.processed_df = df_new
        df = df_new
        st.success("✅ File loaded!")
with top_cols[2]:
    if st.button("🔄 Refresh", key="refresh", use_container_width=True):
        st.rerun()
with top_cols[3]:
    if st.button("⬇️ Download Excel", key="download", use_container_width=True):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        excel_data = output.getvalue()
        st.download_button(
            label="⬇️ Download Report",
            data=excel_data,
            file_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
with top_cols[4]:
    if st.button("📄 Export PDF", key="export_pdf", use_container_width=True):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        story.append(Paragraph("Puja Fluid Seals - Analytics Report", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['Normal']))
        story.append(Spacer(1,24))
        data = [df.columns.tolist()] + df.head(10).values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0A2A66')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0),12),
            ('GRID', (0,0), (-1,-1),1, colors.HexColor('#E5E7EB')),
        ]))
        story.append(table)
        doc.build(story)
        pdf_data = buffer.getvalue()
        st.download_button(
            label="📄 Download PDF",
            data=pdf_data,
            file_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
with top_cols[5]:
    st.markdown("<div style='text-align:right; padding:12px 0;'><b>Admin</b></div>", unsafe_allow_html=True)

if search_query:
    df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

st.markdown("<br>", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
total_records = len(df)
dept_count = df['Department'].nunique() if 'Department' in df.columns else 10
total_employees = df['EmployeeID'].nunique() if 'EmployeeID' in df.columns else total_records
avg_eff = df['Efficiency'].mean() if 'Efficiency' in df.columns else 85
att_pct = 87.5
if 'Present' in df.columns and 'Absent' in df.columns:
    att_pct = (df['Present'].mean() / (df['Present'].mean() + df['Absent'].mean()) *100)
total_prod = df['Production'].sum() if 'Production' in df.columns else 500000

kpi_data = [
    {"label":"Total Records", "value":f"{total_records:,}"},
    {"label":"Total Employees", "value":f"{total_employees:,}"},
    {"label":"Dept Count", "value":f"{dept_count}"},
    {"label":"Attendance %", "value":f"{round(att_pct,1)}%"},
    {"label":"Efficiency", "value":f"{round(avg_eff,1)}%"},
    {"label":"Production", "value":f"{total_prod:,}"},
]

for col, kpi in zip([kpi1, kpi2, kpi3, kpi4, kpi5, kpi6], kpi_data):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{kpi['label']}</div>
            <div class="kpi-value">{kpi['value']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

mid1, mid2, mid3 = st.columns([3, 2, 2])

with mid1:
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">Trend Analysis</h3>', unsafe_allow_html=True)
    cols_plot = [c for c in numeric_cols if c != 'EmployeeID'][:3]
    if cols_plot:
        if 'Date' in df.columns:
            fig = px.line(df, x='Date', y=cols_plot, template='plotly_white')
        else:
            fig = px.line(df, y=cols_plot, template='plotly_white')
        fig.update_layout(height=340, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with mid2:
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">Distribution</h3>', unsafe_allow_html=True)
    if 'Department' in df.columns:
        dist = df['Department'].value_counts().reset_index()
        dist.columns = ['Department', 'Count']
        fig2 = px.pie(dist, values='Count', names='Department', template='plotly_white', hole=0.65)
        fig2.update_layout(height=340, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with mid3:
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">Recent Data</h3>', unsafe_allow_html=True)
    st.dataframe(df.head(8), hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.selected_page == 'home':
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">Full Data Preview</h3>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">Statistics</h3>', unsafe_allow_html=True)
        if numeric_cols:
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
elif st.session_state.selected_page == 'employees':
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">👥 Employee Dashboard</h3>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
elif st.session_state.selected_page == 'attendance':
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">📊 Attendance Dashboard</h3>', unsafe_allow_html=True)
    if 'Present' in df.columns and 'Absent' in df.columns:
        fig_att = px.bar(df, y=['Present', 'Absent'], template='plotly_white')
        st.plotly_chart(fig_att, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
elif st.session_state.selected_page == 'production':
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">🏭 Production Dashboard</h3>', unsafe_allow_html=True)
    if 'Production' in df.columns:
        if 'Date' in df.columns:
            fig_prod = px.line(df, x='Date', y='Production', template='plotly_white')
        else:
            fig_prod = px.line(df, y='Production', template='plotly_white')
        st.plotly_chart(fig_prod, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
elif st.session_state.selected_page == 'skills':
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">🎯 Skill Matrix</h3>', unsafe_allow_html=True)
    if 'SkillLevel' in df.columns:
        fig_skill = px.histogram(df, x='SkillLevel', nbins=20, template='plotly_white')
        st.plotly_chart(fig_skill, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
elif st.session_state.selected_page == 'stock':
    st.markdown('<div class="chart-card"><h3 style="margin:0 0 20px 0; color:#0A2A66; font-size:24px; font-weight:800;">📦 Stock Analysis</h3>', unsafe_allow_html=True)
    if 'Stock' in df.columns:
        if 'Date' in df.columns:
            fig_stock = px.line(df, x='Date', y='Stock', template='plotly_white')
        else:
            fig_stock = px.line(df, y='Stock', template='plotly_white')
        st.plotly_chart(fig_stock, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

