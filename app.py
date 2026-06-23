
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

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
    min-width: 320px !important;
    max-width: 320px !important;
    border-right: 1px solid rgba(255,255,255,0.1) !important;
}

[data-testid="stHeader"] {
    background: white !important;
    border-bottom: 1px solid #E5E7EB !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}

[data-testid="block-container"] {
    padding: 32px 48px !important;
}

.main {
    background-color: #F8FAFC !important;
}

.kpi-card {
    background: white;
    border-radius: 24px;
    padding: 32px 28px;
    border: 1px solid #F1F5F9;
    box-shadow: 0 8px 24px rgba(10,42,102,0.06);
    transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
}

.kpi-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(10,42,102,0.12);
    border-color: #DBEAFE;
}

.kpi-value {
    font-size: clamp(32px,4vw,48px) !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0A2A66 0%, #1E40AF 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    margin:16px 0 10px !important;
}

.kpi-label {
    font-size: clamp(15px, 1.8vw,18px) !important;
    font-weight: 700 !important;
    color: #475569 !important;
    text-transform:none;
}

.kpi-trend {
    font-size: 15px !important;
    font-weight:700 !important;
}

.chart-card {
    background: white;
    border-radius:24px;
    padding:36px;
    border:1px solid #F1F5F9;
    box-shadow:0 8px 24px rgba(10,42,102,0.06);
    margin-bottom: 32px;
}

.chart-title {
    font-size: clamp(20px, 2.5vw,26px) !important;
    font-weight:800 !important;
    color:#0A2A66 !important;
    margin-bottom: 28px !important;
    letter-spacing: -0.3px;
}

div.stButton > button {
    font-size: 15px !important;
    font-weight: 700 !important;
    padding: 14px 24px !important;
    border-radius: 12px !important;
    transition: all 0.25s ease !important;
    white-space: nowrap !important;
    width: 100% !important;
    min-width: 160px !important;
}

[data-testid="stDataFrame"] {
    font-size:14px !important;
}

[data-testid="stDataFrame"] th {
    font-size:15px !important;
    font-weight:800 !important;
    color:#0A2A66 !important;
    background:#F8FAFC !important;
    padding:16px 20px !important;
}

[data-testid="stDataFrame"] td {
    padding:16px 20px !important;
}

