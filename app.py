
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64
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
&lt;style&gt;
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&amp;display=swap');

* {
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #04152D 0%, #0A2A66 100%) !important;
    min-width: 280px !important;
    max-width: 340px !important;
    border-right: 1px solid rgba(255,255,255,0.1) !important;
}

[data-testid="stHeader"] {
    background: white !important;
    border-bottom: 1px solid #E5E7EB !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
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
    transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
}

.kpi-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 40px rgba(10,42,102,0.12);
    border-color: #DBEAFE;
}

.kpi-value {
    font-size: clamp(28px,4vw,44px) !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0A2A66 0%, #1E40AF 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    margin:14px 0 8px !important;
}

.kpi-label {
    font-size: clamp(14px, 1.8vw,17px) !important;
    font-weight: 700 !important;
    color: #475569 !important;
    text-transform:none;
}

.kpi-trend {
    font-size:14px !important;
    font-weight:700 !important;
}

.chart-card {
    background: white;
    border-radius:20px;
    padding:32px;
    border:1px solid #F1F5F9;
    box-shadow:0 8px 24px rgba(10,42,102,0.06);
    margin-bottom: 28px;
}

.chart-title {
    font-size: clamp(18px, 2.5vw,24px) !important;
    font-weight:800 !important;
    color:#0A2A66 !important;
    margin-bottom: 24px !important;
    letter-spacing: -0.3px;
}

div.stButton &gt; button {
    font-size:14px !important;
    font-weight:700 !important;
    padding:12px 20px !important;
    border-radius:12px !important;
    transition: all 0.25s ease !important;
    white-space: nowrap !important;
    width:100% !important;
    min-width:140px !important;
}

[data-testid="stDataFrame"] {
    font-size:13px !important;
}

[data-testid="stDataFrame"] th {
    font-size:14px !important;
    font-weight:800 !important;
    color:#0A2A66 !important;
    background:#F8FAFC !important;
    padding:14px 18px !important;
}

[data-testid="stDataFrame"] td {
    padding:14px 18px !important;
}

