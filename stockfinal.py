import pandas as pd
import numpy as np
from datetime import datetime

# ============================================
# DATA LOADING FUNCTIONS
# ============================================

def load_pending_data(file_path):
    """Load Pending Qty data from Excel"""
    df = pd.read_excel(file_path, sheet_name='Pending')
    return df

def load_bom_data(file_path):
    """Load BOM data from Excel"""
    df = pd.read_excel(file_path, sheet_name='BOM')
    return df

def load_stock_data(file_path):
    """Load Stock data from Excel"""
    df = pd.read_excel(file_path, sheet_name='Stock')
    return df

# ============================================
# DATA PROCESSING FUNCTIONS
# ============================================

def get_sfg_from_bom(pending_df, bom_df):
    """
    Map SFG Item Code and Description from BOM to Pending data
    Based on ItemNo mapping in BOM table
    """
    # Create BOM mapping dictionary
    bom_mapping = {}
    
    for _, row in bom_df.iterrows():
        item_no = row.get('ItemNo')
        bom_item_no = row.get('BOM_ItemNo')
        bom_item_desc = row.get('BOM_ItemDesc')
        
        if pd.notna(item_no) and pd.notna(bom_item_no):
            if item_no not in bom_mapping:
                bom_mapping[item_no] = {
                    'sfg_item_no': bom_item_no,
                    'sfg_item_desc': bom_item_desc
                }
    
    # Apply mapping to pending data
    pending_df['SFG ItemCode'] = pending_df['ItemNo'].map(
        lambda x: bom_mapping.get(x, {}).get('sfg_item_no', '')
    )
    pending_df['SFG ItemDesc'] = pending_df['ItemNo'].map(
        lambda x: bom_mapping.get(x, {}).get('sfg_item_desc', '')
    )
    
    return pending_df


def get_fg_stock(pending_df, stock_df):
    """
    Calculate FG Stock from Stock Report
    """
    # Create stock dictionary for FG items
    fg_stock_dict = {}
    
    for _, row in stock_df.iterrows():
        item_no = row.get('ItemNo')
        closing_stock = row.get('Closing Stock', 0)
        
        if pd.notna(item_no):
            if item_no in fg_stock_dict:
                fg_stock_dict[item_no] += closing_stock
            else:
                fg_stock_dict[item_no] = closing_stock
    
    # Apply to pending data
    pending_df['fg stock'] = pending_df['ItemNo'].map(
        lambda x: fg_stock_dict.get(x, 0)
    ).fillna(0)
    
    return pending_df


def get_sfg_stock(pending_df, stock_df):
    """
    Calculate SFG Stock from Stock Report
    """
    # Create stock dictionary for SFG items
    sfg_stock_dict = {}
    
    for _, row in stock_df.iterrows():
        item_no = row.get('ItemNo')
        closing_stock = row.get('Closing Stock', 0)
        
        if pd.notna(item_no):
            if item_no in sfg_stock_dict:
                sfg_stock_dict[item_no] += closing_stock
            else:
                sfg_stock_dict[item_no] = closing_stock
    
    # Apply to pending data
    pending_df['sfg stock'] = pending_df['SFG ItemCode'].map(
        lambda x: sfg_stock_dict.get(x, 0) if pd.notna(x) else 0
    ).fillna(0)
    
    return pending_df


def calculate_totals(pending_df):
    """
    Calculate Total Stock and Pending Qty for Planning
    """
    # Ensure numeric columns
    pending_df['fg stock'] = pd.to_numeric(pending_df['fg stock'], errors='coerce').fillna(0)
    pending_df['sfg stock'] = pd.to_numeric(pending_df['sfg stock'], errors='coerce').fillna(0)
    pending_df['BalQty'] = pd.to_numeric(pending_df['BalQty'], errors='coerce').fillna(0)
    
    # Calculate total stock
    pending_df['total stock'] = pending_df['fg stock'] + pending_df['sfg stock']
    
    # Calculate pending qty for planning
    pending_df['Bal Qty for planning'] = pending_df['BalQty'] - pending_df['total stock']
    
    # Ensure non-negative values
    pending_df['Bal Qty for planning'] = pending_df['Bal Qty for planning'].clip(lower=0)
    
    return pending_df


def format_output(pending_df):
    """
    Format the output dataframe with required columns
    """
    output_columns = [
        'CustCode', 'CustName', 'SoDate', 'CustPONo', 'ItemNo', 'ItemCode', 
        'ItemDesc', 'SFG ItemCode', 'SFG ItemDesc', 'SOQty', 'InvQty', 'BalQty',
        'fg stock', 'sfg stock', 'total stock', 'Bal Qty for planning'
    ]
    
    # Select only columns that exist
    existing_columns = [col for col in output_columns if col in pending_df.columns]
    output_df = pending_df[existing_columns].copy()
    
    # Format date columns
    if 'SoDate' in output_df.columns:
        output_df['SoDate'] = pd.to_datetime(output_df['SoDate']).dt.strftime('%d-%m-%Y')
    
    return output_df


