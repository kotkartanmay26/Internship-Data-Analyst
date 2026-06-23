"""
Inventory Profit Analyzer - Professional Dashboard
With Lowest Profit Parts Analysis
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import base64
import io
import numpy as np
from datetime import datetime

# ----------------------------
# Data Processing Function
# ----------------------------

def process_file(contents, filename):
    """Process uploaded file and return processed DataFrame"""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if 'xlsx' in filename:
            df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
        elif 'csv' in filename:
            df = pd.read_csv(io.BytesIO(decoded))
        else:
            return None, "Unsupported file format"
        
        # Rename columns
        rename_dict = {}
        for col in df.columns:
            col_clean = str(col).strip()
            if col_clean == 'Qty':
                rename_dict[col] = 'quantity'
            elif col_clean == 'Amount':
                rename_dict[col] = 'amount'
            elif col_clean == 'Customer Name':
                rename_dict[col] = 'customer'
            elif col_clean == 'Part No':
                rename_dict[col] = 'part_no'
            elif col_clean == 'Part Description':
                rename_dict[col] = 'description'
            elif col_clean == 'Item Code':
                rename_dict[col] = 'item_code'
        
        df = df.rename(columns=rename_dict)
        
        # Check for required columns
        if 'quantity' not in df.columns:
            return None, f"Could not find Quantity column. Found: {list(df.columns)}"
        if 'amount' not in df.columns:
            return None, f"Could not find Amount column. Found: {list(df.columns)}"
        
        # Clean data
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['quantity', 'amount'])
        df = df[(df['quantity'] > 0) & (df['amount'] > 0)]
        
        if len(df) == 0:
            return None, "No valid data after cleaning"
        
        # Create part identifier
        if 'part_no' in df.columns:
            df['part_no'] = df['part_no'].fillna('').astype(str)
            if 'description' in df.columns:
                df['description'] = df['description'].fillna('').astype(str)
                df['part_id_full'] = df['part_no'] + ' - ' + df['description']
                df['part_id'] = df['description'].apply(lambda x: x[:35] + '...' if len(x) > 35 else x)
            else:
                df['part_id_full'] = df['part_no']
                df['part_id'] = df['part_no'].apply(lambda x: x[:35] + '...' if len(x) > 35 else x)
        elif 'description' in df.columns:
            df['description'] = df['description'].fillna('').astype(str)
            df['part_id_full'] = df['description']
            df['part_id'] = df['description'].apply(lambda x: x[:35] + '...' if len(x) > 35 else x)
        else:
            df['part_id_full'] = 'Item_' + df.index.astype(str)
            df['part_id'] = 'Item_' + df.index.astype(str)
        
        # Calculate metrics
        df['unit_price'] = df['amount'] / df['quantity']
        
        # Profit margin based on quantity tiers
        df['margin'] = np.where(
            df['quantity'] > 10000, 45,
            np.where(df['quantity'] > 5000, 40,
            np.where(df['quantity'] > 1000, 35,
            np.where(df['quantity'] > 500, 30,
            np.where(df['quantity'] > 100, 25, 20)))))
        
        df['profit'] = df['amount'] * (df['margin'] / 100)
        
        # Sort by profit
        df = df.sort_values('profit', ascending=False).reset_index(drop=True)
        
        print(f"✅ Successfully processed {len(df)} rows")
        print(f"📊 Total Revenue: ₹{df['amount'].sum():,.0f}")
        print(f"💰 Total Profit: ₹{df['profit'].sum():,.0f}")
        
        return df, None
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return None, f"Error: {str(e)}"

# ----------------------------
# Create Dashboard
# ----------------------------

app = Dash(__name__)

# Custom CSS for better styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
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
            
            .dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: white;
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                text-align: center;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                font-size: 42px;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #666;
                font-size: 16px;
            }
            
            .upload-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 50px;
                cursor: pointer;
                transition: transform 0.3s, box-shadow 0.3s;
                margin: 20px auto;
                display: block;
            }
            
            .upload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                transition: transform 0.3s;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.12);
            }
            
            .stat-icon {
                font-size: 40px;
                margin-bottom: 15px;
            }
            
            .stat-label {
                font-size: 13px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            
            .stat-value {
                font-size: 32px;
                font-weight: 800;
                color: #2c3e50;
            }
            
            .chart-card {
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            
            .chart-title {
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #2c3e50;
                border-left: 4px solid #667eea;
                padding-left: 15px;
            }
            
            .footer {
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-top: 30px;
                text-align: center;
                color: #666;
                font-size: 13px;
            }
            
            .insights-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .insight-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 15px;
                padding: 20px;
            }
            
            .data-table-container {
                background: white;
                border-radius: 15px;
                padding: 20px;
                overflow-x: auto;
            }
            
            .low-profit-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 25px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div(className="dashboard-container", children=[
    html.Div(className="header", children=[
        html.H1([html.I(className="fas fa-chart-line", style={'marginRight': '15px'}), "Inventory Profit Analyzer"]),
        html.P("Upload your inventory data to get comprehensive profit analytics and insights"),
    ]),
    
    dcc.Upload(
        id='upload-file',
        children=html.Button('📁 Select Excel/CSV File', className="upload-btn"),
        multiple=False
    ),
    
    html.Div(id='error-message', style={'color': '#ef4444', 'textAlign': 'center', 'margin': '20px'}),
    
    dcc.Loading(
        id='loading',
        type='default',
        children=[html.Div(id='dashboard-content')]
    )
])

@app.callback(
    Output('dashboard-content', 'children'),
    Output('error-message', 'children'),
    Input('upload-file', 'contents'),
    prevent_initial_call=True
)
def update_dashboard(contents):
    if contents is None:
        return html.Div(), ""
    
    df, error = process_file(contents, "file.xlsx")
    
    if error:
        return html.Div(), f"❌ {error}"
    
    # Calculate totals
    total_revenue = df['amount'].sum()
    total_quantity = df['quantity'].sum()
    total_profit = df['profit'].sum()
    avg_margin = df['margin'].mean()
    unique_parts = df['part_id'].nunique()
    
    # Format currency
    def format_currency(value):
        if value >= 10000000:
            return f"₹{value/10000000:.1f}Cr"
        elif value >= 100000:
            return f"₹{value/100000:.1f}L"
        else:
            return f"₹{value:,.0f}"
    
    # Statistics Cards
    stats_cards = html.Div(className="stats-grid", children=[
        html.Div(className="stat-card", children=[
            html.Div(html.I(className="fas fa-chart-line", style={'color': '#667eea'}), className="stat-icon"),
            html.Div("Total Revenue", className="stat-label"),
            html.Div(format_currency(total_revenue), className="stat-value")
        ]),
        html.Div(className="stat-card", children=[
            html.Div(html.I(className="fas fa-boxes", style={'color': '#10b981'}), className="stat-icon"),
            html.Div("Total Quantity", className="stat-label"),
            html.Div(f"{total_quantity:,.0f}", className="stat-value")
        ]),
        html.Div(className="stat-card", children=[
            html.Div(html.I(className="fas fa-chart-pie", style={'color': '#f59e0b'}), className="stat-icon"),
            html.Div("Est. Profit", className="stat-label"),
            html.Div(format_currency(total_profit), className="stat-value")
        ]),
        html.Div(className="stat-card", children=[
            html.Div(html.I(className="fas fa-percent", style={'color': '#ef4444'}), className="stat-icon"),
            html.Div("Avg Margin", className="stat-label"),
            html.Div(f"{avg_margin:.1f}%", className="stat-value")
        ]),
        html.Div(className="stat-card", children=[
            html.Div(html.I(className="fas fa-cubes", style={'color': '#8b5cf6'}), className="stat-icon"),
            html.Div("Unique Parts", className="stat-label"),
            html.Div(f"{unique_parts:,}", className="stat-value")
        ]),
    ])
    
    # Get lowest profit parts
    lowest_parts = df.nsmallest(15, 'profit')[['part_id', 'profit', 'margin', 'quantity', 'amount']].copy()
    lowest_parts['profit_label'] = lowest_parts['profit'].apply(lambda x: f"₹{x:,.0f}")
    
    fig_low = px.bar(lowest_parts, x='profit', y='part_id', 
                      title='⚠️ Lowest 15 Profit Parts (Needs Attention)',
                      labels={'profit': 'Profit (₹)', 'part_id': ''},
                      color='profit',
                      color_continuous_scale='Reds',
                      text='profit_label',
                      orientation='h')
    fig_low.update_traces(textposition='outside', textfont=dict(size=11))
    fig_low.update_layout(
        height=550,
        xaxis_title="Profit (₹)",
        yaxis_title="",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", size=12)
    )
    
    # Top Profitable Parts
    top_parts = df.head(15)[['part_id', 'profit', 'margin', 'quantity']].copy()
    top_parts['profit_label'] = top_parts['profit'].apply(lambda x: f"₹{x/100000:.1f}L" if x >= 100000 else f"₹{x:,.0f}")
    
    fig1 = px.bar(top_parts, x='profit', y='part_id', 
                  title='Top 15 Most Profitable Parts',
                  labels={'profit': 'Profit (₹)', 'part_id': ''},
                  color='margin',
                  color_continuous_scale='Viridis',
                  text='profit_label',
                  orientation='h')
    fig1.update_traces(textposition='outside', textfont=dict(size=11))
    fig1.update_layout(
        height=550,
        xaxis_title="Estimated Profit (₹)",
        yaxis_title="",
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", size=12)
    )
    
    # Top Revenue Parts
    top_revenue = df.head(15)[['part_id', 'amount', 'quantity']].copy()
    top_revenue['amount_label'] = top_revenue['amount'].apply(lambda x: f"₹{x/100000:.1f}L" if x >= 100000 else f"₹{x:,.0f}")
    
    fig2 = px.bar(top_revenue, x='amount', y='part_id',
                  title='Top 15 Parts by Revenue',
                  labels={'amount': 'Revenue (₹)', 'part_id': ''},
                  color='quantity',
                  color_continuous_scale='Blues',
                  text='amount_label',
                  orientation='h')
    fig2.update_traces(textposition='outside', textfont=dict(size=11))
    fig2.update_layout(
        height=550,
        xaxis_title="Revenue (₹)",
        yaxis_title="",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", size=12)
    )
    
    # Margin distribution
    fig4 = px.histogram(df, x='margin', nbins=20,
                        title='Profit Margin Distribution',
                        labels={'margin': 'Margin (%)', 'count': 'Number of Parts'},
                        color_discrete_sequence=['#667eea'])
    fig4.update_layout(
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", size=12)
    )
    
    # Scatter plot
    sample_df = df.head(500) if len(df) > 500 else df
    fig5 = px.scatter(sample_df, x='quantity', y='profit', 
                      size='amount', 
                      color='margin',
                      title='Quantity vs Profit Analysis',
                      labels={'quantity': 'Quantity (log scale)', 'profit': 'Profit (₹)', 'margin': 'Margin (%)'},
                      log_x=True,
                      hover_data={'part_id_full': True, 'quantity': ':.0f', 'profit': ':,.0f'},
                      size_max=50)
    fig5.update_layout(
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", size=12)
    )
    
    # Customer analysis
    if 'customer' in df.columns:
        customer_data = df.groupby('customer')['amount'].sum().nlargest(10).reset_index()
        customer_data['amount_label'] = customer_data['amount'].apply(lambda x: f"₹{x/100000:.1f}L" if x >= 100000 else f"₹{x:,.0f}")
        customer_data['customer_short'] = customer_data['customer'].apply(lambda x: x[:30] + '...' if len(str(x)) > 30 else str(x))
        
        fig6 = px.bar(customer_data, x='amount', y='customer_short',
                      title='Top 10 Customers by Revenue',
                      labels={'amount': 'Revenue (₹)', 'customer_short': 'Customer'},
                      color='amount',
                      color_continuous_scale='Reds',
                      text='amount_label',
                      orientation='h')
        fig6.update_traces(textposition='outside', textfont=dict(size=11))
        fig6.update_layout(
            height=500,
            xaxis_title="Revenue (₹)",
            yaxis_title="",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter", size=12)
        )
        customer_chart = dcc.Graph(figure=fig6)
    else:
        customer_chart = html.Div("Customer data not available", 
                                  style={'textAlign': 'center', 'padding': '50px', 'color': '#666', 'backgroundColor': '#f9f9f9', 'borderRadius': '10px'})
    
    # Data table with full part names
    table_data = df.head(50)[['part_id_full', 'quantity', 'amount', 'unit_price', 'profit', 'margin']].copy()
    table_data.columns = ['Part (Full Name)', 'Quantity', 'Revenue (₹)', 'Unit Price (₹)', 'Profit (₹)', 'Margin (%)']
    table_data = table_data.round(2)
    table_data['Revenue (₹)'] = table_data['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
    table_data['Profit (₹)'] = table_data['Profit (₹)'].apply(lambda x: f"₹{x:,.0f}")
    table_data['Unit Price (₹)'] = table_data['Unit Price (₹)'].apply(lambda x: f"₹{x:.2f}")
    
    table = dash_table.DataTable(
        data=table_data.to_dict('records'),
        columns=[{"name": col, "id": col} for col in table_data.columns],
        page_size=10,
        style_table={'overflowX': 'auto', 'height': '500px'},
        style_cell={
            'textAlign': 'left', 
            'padding': '12px',
            'fontFamily': 'Inter',
            'fontSize': '12px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#667eea',
            'color': 'white',
            'fontWeight': 'bold',
            'fontSize': '13px',
            'padding': '12px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
        ],
        sort_action='native',
        filter_action='native',
    )
    
    # Complete dashboard
    dashboard = html.Div([
        stats_cards,
        html.Div(className="chart-card", children=[
            html.Div("💰 Most Profitable Parts", className="chart-title"),
            dcc.Graph(figure=fig1)
        ]),
        html.Div(className="chart-card", children=[
            html.Div("⚠️ Lowest Profit Parts (Needs Improvement)", className="chart-title"),
            dcc.Graph(figure=fig_low)
        ]),
        html.Div(className="chart-card", children=[
            html.Div("📊 Top Revenue Generators", className="chart-title"),
            dcc.Graph(figure=fig2)
        ]),
        html.Div(className="chart-card", children=[
            html.Div("📊 Margin Distribution", className="chart-title"),
            dcc.Graph(figure=fig4)
        ]),
        html.Div(className="chart-card", children=[
            html.Div("🎯 Volume vs Profit Analysis", className="chart-title"),
            dcc.Graph(figure=fig5)
        ]),
        html.Div(className="chart-card", children=[
            html.Div("🏢 Customer Analysis", className="chart-title"),
            customer_chart
        ]),
        html.Div(className="data-table-container", children=[
            html.Div("📋 Top 50 Profitable Parts", className="chart-title"),
            table
        ]),
        html.Div(className="footer", children=[
            html.I(className="fas fa-info-circle", style={'marginRight': '10px'}),
            "Profit margins estimated based on volume tiers: ",
            html.Span("45% (>10k)", style={'color': '#10b981', 'fontWeight': 'bold'}),
            " | 40% (5-10k) | 35% (1-5k) | 30% (500-1k) | 25% (100-500) | 20% (<100)",
            html.Br(),
            html.Small(f"📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style={'color': '#888'})
        ])
    ])
    
    return dashboard, ""

# ----------------------------
# Run
# ----------------------------
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Inventory Profit Analyzer Starting...")
    print("="*60)
    print("\n📌 Open http://127.0.0.1:8050 in your browser")
    print("📊 Upload your Excel file")
    print("⚠️  Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=8050)