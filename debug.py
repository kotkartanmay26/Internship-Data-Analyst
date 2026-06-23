import pandas as pd

# Read the Excel file
df = pd.read_excel('Employee Joining Data 26.xlsx', sheet_name='Contractor', header=None)

print("="*60)
print("DEBUGGING YOUR CONTRACTOR DATA")
print("="*60)

# Print first 20 rows to see structure
print("\nFirst 20 rows of Contractor sheet:")
print("-"*60)
for idx in range(min(25, len(df))):
    row = df.iloc[idx]
    print(f"Row {idx}: Col0='{row[0]}', Col1='{row[1]}', Col2='{row[2]}', Col3='{row[3]}', Col4='{row[4]}'")

print("\n" + "="*60)
print("COUNTING VALID EMPLOYEES")
print("="*60)

valid_employees = []
empty_cells = 0
header_rows = 0

for idx in range(len(df)):
    row = df.iloc[idx]
    
    # Get name from column 1 (B)
    name = row[1] if pd.notna(row[1]) else ''
    name_str = str(name).strip()
    
    # Skip empty names
    if name_str == '' or name_str == 'nan':
        empty_cells += 1
        continue
    
    # Skip header rows
    if name_str.lower() in ['name', 'sr.no', 's.no']:
        header_rows += 1
        continue
    
    # Check if it has a left date
    left_date = row[4] if len(row) > 4 and pd.notna(row[4]) else ''
    left_date_str = str(left_date).strip()
    
    has_left = left_date_str != '' and left_date_str != 'nan'
    
    dept = row[2] if pd.notna(row[2]) else 'Unknown'
    
    valid_employees.append({
        'row': idx,
        'name': name_str[:30],
        'dept': str(dept)[:20],
        'has_left': has_left,
        'left_date': left_date_str[:15] if has_left else 'None'
    })

print(f"\nTotal rows in sheet: {len(df)}")
print(f"Empty rows (no name): {empty_cells}")
print(f"Header rows: {header_rows}")
print(f"VALID EMPLOYEES: {len(valid_employees)}")

print("\n" + "="*60)
print("EMPLOYEES WITH NO LEFT DATE (Currently Working)")
print("="*60)

working = [e for e in valid_employees if not e['has_left']]
for e in working:
    print(f"Row {e['row']}: {e['name']:30} - {e['dept']}")

print(f"\nTOTAL WORKING: {len(working)}")

print("\n" + "="*60)
print("EMPLOYEES WITH LEFT DATE")
print("="*60)

left = [e for e in valid_employees if e['has_left']]
for e in left[:20]:  # Show first 20
    print(f"Row {e['row']}: {e['name']:30} - {e['dept']:20} - Left: {e['left_date']}")

print(f"\nTOTAL LEFT: {len(left)}")
print(f"TOTAL VALID: {len(working) + len(left)}")

print("\n" + "="*60)
print("DEPARTMENT WISE BREAKDOWN")
print("="*60)

dept_stats = {}
for e in valid_employees:
    dept = e['dept']
    if dept not in dept_stats:
        dept_stats[dept] = {'total': 0, 'left': 0}
    dept_stats[dept]['total'] += 1
    if e['has_left']:
        dept_stats[dept]['left'] += 1

for dept, stats in sorted(dept_stats.items(), key=lambda x: x[1]['total'], reverse=True):
    working_count = stats['total'] - stats['left']
    attrition = (stats['left'] / stats['total']) * 100
    print(f"{dept:25} Total: {stats['total']:3} | Working: {working_count:3} | Left: {stats['left']:3} | Attrition: {attrition:5.1f}%")