.sidebar-logo {
    width:60px;
    height:60px;
    border-radius:16px;
    background:linear-gradient(135deg,#2563EB 0%,#0A2A66 100%);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:32px;
    color:white;
    box-shadow:0 12px 32px rgba(37,99,235,0.35);
}

.quick-action-card {
    background: linear-gradient(135deg,#F8FAFC 0%,#F1F5F9 100%);
    border-radius:20px;
    padding:28px 20px;
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
    font-size:40px;
    margin-bottom:14px;
}

.quick-action-text {
    font-size:15px;
    font-weight:800;
    color:#0A2A66;
}
</style>
""", unsafe_allow_html=True)

if 'selected_page' not in st.session_state:
    st.session_state.selected_page = 'home'

@st.cache_data
def load_mock_data():
    dates = pd.date_range(start='2026-05-24', end='2026-06-23', freq='D')
    attendance = pd.DataFrame({
        "Date": dates,
        "Present": np.random.randint(190, 215, len(dates)),
        "Absent": np.random.randint(6,31, len(dates))
    })
    
    departments = pd.DataFrame({
        "Department": ["Production","Quality","Maintenance","Toolroom","HR","Purchase","Others"],
        "Count": [85,35,30,25,20,15,11]
    })
    
    skills = pd.DataFrame({
        "Skill Category": ["Technical Skills","Quality Skills","Safety Skills","Operator Skills","Maintenance Skills"],
        "Skilled": [150,142,160,135,120],
        "Average Level": [78,72,85,68,60],
        "Training Required": [18,16,10,20,22]
    })
    return attendance, departments, skills

attendance_df, departments_df, skills_df = load_mock_data()

with st.sidebar:
    st.markdown("""
    <div style="
        padding:28px 24px;
        display:flex;
        align-items:center;
        gap:18px;
        border-bottom:1px solid rgba(255,255,255,0.1);
        margin:-28px -24px 28px -24px;
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
    ">
        <div class="sidebar-logo">🏭</div>
        <div>
            <h2 style="margin:0; font-size:20px; font-weight:800; color:white;">Puja Fluid Seals</h2>
            <p style="margin:8px 0 0; font-size:14px; color:#94A3B8; font-weight:600;">Pvt. Ltd.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="padding:0 12px 16px;">
        <p style="color:#64748B; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin:0;">Main Menu</p>
    </div>
    """, unsafe_allow_html=True)
    
    nav_items = [
        ("home", "🏠", "Dashboard Overview"),
        ("employees", "👥", "Employee Dashboard"),
        ("efficiency", "📈", "Employee Efficiency"),
        ("skills", "🎯", "Skill Matrix"),
        ("stock", "📦", "Stock Analysis"),
        ("production", "🏭", "Production Planning"),
        ("toolroom", "🔧", "Toolroom Efficiency"),
        ("profit", "💰", "Profit Analyzer"),
        ("training", "📚", "Training Dashboard"),
        ("departments", "🏢", "Department Analytics"),
        ("reports", "📊", "Production Reports")
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
    <div style="padding:24px 12px 0; border-top:1px solid rgba(255,255,255,0.1); margin-top:28px;">
        <p style="color:#64748B; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin:0 0 16px 0;">System</p>
        <div style="display:flex; align-items:center; gap:12px; padding:16px 20px; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.35); border-radius:14px; margin-bottom:20px;">
            <span style="width:14px; height:14px; border-radius:50%; background:#22C55E; box-shadow:0 0 0 6px rgba(34,197,94,0.25);"></span>
            <span style="font-size:15px; color:#86EFAC; font-weight:800;">All Systems Operational</span>
        </div>
        <div style="
            background:linear-gradient(135deg, rgba(37,99,235,0.15) 0%, rgba(10,42,102,0.12) 100%);
            border:1px solid rgba(37,99,235,0.3);
            border-radius:18px;
            padding:24px;
            margin-bottom:20px;
        ">
            <p style="font-size:17px; font-weight:800; color:#60A5FA; margin:0 0 12px;">🚀 Boost Productivity</p>
            <p style="font-size:14px; color:rgba(255,255,255,0.8); line-height:1.7; margin:0 0 18px;">Track performance and make data-driven decisions effectively.</p>
        </div>
        <div style="
            padding-top:20px;
            border-top:1px solid rgba(255,255,255,0.1);
            color:rgba(255,255,255,0.7);
            font-size:14px;
            font-weight:600;
        ">
            <p style="margin:0 0 6px;">© 2024 Puja Fluid Seals Pvt. Ltd.</p>
            <p style="margin:0; opacity:0.8;">All rights reserved.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

header_col1, header_col2 = st.columns([1,2.5])
with header_col1:
    st.markdown("""
    <div>
        <h1 style="margin:0; font-size: clamp(30px,3.5vw,42px); font-weight:900; color:#0A2A66; letter-spacing:-0.5px;">Dashboard Overview</h1>
        <p style="margin:10px 0 0; font-size:17px; color:#64748B; font-weight:600;">Home • Overview</p>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    search_col, date_col, refresh_col, download_col, export_col, notif_col, profile_col = st.columns([2,1.5,1,1,1,0.8,1])
    
    with search_col:
        st.text_input(
            "🔍 Search employees, departments, skills, reports...",
            placeholder="🔍 Search employees, departments, skills, reports...",
            key="global_search",
            label_visibility="collapsed"
        )
    
    with date_col:
        default_start = datetime.now() - timedelta(days=30)
        default_end = datetime.now()
        st.date_input("📅 Date Range", [default_start, default_end], key="date_range", label_visibility="collapsed")
    
    with refresh_col:
        st.button("🔄 Refresh", key="refresh_header", use_container_width=True)
    
    with download_col:
        st.button("⬇️ Download", key="download_header", use_container_width=True)
    
    with export_col:
        st.button("📤 Export", key="export_header", use_container_width=True)
    
    with notif_col:
        st.button("🔔", key="notifications", use_container_width=True)
    
    with profile_col:
        st.markdown("""
        <div style="
            display:flex;
            align-items:center;
            gap:14px;
            padding:12px 20px;
            background:linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
            border:1px solid #E2E8F0;
            border-radius:16px;
            justify-content:center;
        ">
            <div style="
                width:48px;
                height:48px;
                border-radius:50%;
                background:linear-gradient(135deg,#2563EB 0%,#0A2A66 100%);
                display:flex;
                align-items:center;
                justify-content:center;
                color:white;
                font-size:22px;
                font-weight:900;
            ">
                A
            </div>
            <div style="text-align:left;">
                <p style="margin:0; font-size:16px; font-weight:900; color:#0A2A66;">Admin</p>
                <p style="margin:3px 0 0; font-size:13px; color:#64748B; font-weight:600;">Administrator</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)

if st.session_state.selected_page == "home":
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
    kpi_items = [
        {"label":"Total Employees","value":"221","trend":"up","percent":"12.5%","icon":"👥","bg":"#EFF6FF","color":"#1E40AF","target":"employees"},
        {"label":"Skilled Employees","value":"180","trend":"up","percent":"15.8%","icon":"🎓","bg":"#F0FDF4","color":"#166534","target":"skills"},
        {"label":"Training Required","value":"25","trend":"up","percent":"3.2%","icon":"📖","bg":"#FFF7ED","color":"#9A3412","target":"training"},
        {"label":"Departments","value":"21","trend":"neutral","percent":"No change","icon":"🏢","bg":"#F5F3FF","color":"#5B21B6","target":"departments"},
        {"label":"Production Efficiency","value":"88.6%","trend":"up","percent":"5.6%","icon":"📊","bg":"#E0F2FE","color":"#0C4A6E","target":"production"},
        {"label":"Monthly Output","value":"₹12.4K","trend":"down","percent":"2.3%","icon":"₹","bg":"#FEF2F2","color":"#991B1B","target":"reports"}
    ]
    
    for col, kpi in zip([kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6], kpi_items):
        with col:
            trend_icon = "↑" if kpi["trend"] == "up" else "↓" if kpi["trend"] == "down" else "→"
            trend_color = "#22C55E" if kpi["trend"] == "up" else "#EF4444" if kpi["trend"] == "down" else "#6B7280"
            st.markdown(f"""
            <div class="kpi-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <span class="kpi-label">{kpi['label']}</span>
                    <div style="
                        width:56px;
                        height:56px;
                        border-radius:16px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-size:28px;
                        background:{kpi['bg']};
                        color:{kpi['color']};
                    ">
                        {kpi['icon']}
                    </div>
                </div>
                <div class="kpi-value">{kpi['value']}</div>
                <div class="kpi-trend" style="color:{trend_color}; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px; font-weight:900;">{trend_icon}</span>
                    <span>{kpi['percent']} this month</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"View Details", key=f"kpi_btn_{kpi['label']}", use_container_width=True):
                st.session_state.selected_page = kpi["target"]
                st.rerun()
    
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    
    mid_col1, mid_col2, mid_col3 = st.columns([3, 2, 2])
    
    with mid_col1:
        with st.container():
            st.markdown("""
            <div class="chart-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                    <span class="chart-title">Employee Attendance Trend</span>
                    <div style="
                        background:#F8FAFC;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:10px 20px;
                    ">
                        <span style="font-size:14px; font-weight:700; color:#0A2A66;">This Month</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            fig_attendance = px.line(
                attendance_df,
                x="Date",
                y=["Present","Absent"],
                template="plotly_white",
                color_discrete_map={"Present":"#22C55E","Absent":"#EF4444"},
                line_shape="spline"
            )
            fig_attendance.update_traces(line=dict(width=4), marker=dict(size=7), fill='tozeroy', fillcolor='rgba(34,197,94,0.1)')
            fig_attendance.update_layout(
                height=340, margin=dict(l=0,r=0,t=0,b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14)),
                xaxis=dict(title="", showgrid=False, zeroline=False, tickfont=dict(size=13)),
                yaxis=dict(title="", gridcolor="#E2E8F0", tickfont=dict(size=13))
            )
            st.plotly_chart(fig_attendance, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    with mid_col2:
        with st.container():
            st.markdown("""
            <div class="chart-card">
                <span class="chart-title">Department Wise Distribution</span>
            """, unsafe_allow_html=True)
            
            fig_dept = px.pie(
                departments_df,
                values="Count",
                names="Department",
                template="plotly_white",
                hole=0.65,
                color_discrete_sequence=["#0A2A66","#2563EB","#7C3AED","#22C55E","#F97316","#06B6D4","#64748B"]
            )
            fig_dept.update_traces(textposition='outside', textinfo='percent+label', textfont=dict(size=13))
            fig_dept.update_layout(
                height=340, margin=dict(l=0,r=0,t=24,b=0), showlegend=True, legend=dict(font=dict(size=13)),
                annotations=[dict(text='221<br>Total', x=0.5, y=0.5, font_size=24, font_family='Inter', showarrow=False)]
            )
            st.plotly_chart(fig_dept, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    with mid_col3:
        with st.container():
            st.markdown("""
            <div class="chart-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                    <span class="chart-title">Recent Activities</span>
                    <button style="
                        background:transparent; border:none; color:#2563EB; font-size:14px; font-weight:800; cursor:pointer;
                    ">View All</button>
                </div>
            """, unsafe_allow_html=True)
            
            activities = [
                {"icon":"👤","text":"Employee data updated","time":"10:15 AM","bg":"#EFF6FF","color":"#1E40AF"},
                {"icon":"📋","text":"Skill matrix refreshed","time":"09:48 AM","bg":"#E0F2FE","color":"#0C4A6E"},
                {"icon":"📊","text":"Production report uploaded","time":"09:30 AM","bg":"#F0FDF4","color":"#166534"},
                {"icon":"📦","text":"Stock data updated","time":"09:15 AM","bg":"#FFF7ED","color":"#9A3412"},
                {"icon":"🔧","text":"Toolroom efficiency calculated","time":"08:50 AM","bg":"#FEF2F2","color":"#991B1B"}
            ]
            
            for act in activities:
                st.markdown(f"""
                <div style="
                    display:flex; align-items:flex-start; gap:16px; padding:18px 0; border-bottom:1px solid #F1F5F9;
                ">
                    <div style="
                        width:48px; height:48px; border-radius:14px; display:flex; align-items:center; justify-content:center;
                        font-size:22px; background:{act['bg']}; color:{act['color']}; flex-shrink:0;
                    ">
                        {act['icon']}
                    </div>
                    <div style="flex:1;">
                        <p style="margin:0 0 8px; font-size:15px; color:#1E293B; font-weight:700;">{act['text']}</p>
                        <p style="margin:0; font-size:13px; color:#64748B; font-weight:600;">{act['time']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    
    bottom_col1, bottom_col2, bottom_col3 = st.columns([2,1.8,1.2])
    
    with bottom_col1:
        with st.container():
            st.markdown("""
            <div class="chart-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                    <span class="chart-title">Skill Matrix Summary</span>
                    <div style="
                        background: linear-gradient(135deg,#2563EB 0%,#0A2A66 100%);
                        color:white; padding:12px 22px; border-radius:12px; font-weight:800; font-size:14px;
                    ">
                        View Details
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(skills_df,
                column_config={"Average Level": st.column_config.ProgressColumn("Average Level", format="%d%%", min_value=0, max_value=100, width="medium")},
                use_container_width=True,
                hide_index=True
            )
            st.markdown("</div>", unsafe_allow_html=True)
    
    with bottom_col2:
        with st.container():
            st.markdown("""
            <div class="chart-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                    <span class="chart-title">Training Status</span>
                    <div style="
                        background:#F8FAFC;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:10px 20px;
                    ">
                        <span style="font-size:14px; font-weight:700; color:#0A2A66;">This Month</span>
                    </div>
                </div>
                <div style="display:flex; gap:28px; align-items:center;">
                    <div style="
                        position:relative; width:180px; height:180px; border-radius:50%;
                        background: conic-gradient(#22C55E 0deg 270deg, #E2E8F0 270deg 360deg);
                        display:flex; align-items:center; justify-content:center;
                    ">
                        <div style="
                            width:140px; height:140px; border-radius:50%; background:white;
                            display:flex; align-items:center; justify-content:center; flex-direction:column;
                        ">
                            <span style="font-size:44px; font-weight:900; color:#0A2A66;">75%</span>
                            <span style="font-size:15px; color:#64748B; font-weight:700; margin-top:4px;">Completed</span>
                        </div>
                    </div>
                    <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                            <span style="font-size:15px; color:#475569; font-weight:700;">Total Trainings</span>
                            <span style="font-size:15px; color:#0A2A66; font-weight:900;">40</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                            <span style="font-size:15px; color:#475569; font-weight:700;">Completed</span>
                            <span style="font-size:15px; color:#22C55E; font-weight:900;">30</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                            <span style="font-size:15px; color:#475569; font-weight:700;">In Progress</span>
                            <span style="font-size:15px; color:#F97316; font-weight:900;">8</span>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span style="font-size:15px; color:#475569; font-weight:700;">Pending</span>
                            <span style="font-size:15px; color:#EF4444; font-weight:900;">2</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with bottom_col3:
        with st.container():
            st.markdown("""
            <div class="chart-card">
                <span class="chart-title">Quick Actions</span>
            """, unsafe_allow_html=True)
            
            quick_col1, quick_col2 = st.columns(2)
            with quick_col1:
                st.markdown("""
                <div class="quick-action-card" style="margin-bottom:20px;">
                    <div class="quick-action-icon">⬆️</div>
                    <div class="quick-action-text">Upload Excel</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                <div class="quick-action-card">
                    <div class="quick-action-icon">🔄</div>
                    <div class="quick-action-text">Refresh Data</div>
                </div>
                """, unsafe_allow_html=True)
            
            with quick_col2:
                st.markdown("""
                <div class="quick-action-card" style="margin-bottom:20px;">
                    <div class="quick-action-icon">⬇️</div>
                    <div class="quick-action-text">Download Report</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                <div class="quick-action-card">
                    <div class="quick-action-icon">📄</div>
                    <div class="quick-action-text">Export PDF</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        text-align:center; padding:40px 28px 28px; display:flex; justify-content:space-between; align-items:center;
        border-top:1px solid #E2E8F0; margin-top:12px;
    ">
        <div style="color:#64748B; font-size:15px; font-weight:600;">
            ⏰ {datetime.now().strftime('%A, %B %d, %Y')} • {datetime.now().strftime('%I:%M %p')}
        </div>
        <div style="color:#64748B; font-size:15px; font-weight:600;">
            📊 Dashboard last updated: {datetime.now().strftime('%b %d, %Y at %I:%M %p')}
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span style="color:#64748B; font-size:15px; font-weight:600;">Auto refresh every 5 minutes</span>
            <div style="
                width:56px; height:30px; background:linear-gradient(135deg,#22C55E 0%,#16A34A 100%);
                border-radius:16px; display:flex; align-items:center; padding:4px;
            ">
                <div style="width:24px; height:24px; background:white; border-radius:50%; margin-left:auto;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.selected_page == "employees":
    with st.container():
        st.markdown("""
        <div class="chart-card">
            <span class="chart-title">👥 Employee Dashboard</span>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("📤 Upload Employee Data Excel", type=['xlsx', 'xls'])
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.button("➕ Add Employee", use_container_width=True)
        
        with col2:
            st.button("📥 Download Report", use_container_width=True)
        
        with col3:
            st.button("🔄 Refresh", use_container_width=True)
        
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.info("This is the Employee Dashboard - full features coming soon!")

else:
    page_titles = {
        "efficiency": "📈 Employee Efficiency",
        "skills": "🎯 Skill Matrix",
        "stock": "📦 Stock Analysis",
        "production": "🏭 Production Planning",
        "toolroom": "🔧 Toolroom Efficiency",
        "profit": "💰 Profit Analyzer",
        "training": "📚 Training Dashboard",
        "departments": "🏢 Department Analytics",
        "reports": "📊 Production Reports"
    }
    
    with st.container():
        st.markdown(f"""
        <div class="chart-card">
            <span class="chart-title">{page_titles[st.session_state.selected_page]}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info(f"This is the {page_titles[st.session_state.selected_page]} page - full features coming soon!")