def generate_planning_summary(pending_df):
    """
    Generate summary of items needing planning
    """
    planning_df = pending_df[pending_df['Bal Qty for planning'] > 0].copy()
    planning_df = planning_df.sort_values('Bal Qty for planning', ascending=False)
    
    summary = {
        'total_items': len(pending_df),
        'items_need_planning': len(planning_df),
        'total_pending_qty': pending_df['Bal Qty for planning'].sum(),
        'total_planning_qty': planning_df['Bal Qty for planning'].sum(),
        'planning_list': planning_df[['ItemNo', 'ItemDesc', 'Bal Qty for planning']].to_dict('records')
    }
    
    return summary


def merge_with_erp_pending(pending_df, erp_df):
    """
    Merge with ERP Pending data if available
    """
    # Rename columns for consistency
    erp_columns = {
        'SONo': 'SONo',
        'ItemNo': 'ItemNo',
        'SOQty': 'SOQty_ERP',
        'InvQty': 'InvQty_ERP',
        'BalQty': 'BalQty_ERP'
    }
    
    for old_col, new_col in erp_columns.items():
        if old_col in erp_df.columns:
            erp_df.rename(columns={old_col: new_col}, inplace=True)
    
    # Merge on ItemNo
    merged_df = pd.merge(
        pending_df, 
        erp_df[['ItemNo', 'SOQty_ERP', 'InvQty_ERP', 'BalQty_ERP']], 
        on='ItemNo', 
        how='left'
    )
    
    return merged_df

# ============================================
# MAIN EXECUTION
# ============================================

