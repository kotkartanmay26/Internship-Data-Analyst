"""
Quick Diagnostic - Find where data starts in Stock file
"""
import pandas as pd

print("=" * 80)
print("ANALYZING STOCK FILE STRUCTURE")
print("=" * 80)

# Read the file without any headers
df_raw = pd.read_excel("Stock FG SFG.xls", sheet_name=0, header=None)

print(f"\nTotal rows in file: {len(df_raw)}")
print(f"Total columns: {len(df_raw.columns)}")

print("\n🔍 First 10 rows of the file:")
print("-" * 80)
for i in range(min(10, len(df_raw))):
    row_data = df_raw.iloc[i].tolist()
    # Show first 5 columns only for clarity
    print(f"Row {i}: {row_data[:5]}...")

print("\n🔍 Looking for 'Plant' column header...")
plant_row = None
for i in range(len(df_raw)):
    if pd.notna(df_raw.iloc[i, 0]) and str(df_raw.iloc[i, 0]).strip() == 'Plant':
        plant_row = i
        print(f"✅ Found 'Plant' at row {i}")
        break

if plant_row is not None:
    print(f"\n📋 Row {plant_row} contains column headers:")
    headers = df_raw.iloc[plant_row].tolist()
    for j, h in enumerate(headers[:15]):
        print(f"   Col {j}: {h}")
    
    print(f"\n📊 Row {plant_row + 1} (first data row):")
    first_data = df_raw.iloc[plant_row + 1].tolist()
    for j, d in enumerate(first_data[:15]):
        print(f"   Col {j}: {d}")
    
    print(f"\n✅ Total data rows: {len(df_raw) - plant_row - 1}")