# 🏭 Puja Fluid Seals - Integrated Dashboard

A unified, production-ready dashboard application integrating all existing modules into a single Streamlit app.

---

## 📋 Table of Contents
1. [Features](#-features)
2. [Installation](#-installation)
3. [Running the App](#-running-the-app)
4. [Dashboard Modules](#-dashboard-modules)
5. [Change Report](#-change-report)
6. [Deployment](#-deployment)
7. [Dependencies](#-dependencies)

---

## ✨ Features

- 🔗 **All-in-One Application**: 7 dashboards integrated into a single app
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Modern UI**: Beautiful gradients and intuitive navigation
- 📊 **Interactive Charts**: Powered by Plotly for rich visualizations
- 📁 **File Upload**: Support for Excel and CSV files
- 📥 **Export Features**: Download reports in multiple formats
- 🔍 **Search & Filter**: Easy data exploration
- 📈 **Real-time Analytics**: Instant insights from your data

---

## 🚀 Installation

### Step 1: Install Python
Ensure you have Python 3.8 or higher installed. Download from [python.org](https://www.python.org/)

### Step 2: Clone or Navigate to Project
```bash
cd d:\Internship-Project-main
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the App

### Local Development
```bash
streamlit run app.py
```

The app will automatically open in your default browser at `http://localhost:8501`

### Access from Network
To access from other devices on your network:
```bash
streamlit run app.py --server.address 0.0.0.0
```

---

## 📊 Dashboard Modules

### 1. 🏠 Home
- Overview of all available dashboards
- Quick navigation to any module
- System status and metrics

### 2. 👥 Employee Dashboard
- Manage employee records
- Add new employees
- Export data (CSV, Excel)
- Quick statistics

### 3. 📈 Employee Efficiency
- Upload and analyze operator efficiency data
- Individual employee trend charts
- Distribution analysis
- All employees comparison
- Performance metrics

### 4. 🎯 Skill Matrix
- Employee competency assessment
- Skill rating visualization
- Distribution charts
- Skill level breakdown

### 5. 📦 Stock Analysis
- Upload sales and stock files
- Analyze stock vs pending orders
- Quick summary metrics
- Data preview and exploration

### 6. 🏭 Production Planning
- BOM (Bill of Materials) integration
- FG/SFG stock analysis
- Production requirement calculation
- Planning summary

### 7. 🔧 Toolroom Efficiency
- Toolroom operator performance
- Monthly trends
- Top performers analysis
- Efficiency metrics

### 8. 💰 Profit Analyzer
- Inventory profitability analysis
- Margin calculation based on quantity tiers
- Top/Low profit parts
- Revenue vs Profit visualization

---

## 📝 Change Report

### What Was Changed

#### ✅ Before Integration
- **7+ separate applications** (Flask, Dash, standalone scripts)
- **Port conflicts**: All Flask apps tried to use port 5000
- **No unified navigation**: Each app had to be run separately
- **Duplicate code**: Similar functions across multiple files
- **Inconsistent UI**: Different styling and user experience

#### ✅ After Integration
- **Single Streamlit app**: All modules in one place
- **No port conflicts**: Runs on port 8501 (Streamlit default)
- **Sidebar navigation**: Easy switching between dashboards
- **Unified UI/UX**: Consistent look and feel
- **Code optimization**: Removed redundancy
- **Production-ready**: Ready for deployment

### Files Created
1. `app.py` - Main unified application
2. `requirements.txt` - All dependencies
3. `README.md` - This documentation

### Files Analyzed (Original)
- `dashboard.py` - Employee dashboard
- `dashboard2.py` - Employee dashboard v2
- `employeeefficiency.py` - Efficiency analysis
- `skillmatrix.py` - Skill matrix
- `stockandsales.py` - Stock analysis
- `stockfinal.py` - Stock final
- `merge_stock.py` - Stock merging
- `toolroomeff.py` - Toolroom efficiency
- `profit.py` - Profit analyzer (Dash)
- `planning_app_complete.py` - Production planning
- `presentee.py` - Presentee
- `employeejoining.py` - Employee joining
- `reportsystem.py` - Report system
- `diagnostic.py` - Diagnostic
- `debug.py` - Debug

### Key Improvements
1. **Single Entry Point**: Run `streamlit run app.py` and everything is available
2. **Consistent Navigation**: Sidebar with all dashboards
3. **No Port Conflicts**: Uses Streamlit's default port 8501
4. **Modern UI**: Beautiful gradient designs
5. **Responsive Layout**: Works on all screen sizes
6. **Interactive Charts**: Plotly visualizations
7. **File Handling**: Built-in Streamlit file upload
8. **Session Management**: State persistence for user inputs

---

## 🌐 Deployment

### Option 1: Streamlit Cloud (Free)
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repo, branch, and file (`app.py`)
6. Click "Deploy!"

### Option 2: Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

Build and run:
```bash
docker build -t puja-dashboard .
docker run -p 8501:8501 puja-dashboard
```

### Option 3: Local Network
Run on your machine and share the URL with colleagues:
```bash
streamlit run app.py --server.address 0.0.0.0
```
Then access via `http://[YOUR_IP]:8501`

---

## 📦 Dependencies

```
streamlit==1.31.0
pandas==2.2.0
numpy==1.26.4
plotly==5.18.0
openpyxl==3.1.2
xlrd==2.0.1
flask==3.0.1
flask-cors==4.0.0
fpdf==1.7.2
dash==2.15.0
```

---

## 💡 Usage Tips

1. **File Upload**: Use Excel (.xlsx, .xls) or CSV files
2. **Navigation**: Use the sidebar to switch between dashboards
3. **Export**: Download buttons available in relevant modules
4. **Charts**: Hover over charts for detailed information
5. **Responsive**: Resize your browser - the app adapts automatically

---

## 🔧 Troubleshooting

### Port Already in Use
If port 8501 is occupied:
```bash
streamlit run app.py --server.port 8502
```

### Dependency Issues
Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

### Excel File Reading Issues
Ensure you have the latest Excel libraries:
```bash
pip install --upgrade openpyxl xlrd pandas
```

---

## 📄 License

Internal use for Puja Fluid Seals Pvt Ltd.

---

## 👥 Support

For questions or issues, contact the development team.

---

**Last Updated**: 2024