def main(pending_file_path, bom_file_path, stock_file_path, output_file_path=None):
    """
    Main function to process all data and generate output
    """
    print("Loading data files...")
    
    # Load data
    pending_df = load_pending_data(pending_file_path)
    bom_df = load_bom_data(bom_file_path)
    stock_df = load_stock_data(stock_file_path)
    
    print(f"Pending records: {len(pending_df)}")
    print(f"BOM records: {len(bom_df)}")
    print(f"Stock records: {len(stock_df)}")
    
    # Process data
    print("\nProcessing BOM mapping...")
    pending_df = get_sfg_from_bom(pending_df, bom_df)
    
    print("Calculating FG stock...")
    pending_df = get_fg_stock(pending_df, stock_df)
    
    print("Calculating SFG stock...")
    pending_df = get_sfg_stock(pending_df, stock_df)
    
    print("Calculating totals and planning qty...")
    pending_df = calculate_totals(pending_df)
    
    # Format output
    output_df = format_output(pending_df)
    
    # Generate summary
    summary = generate_planning_summary(pending_df)
    
    # Print summary
    print("\n" + "="*60)
    print("PRODUCTION PLANNING SUMMARY")
    print("="*60)
    print(f"Total Pending Items: {summary['total_items']}")
    print(f"Items Needing Planning: {summary['items_need_planning']}")
    print(f"Total Pending Quantity: {summary['total_pending_qty']:.0f}")
    print(f"Total Planning Required: {summary['total_planning_qty']:.0f}")
    print("="*60)
    
    # Show top 10 items needing planning
    print("\nTOP 10 ITEMS NEEDING PLANNING:")
    print("-"*80)
    for i, item in enumerate(summary['planning_list'][:10], 1):
        print(f"{i}. {item['ItemNo']} - {item['ItemDesc'][:50]}... : {item['Bal Qty for planning']:.0f} units")
    
    # Save to Excel if output path provided
    if output_file_path:
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            output_df.to_excel(writer, sheet_name='Planning Output', index=False)
            
            # Add summary sheet
            summary_df = pd.DataFrame([
                ['Total Pending Items', summary['total_items']],
                ['Items Needing Planning', summary['items_need_planning']],
                ['Total Pending Quantity', summary['total_pending_qty']],
                ['Total Planning Required', summary['total_planning_qty']],
                ['Report Generated', datetime.now().strftime('%d-%m-%Y %H:%M:%S')]
            ], columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Add planning list
            planning_list_df = pd.DataFrame(summary['planning_list'])
            planning_list_df.to_excel(writer, sheet_name='Planning List', index=False)
        
        print(f"\nOutput saved to: {output_file_path}")
    
    return output_df, summary


# ============================================
# SAMPLE DATA FOR TESTING
# ============================================

def create_sample_data():
    """Create sample data for testing"""
    
    # Sample Pending Data
    pending_data = {
        'CustCode': ['C0001', 'C0001', 'C0001', 'C0092'],
        'CustName': ['Rsb Transmission (I) Ltd', 'Rsb Transmission (I) Ltd', 'Rsb Transmission (I) Ltd', 'RSB Transmissions (I)Ltd.Sricity UII'],
        'SoDate': ['30-01-2026', '30-01-2026', '30-01-2026', '03-02-2026'],
        'CustPONo': ['OF 25001405', 'OF 25001405', 'OF 25001405', 'OF / 25000206'],
        'ItemNo': ['FG0002', 'FG0003', 'FG0006', 'FG0017'],
        'ItemCode': ['20022340002P55P', '21022340003P00P', '25222330008P00P', '26422330001P00P'],
        'ItemDesc': ['1864 - 680 JT C B Seal', '2403 - 620 JT C B Seal', '80021 - TML Rubber Housing', '81297 - Isuzu 4X4 Rubber Housing'],
        'SOQty': [6000, 7000, 200, 8500],
        'InvQty': [2200, 3600, 75, 2835],
        'BalQty': [3800, 3400, 125, 5665]
    }
    
    # Sample BOM Data
    bom_data = {
        'ItemNo': ['FG0002', 'FG0003', 'FG0006', 'FG0007', 'FG0009', 'FG0010', 'FG0011', 'FG0012', 'FG0013', 'FG0016', 'FG0017', 'FG0018'],
        'BOM_ItemNo': ['SFG1940', 'SFG1941', 'SFG1944', 'SFG1945', 'SFG1947', 'SFG1948', 'SFG1949', 'SFG1950', 'SFG1951', 'SFG1954', 'SFG1955', 'SFG1956'],
        'BOM_ItemDesc': [
            'Molding - 1864 - 680 JT C B Seal NBR 70',
            'Molding - 2403 - 620 JT C B Seal NBR 70',
            'Molding - 80021 - TML Rubber Housing NR+SBR 60',
            'Molding - 81900/80565 - Rubber HSG 590JT (A-1) NR+SBR 60',
            'Molding - 81851 - 680 JT Rubber Housing NR+SBR 60',
            'Molding - 83060 - 590 NG Rubber Housing NR+SBR 60',
            'Molding - 83816/83374 - 590 HD Rubber Housing NR+SBR 65',
            'Molding - 83426 - 620 HD Rubber Housing NR+SBR 65',
            'Molding - 1534 - 490 JT C B Seal NBR 70',
            'Molding - 2466 - C B Seal 590 NG NBR 70',
            'Molding - 81297 - 4X4 Rubber Housing NEOPRENE 65',
            'Molding - 81656 - Rubber Housing 6301 NR+SBR 55'
        ]
    }
    
    # Sample Stock Data
    stock_data = {
        'ItemNo': ['FG0002', 'FG0002', 'FG0004', 'FG0005', 'FG0009', 'FG0010', 'FG0011', 'FG0013', 'FG0016', 'FG0017', 'FG0018', 'SFG1940', 'SFG1941', 'SFG1944', 'SFG1945', 'SFG1947', 'SFG1948', 'SFG1949', 'SFG1950', 'SFG1951', 'SFG1954', 'SFG1955'],
        'Closing Stock': [91, 0, 17, 7, 25, 18, 24, 31, 26, 41, 26, 810, 1150, 20, 1083, 167, 668, 1240, 800, 2021, 1860, 695]
    }
    
    pending_df = pd.DataFrame(pending_data)
    bom_df = pd.DataFrame(bom_data)
    stock_df = pd.DataFrame(stock_data)
    
    return pending_df, bom_df, stock_df


# ============================================
# RUN WITH SAMPLE DATA
# ============================================

if __name__ == "__main__":
    # Option 1: Use sample data for testing
    print("Running with sample data...")
    pending_df, bom_df, stock_df = create_sample_data()
    
    # Process data
    pending_df = get_sfg_from_bom(pending_df, bom_df)
    pending_df = get_fg_stock(pending_df, stock_df)
    pending_df = get_sfg_stock(pending_df, stock_df)
    pending_df = calculate_totals(pending_df)
    output_df = format_output(pending_df)
    summary = generate_planning_summary(pending_df)
    
    # Display results
    print("\n" + "="*100)
    print("PROCESSED OUTPUT")
    print("="*100)
    print(output_df.to_string(index=False))
    
    print("\n" + "="*100)
    print("PLANNING SUMMARY")
    print("="*100)
    for key, value in summary.items():
        if key != 'planning_list':
            print(f"{key}: {value}")
    
    # Save to file
    output_df.to_excel('production_planning_output.xlsx', index=False)
    print("\nOutput saved to 'production_planning_output.xlsx'")
    
    # Option 2: Use actual files (uncomment and provide file paths)
    """
    pending_file = 'Pending Qty 19.05.2026 w.xlsx'
    bom_file = 'Pending Qty 19.05.2026 w.xlsx'
    stock_file = 'Pending Qty 19.05.2026 w.xlsx'
    output_file = 'production_planning_output.xlsx'
    
    output_df, summary = main(pending_file, bom_file, stock_file, output_file)
    """