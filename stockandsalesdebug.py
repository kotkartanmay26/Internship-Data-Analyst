"""
FILE DIAGNOSTIC SCRIPT - Run this first to understand your file structure
"""

import pandas as pd

print("=" * 80)
print("FILE DIAGNOSTIC")
print("=" * 80)

# Read Sales File
print("\n1. READING SALES ORDER FILE...")
try:
    df_sales = pd.read_excel("Sales Order Book Balance.xls", sheet_name=0)
    print(f"✅ Successfully loaded {len(df_sales)} rows")
    print(f"\n📋 COLUMNS in Sales file:")
    for i, col in enumerate(df_sales.columns, 1):
        print(f"   {i}. '{col}'")
    
    print(f"\n📝 FIRST 3 ROWS of Sales file:")
    print(df_sales.head(3).to_string())
    
    print(f"\n🔍 Checking for Item Description column...")
    possible_desc_cols = ['ItemDesc', 'Item Description', 'Description', 'ITEMDESC', 'itemdesc', 'Item_Desc']
    found_desc = None
    for col in possible_desc_cols:
        if col in df_sales.columns:
            found_desc = col
            print(f"   ✅ Found column: '{col}'")
            break
    
    if not found_desc:
        print(f"   ❌ Could not find item description column!")
        print(f"   Available columns: {list(df_sales.columns)}")
        print(f"\n   Please check which column contains the item numbers like '1534 - NBR 70...'")
        
except Exception as e:
    print(f"❌ Error reading sales file: {e}")

# Read Stock File
print("\n" + "=" * 80)
print("2. READING STOCK FILE...")
try:
    df_stock = pd.read_excel("Stock FG SFG.xls", sheet_name=0)
    print(f"✅ Successfully loaded {len(df_stock)} rows")
    print(f"\n📋 COLUMNS in Stock file:")
    for i, col in enumerate(df_stock.columns, 1):
        print(f"   {i}. '{col}'")
    
    print(f"\n📝 FIRST 3 ROWS of Stock file:")
    print(df_stock.head(3).to_string())
    
    print(f"\n🔍 Checking for required columns...")
    
    # Check for ItemDesc
    if 'ItemDesc' in df_stock.columns:
        print(f"   ✅ Found 'ItemDesc' column")
        print(f"\n   Sample ItemDesc values:")
        for desc in df_stock['ItemDesc'].head(5):
            print(f"      - {desc}")
    else:
        print(f"   ❌ 'ItemDesc' column NOT found!")
        print(f"   Available columns: {list(df_stock.columns)}")
    
    # Check for Closing Stock
    if 'Closing Stock' in df_stock.columns:
        print(f"   ✅ Found 'Closing Stock' column")
        print(f"\n   Sample Closing Stock values:")
        for stock in df_stock['Closing Stock'].head(10):
            print(f"      - {stock}")
    else:
        print(f"   ❌ 'Closing Stock' column NOT found!")
        # Look for similar columns
        stock_cols = [col for col in df_stock.columns if 'stock' in col.lower() or 'qty' in col.lower()]
        if stock_cols:
            print(f"   💡 Similar columns found: {stock_cols}")
    
except Exception as e:
    print(f"❌ Error reading stock file: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)