.sidebar-logo {
    width:56px;
    height:56px;
    border-radius:14px;
    background:linear-gradient(135deg,#2563EB 0%,#0A2A66 100%);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:30px;
    color:white;
    box-shadow:0 12px 32px rgba(37,99,235,0.35);
}

.quick-action-card {
    background: linear-gradient(135deg,#F8FAFC 0%,#F1F5F9 100%);
    border-radius:18px;
    padding:24px 18px;
    border:1px solid #E2E8F0;
    text-align:center;
    transition: all 0.3s ease;
    cursor: pointer;
}

.quick-action-card:hover {
    transform: translateY(-4px);
    box-shadow:0 16px 32px rgba(0,0,0,0.08);
    border-color:#2563EB;
}

.quick-action-icon {
    font-size:36px;
    margin-bottom:12px;
}

.quick-action-text {
    font-size:14px;
    font-weight:800;
    color:#0A2A66;
}

@media (max-width: 1400px) {
    [data-testid="block-container"] {
        padding:20px 24px !important;
    }
    .chart-card { padding:28px; }
}

@media (max-width: 1024px) {
    [data-testid="block-container"] {
        padding:16px 20px !important;
    }
}
&lt;/style&gt;
""", unsafe_allow_html=True)

# Session state initialization
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = 'home'
if 'uploaded_df' not in st.session_state:
    st.session_state.uploaded_df = None
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None

# Mock data function (default if no file uploaded)
def load_mock_data():
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
    return pd.DataFrame(data)

# Load default data if nothing uploaded
if st.session_state.processed_df is None:
    st.session_state.processed_df = load_mock_data()
    st.session_state.uploaded_df = st.session_state.processed_df.copy()

df = st.session_state.processed_df

with st.sidebar:
    st.markdown("""
    &lt;div style="
        padding:28px 24px;
        display:flex;
        align-items:center;
        gap:18px;
        border-bottom:1px solid rgba(255,255,255,0.1);
        margin:-28px -24px 28px -24px;
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
    "&gt;
        &lt;div class="sidebar-logo"&gt;🏭&lt;/div&gt;
        &lt;div&gt;
            &lt;h2 style="margin:0; font-size:20px; font-weight:800; color:white;"&gt;Puja Fluid Seals&lt;/h2&gt;
            &lt;p style="margin:8px 0 0; font-size:14px; color:#94A3B8; font-weight:600;"&gt;Pvt. Ltd.&lt;/p&gt;
        &lt;/div&gt;
    &lt;/div&gt;
    """, unsafe_allow_html=True)
    
    st.markdown("""
    &lt;div style="padding:0 12px 16px;"&gt;
        &lt;p style="color:#64748B; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin:0;"&gt;Main Menu&lt;/p&gt;
    &lt;/div&gt;
    """, unsafe_allow_html=True)
    
    nav_items = [
        ("home", "🏠", "Dashboard Overview"),
        ("employees", "👥", "Employee Dashboard"),
        ("attendance", "📊", "Attendance Dashboard"),
        ("production", "🏭", "Production Dashboard"),
        ("skills", "🎯", "Skill Matrix"),
        ("stock", "📦", "Stock Analysis"),
        ("toolroom", "🔧", "Toolroom Dashboard"),
        ("profit", "💰", "Profit Analysis"),
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
    
    st.markdown("""
    &lt;div style="padding:24px 12px 0; border-top:1px solid rgba(255,255,255,0.1); margin-top:28px;"&gt;
        &lt;p style="color:#64748B; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin:0 0 16px 0;"&gt;System&lt;/p&gt;
        &lt;div style="display:flex; align-items:center; gap:12px; padding:16px 20px; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.35); border-radius:14px; margin-bottom:20px;"&gt;
            &lt;span style="width:14px; height:14px; border-radius:50%; background:#22C55E; box-shadow:0 0 0 6px rgba(34,197,94,0.25);"&gt;&lt;/span&gt;
            &lt;span style="font-size:15px; color:#86EFAC; font-weight:800;"&gt;All Systems Operational&lt;/span&gt;
        &lt;/div&gt;
        &lt;div style="padding-top:20px; border-top:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.7); font-size:14px; font-weight:600;"&gt;
            &lt;p style="margin:0 0 6px;"&gt;© 2024 Puja Fluid Seals Pvt. Ltd.&lt;/p&gt;
            &lt;p style="margin:0; opacity:0.8;"&gt;All rights reserved.&lt;/p&gt;
        &lt;/div&gt;
    &lt;/div&gt;
    """, unsafe_allow_html=True)

header_col1, header_col2 = st.columns([1.2,3])
with header_col1:
    st.markdown("""
    &lt;div&gt;
        &lt;h1 style="margin:0; font-size: clamp(30px,3.5vw,42px); font-weight:900; color:#0A2A66; letter-spacing:-0.5px;"&gt;Dashboard Overview&lt;/h1&gt;
        &lt;p style="margin:10px 0 0; font-size:17px; color:#64748B; font-weight:600;"&gt;Home • Overview&lt;/p&gt;
    &lt;/div&gt;
    """, unsafe_allow_html=True)

with header_col2:
    search_col, upload_col, refresh_col, download_col, export_col, notif_col, profile_col = st.columns([1.8,1.2,1,1,1,0.8,1])
    
    with search_col:
        search_query = st.text_input(
            "🔍 Search employees, departments, skills, reports...",
            placeholder="🔍 Search...",
            key="global_search",
            label_visibility="collapsed"
        )
    
    with upload_col:
        uploaded_file = st.file_uploader(
            "📤 Upload", 
            type=['xlsx', 'csv', 'xls'],
            key="file_upload",
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    new_df = pd.read_csv(uploaded_file)
                else:
                    new_df = pd.read_excel(uploaded_file)
                st.session_state.uploaded_df = new_df
                st.session_state.processed_df = new_df
                st.success("✅ File uploaded and processed!")
                df = new_df
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
    
    with refresh_col:
        if st.button("🔄 Refresh", key="refresh_header", use_container_width=True):
            if st.session_state.uploaded_df is not None:
                st.session_state.processed_df = st.session_state.uploaded_df.copy()
            df = st.session_state.processed_df
            st.success("✅ Data refreshed!")
            st.rerun()
    
    with download_col:
        if st.button("⬇️ Download", key="download_header", use_container_width=True):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
            excel_data = output.getvalue()
            st.download_button(
                label="⬇️ Download Excel Report",
                data=excel_data,
                file_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with export_col:
        if st.button("📤 Export PDF", key="export_header", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            story.append(Paragraph("Puja Fluid Seals - Analytics Report", styles['Title']))
            story.append(Spacer(1,12))
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
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
            ]))
            story.append(table)
            doc.build(story)
            pdf_data = buffer.getvalue()
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name=f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
    
    with notif_col:
        st.button("🔔", key="notifications", use_container_width=True)
    
    with profile_col:
        st.markdown("""
        &lt;div style="
            display:flex; align-items:center; gap:14px;
            padding:12px 20px; background:linear-gradient(135deg,#F8FAFC 0%,#F1F5F9 100%);
            border:1px solid #E2E8F0; border-radius:16px; justify-content:center;
        "&gt;
            &lt;div style="width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,#2563EB 0%,#0A2A66 100%);
                display:flex; align-items:center; justify-content:center; color:white;
                font-size:22px; font-weight:900;"&gt;A&lt;/div&gt;
            &lt;div style="text-align:left;"&gt;
                &lt;p style="margin:0; font-size:16px; font-weight:900; color:#0A2A66;"&gt;Admin&lt;/p&gt;
                &lt;p style="margin:3px 0 0; font-size:13px; color:#64748B; font-weight:600;"&gt;Administrator&lt;/p&gt;
            &lt;/div&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)

st.markdown("&lt;div style='height:36px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)

if search_query:
    df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

# Page rendering
if st.session_state.selected_page == "home":
    # KPI Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    total_records = len(df)
    dept_count = df['Department'].nunique() if 'Department' in df.columns else 10
    total_employees = df['EmployeeID'].nunique() if 'EmployeeID' in df.columns else total_records
    
    avg_efficiency = np.mean(df[numeric_cols].mean()) if numeric_cols else 85
    avg_efficiency = round(avg_efficiency, 1) if avg_efficiency else 85
    
    total_production = df['Production'].sum() if 'Production' in df.columns else 500000
    attendance_pct = (df['Present'].mean() / (df['Present'].mean() + df['Absent'].mean()) * 100) if ('Present' in df.columns and 'Absent' in df.columns) else 87.5
    
    kpi_items = [
        {"label":"Total Records", "value":f"{total_records:,}", "trend":"up", "percent":"12.5%", "icon":"📋", "bg":"#EFF6FF", "color":"#1E40AF"},
        {"label":"Total Employees", "value":f"{total_employees:,}", "trend":"up", "percent":"15.8%", "icon":"👥", "bg":"#F0FDF4", "color":"#166534"},
        {"label":"Department Count", "value":f"{dept_count}", "trend":"neutral", "percent":"No change", "icon":"🏢", "bg":"#F5F3FF", "color":"#5B21B6"},
        {"label":"Attendance %", "value":f"{round(attendance_pct,1)}%", "trend":"up", "percent":"3.2%", "icon":"📊", "bg":"#FFF7ED", "color":"#9A3412"},
        {"label":"Efficiency", "value":f"{avg_efficiency}%", "trend":"up", "percent":"5.6%", "icon":"📈", "bg":"#E0F2FE", "color":"#0C4A6E"},
        {"label":"Total Production", "value":f"{total_production:,}", "trend":"down", "percent":"2.3%", "icon":"🏭", "bg":"#FEF2F2", "color":"#991B1B"},
    ]
    
    for col, kpi in zip([kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6], kpi_items):
        with col:
            trend_icon = "↑" if kpi["trend"] == "up" else "↓" if kpi["trend"] == "down" else "→"
            trend_color = "#22C55E" if kpi["trend"] == "up" else "#EF4444" if kpi["trend"] == "down" else "#6B7280"
            st.markdown(f"""
            &lt;div class="kpi-card"&gt;
                &lt;div style="display:flex; justify-content:space-between; align-items:flex-start;"&gt;
                    &lt;span class="kpi-label"&gt;{kpi['label']}&lt;/span&gt;
                    &lt;div style="width:56px;height:56px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:28px;background:{kpi['bg']};color:{kpi['color']};"&gt;{kpi['icon']}&lt;/div&gt;
                &lt;/div&gt;
                &lt;div class="kpi-value"&gt;{kpi['value']}&lt;/div&gt;
                &lt;div class="kpi-trend" style="color:{trend_color}; display:flex; align-items:center; gap:8px;"&gt;
                    &lt;span style="font-size:16px; font-weight:900;"&gt;{trend_icon}&lt;/span&gt;
                    &lt;span&gt;{kpi['percent']} this month&lt;/span&gt;
                &lt;/div&gt;
            &lt;/div&gt;
            """, unsafe_allow_html=True)
    
    st.markdown("&lt;div style='height:24px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
    
    # Charts
    mid_col1, mid_col2, mid_col3 = st.columns([3, 2, 2])
    
    with mid_col1:
        with st.container():
            st.markdown("""
            &lt;div class="chart-card"&gt;
                &lt;div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;"&gt;
                    &lt;span class="chart-title"&gt;Trend Analysis&lt;/span&gt;
                &lt;/div&gt;
            """, unsafe_allow_html=True)
            
            plot_cols = [col for col in numeric_cols if col != 'EmployeeID'][:3]
            if plot_cols:
                if 'Date' in df.columns:
                    fig = px.line(df, x='Date', y=plot_cols, template='plotly_white', line_shape='spline')
                else:
                    fig = px.line(df, y=plot_cols, template='plotly_white', line_shape='spline')
                fig.update_layout(height=340, margin=dict(l=0,r=0,t=0,b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14)))
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("&lt;/div&gt;", unsafe_allow_html=True)
    
    with mid_col2:
        with st.container():
            st.markdown("""
            &lt;div class="chart-card"&gt;
                &lt;span class="chart-title"&gt;Distribution&lt;/span&gt;
            """, unsafe_allow_html=True)
            
            if 'Department' in df.columns:
                dept_dist = df['Department'].value_counts().reset_index()
                dept_dist.columns = ['Department', 'Count']
                fig_dept = px.pie(dept_dist, values='Count', names='Department', template='plotly_white', hole=0.65, color_discrete_sequence=["#0A2A66","#2563EB","#7C3AED","#22C55E","#F97316","#06B6D4","#64748B"])
                fig_dept.update_layout(height=340, margin=dict(l=0,r=0,t=24,b=0), showlegend=True, legend=dict(font=dict(size=13)))
                st.plotly_chart(fig_dept, use_container_width=True)
            st.markdown("&lt;/div&gt;", unsafe_allow_html=True)
    
    with mid_col3:
        with st.container():
            st.markdown("""
            &lt;div class="chart-card"&gt;
                &lt;div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;"&gt;
                    &lt;span class="chart-title"&gt;Recent Activities&lt;/span&gt;
                &lt;/div&gt;
            """, unsafe_allow_html=True)
            
            st.dataframe(df.head(5), hide_index=True, use_container_width=True)
            st.markdown("&lt;/div&gt;", unsafe_allow_html=True)
    
    st.markdown("&lt;div style='height:24px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
    
    # Bottom section
    bottom_col1, bottom_col2 = st.columns([2, 2])
    with bottom_col1:
        with st.container():
            st.markdown("""
            &lt;div class="chart-card"&gt;
                &lt;span class="chart-title"&gt;Full Data Preview&lt;/span&gt;
            """, unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("&lt;/div&gt;", unsafe_allow_html=True)
    
    with bottom_col2:
        with st.container():
            st.markdown("""
            &lt;div class="chart-card"&gt;
                &lt;span class="chart-title"&gt;Statistics Summary&lt;/span&gt;
            """, unsafe_allow_html=True)
            if numeric_cols:
                st.dataframe(df[numeric_cols].describe(), use_container_width=True)
            st.markdown("&lt;/div&gt;", unsafe_allow_html=True)

elif st.session_state.selected_page == "employees":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;👥 Employee Dashboard&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        if 'EmployeeID' in df.columns or 'Name' in df.columns:
            emp_cols = [col for col in df.columns if 'emp' in col.lower() or 'name' in col.lower() or 'department' in col.lower()]
            if emp_cols:
                st.dataframe(df[emp_cols + list(set(df.columns) - set(emp_cols))], use_container_width=True, hide_index=True)
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.selected_page == "attendance":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;📊 Attendance Dashboard&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        att_cols = [col for col in df.columns if 'att' in col.lower() or 'present' in col.lower() or 'absent' in col.lower()]
        if att_cols:
            fig = px.bar(df, y=att_cols, title='Attendance Overview', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.selected_page == "production":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;🏭 Production Dashboard&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        prod_cols = [col for col in df.columns if 'prod' in col.lower() or 'production' in col.lower() or 'efficiency' in col.lower()]
        if prod_cols:
            if 'Date' in df.columns:
                fig = px.line(df, x='Date', y=prod_cols, template='plotly_white', line_shape='spline')
            else:
                fig = px.line(df, y=prod_cols, template='plotly_white', line_shape='spline')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.selected_page == "skills":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;🎯 Skill Matrix&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        if 'SkillLevel' in df.columns:
            fig = px.histogram(df, x='SkillLevel', nbins=20, template='plotly_white', title='Skill Level Distribution')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.selected_page == "stock":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;📦 Stock Analysis&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        if 'Stock' in df.columns:
            if 'Date' in df.columns:
                fig = px.line(df, x='Date', y='Stock', template='plotly_white', line_shape='spline', title='Stock Trend')
            else:
                fig = px.line(df, y='Stock', template='plotly_white', line_shape='spline', title='Stock Trend')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.selected_page == "toolroom":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;🔧 Toolroom Dashboard&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        if 'Tool' in df.columns or 'tool' in df.columns:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.selected_page == "profit":
    with st.container():
        st.markdown("""
        &lt;div class="chart-card"&gt;
            &lt;span class="chart-title"&gt;💰 Profit Analysis&lt;/span&gt;
        &lt;/div&gt;
        """, unsafe_allow_html=True)
        
        st.markdown("&lt;div style='height:20px;'&gt;&lt;/div&gt;", unsafe_allow_html=True)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            fig = px.bar(df, y=numeric_cols, title='Profit &amp; Metrics Overview', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
