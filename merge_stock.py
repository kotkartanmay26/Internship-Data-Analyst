import pandas as pd
import re
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# ==========================================================
# FILE NAMES
# ==========================================================
SALES_FILE = "Sales Order Book Balance.xls"
STOCK_FILE = "Stock FG SFG.xls"

OUTPUT_EXCEL = "Sales_Order_Balance_With_Stock.xlsx"
OUTPUT_PDF = "Sales_Order_Balance_With_Stock_Report.pdf"


# ==========================================================
# HELPER FUNCTION: Extract numeric item code from ItemDesc
# Example:
# "1534 - NBR 70 490 JT C B Seal" -> "1534"
# "80595 - NR+SBR 55 Rubber HSG" -> "80595"
# ==========================================================
def extract_code(text):
    if pd.isna(text):
        return None

    # Try to match numbers at the beginning first (most common)
    match = re.match(r"^(\d+)", str(text).strip())
    if match:
        return match.group(1)
    
    # If not at beginning, search anywhere
    match = re.search(r"\b(\d{4,6})\b", str(text))
    if match:
        return match.group(1)
    
    # Last resort - any number
    match = re.search(r"(\d+)", str(text))
    if match:
        return match.group(1)

    return None


# ==========================================================
# STEP 1: READ SALES ORDER FILE
# ==========================================================
print("=" * 60)
print("STEP 1: Reading Sales Order file...")
print("=" * 60)

sales_df = pd.read_excel(SALES_FILE, engine="xlrd")

# Remove extra spaces from column names
sales_df.columns = [str(col).strip() for col in sales_df.columns]

print(f"Sales file columns: {list(sales_df.columns)}")
print(f"Total rows in sales file: {len(sales_df)}")

# Required columns in sales file
sales_item_col = "ItemDesc"
invoice_col = "InvoiceQty"
bal_qty_col = "Bal_Qty"

# Extract item code from ItemDesc
sales_df["Item_Code"] = sales_df[sales_item_col].apply(extract_code)

# Filter out rows with no item code
sales_df = sales_df[sales_df["Item_Code"].notna()].copy()
print(f"Rows with valid Item_Code: {len(sales_df)}")

# Show sample of extracted codes
print("\nSample of extracted item codes from Sales file:")
for i, row in sales_df.head(10).iterrows():
    print(f"  {row['Item_Code']} - {str(row[sales_item_col])[:60]}...")


# ==========================================================
# STEP 2: FIND HEADER ROW IN STOCK FILE
# ==========================================================
print("\n" + "=" * 60)
print("STEP 2: Reading Stock file...")
print("=" * 60)

raw_stock = pd.read_excel(STOCK_FILE, engine="xlrd", header=None)

header_row = None

for i in range(len(raw_stock)):
    # Replace NaN with empty string and convert to lowercase
    row_values = (
        raw_stock.iloc[i]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .tolist()
    )

    if "itemdesc" in row_values:
        header_row = i
        break

if header_row is None:
    raise Exception("Could not find header row containing 'ItemDesc'.")

print(f"Header row found at row index: {header_row}")

# Read stock file again using detected header row
stock_df = pd.read_excel(
    STOCK_FILE,
    engine="xlrd",
    header=header_row
)

# Clean column names
stock_df.columns = [str(col).strip() for col in stock_df.columns]

print(f"Stock file columns: {list(stock_df.columns)[:15]}...")
print(f"Total rows in stock file: {len(stock_df)}")


# ==========================================================
# STEP 3: DETECT IMPORTANT COLUMNS IN STOCK FILE
# ==========================================================
def find_column(columns, keywords):
    """
    Find the first column containing all keywords.
    """
    for col in columns:
        col_lower = col.lower()
        if all(keyword.lower() in col_lower for keyword in keywords):
            return col
    return None


# Detect item description column
stock_item_col = find_column(stock_df.columns, ["item", "desc"])
if stock_item_col is None:
    # Try other variations
    for col in stock_df.columns:
        if "itemdesc" in col.lower() or "item desc" in col.lower():
            stock_item_col = col
            break

# Detect closing stock column
closing_col = None
for col in stock_df.columns:
    col_lower = col.lower()
    if "closing" in col_lower and "stock" in col_lower:
        closing_col = col
        break

# If not found, try alternative names
if closing_col is None:
    for col in stock_df.columns:
        if "closing" in col.lower():
            closing_col = col
            break

# Detect department column (OPName in your data)
dept_col = None
for col in stock_df.columns:
    col_lower = col.lower()
    if "opname" in col_lower or "department" in col_lower or "dept" in col_lower:
        dept_col = col
        break

if stock_item_col is None:
    raise Exception("ItemDesc column not found in stock file.")

if closing_col is None:
    raise Exception("Closing Stock column not found in stock file.")

print(f"\nStock Item Column   : {stock_item_col}")
print(f"Closing Stock Column: {closing_col}")
print(f"Department Column   : {dept_col}")


# ==========================================================
# STEP 4: PREPARE STOCK DATA
# ==========================================================
print("\n" + "=" * 60)
print("STEP 4: Preparing stock data...")
print("=" * 60)

# Extract item code from stock file
stock_df["Item_Code"] = stock_df[stock_item_col].apply(extract_code)

# Remove rows with no item code
stock_df = stock_df[stock_df["Item_Code"].notna()].copy()
print(f"Stock rows with valid Item_Code: {len(stock_df)}")

# Show sample of extracted codes from stock
print("\nSample of extracted item codes from Stock file:")
for i, row in stock_df.head(10).iterrows():
    print(f"  {row['Item_Code']} - {str(row[stock_item_col])[:60]}...")

# Convert closing stock to numeric
stock_df[closing_col] = pd.to_numeric(
    stock_df[closing_col],
    errors="coerce"
).fillna(0)


# ==========================================================
# STEP 5: CREATE DEPARTMENT-WISE SUMMARY
# ==========================================================
print("\n" + "=" * 60)
print("STEP 5: Creating department-wise summary...")
print("=" * 60)

if dept_col:
    # Create pivot table for department-wise stock
    dept_summary = stock_df.pivot_table(
        index="Item_Code",
        columns=dept_col,
        values=closing_col,
        aggfunc="sum",
        fill_value=0
    )
    print(f"Department columns found: {list(dept_summary.columns)}")
else:
    # If no department column, create empty dataframe
    print("No department column found - creating summary without department breakdown")
    dept_summary = pd.DataFrame(
        index=stock_df["Item_Code"].dropna().unique()
    )

# Total closing stock
total_stock = (
    stock_df.groupby("Item_Code")[closing_col]
    .sum()
    .rename("Total_Closing_Stock")
)

# Combine department-wise and total stock
dept_summary = dept_summary.join(total_stock, how="outer")

# FIX: Convert index back to column properly
dept_summary.reset_index(inplace=True)

# Ensure Item_Code column exists
if "Item_Code" not in dept_summary.columns:
    if dept_summary.index.name == "Item_Code":
        dept_summary.reset_index(inplace=True)
    else:
        dept_summary["Item_Code"] = dept_summary.index

print(f"Department summary shape: {dept_summary.shape}")
print(f"Department summary columns: {list(dept_summary.columns)}")


# ==========================================================
# STEP 6: MERGE SALES FILE WITH STOCK SUMMARY
# ==========================================================
print("\n" + "=" * 60)
print("STEP 6: Merging sales and stock data...")
print("=" * 60)

# First, ensure both DataFrames have Item_Code as string type for consistent merging
sales_df["Item_Code"] = sales_df["Item_Code"].astype(str)
dept_summary["Item_Code"] = dept_summary["Item_Code"].astype(str)

# Merge
final_df = sales_df.merge(
    dept_summary,
    on="Item_Code",
    how="left"
)

# Fill missing stock values with 0
new_cols = [col for col in final_df.columns if col not in sales_df.columns]
final_df[new_cols] = final_df[new_cols].fillna(0)

print(f"Final merged dataframe shape: {final_df.shape}")
print(f"Number of rows with stock data: {(final_df['Total_Closing_Stock'] > 0).sum()}")


# ==========================================================
# STEP 7: ADD CALCULATIONS
# ==========================================================
print("\n" + "=" * 60)
print("STEP 7: Adding calculations...")
print("=" * 60)

# Calculate shortage (if balance quantity > stock)
final_df["Shortage"] = final_df.apply(
    lambda row: max(0, abs(row["Bal_Qty"]) - row["Total_Closing_Stock"]),
    axis=1
)

# Calculate status
final_df["Stock_Status"] = final_df.apply(
    lambda row: "SUFFICIENT" if row["Total_Closing_Stock"] >= abs(row["Bal_Qty"]) else "INSUFFICIENT",
    axis=1
)

print(f"Items with INSUFFICIENT stock: {(final_df['Stock_Status'] == 'INSUFFICIENT').sum()}")
print(f"Items with SUFFICIENT stock: {(final_df['Stock_Status'] == 'SUFFICIENT').sum()}")


# ==========================================================
# STEP 8: SAVE EXCEL FILE
# ==========================================================
print("\n" + "=" * 60)
print("STEP 8: Saving Excel file...")
print("=" * 60)

# Reorder columns for better readability
base_cols = ["Item_Code", "ItemDesc", "CustName", "SO_No", "SO_Qty", "InvoiceQty", "Bal_Qty", 
             "Total_Closing_Stock", "Shortage", "Stock_Status"]

# Add department columns if they exist
dept_cols = [col for col in final_df.columns if col not in base_cols and col not in sales_df.columns]
ordered_cols = base_cols + dept_cols

# Only keep columns that exist
ordered_cols = [col for col in ordered_cols if col in final_df.columns]
final_df[ordered_cols].to_excel(OUTPUT_EXCEL, index=False)

print(f"Excel file created: {OUTPUT_EXCEL}")


# ==========================================================
# STEP 9: CREATE PDF REPORT
# ==========================================================
print("\n" + "=" * 60)
print("STEP 9: Generating PDF report...")
print("=" * 60)

doc = SimpleDocTemplate(
    OUTPUT_PDF,
    pagesize=landscape(A4),
    rightMargin=20,
    leftMargin=20,
    topMargin=20,
    bottomMargin=20
)

styles = getSampleStyleSheet()
elements = []

# Title
elements.append(
    Paragraph(
        "<b>Sales Order Book Balance with Stock Summary</b>",
        styles["Title"]
    )
)
elements.append(Spacer(1, 12))

# Subtitle with timestamp
from datetime import datetime
elements.append(
    Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"]
    )
)
elements.append(Spacer(1, 20))

# Columns to show in PDF
display_cols = ["Item_Code", "ItemDesc", "CustName", "Bal_Qty", "Total_Closing_Stock", "Shortage", "Stock_Status"]

# Add department columns if they exist
for col in final_df.columns:
    if col not in display_cols and col not in sales_df.columns and "Item" not in col:
        display_cols.append(col)

# Limit to first 200 rows for PDF (can be adjusted)
pdf_df = final_df[display_cols].head(200).copy()
pdf_df = pdf_df.fillna("")

# Truncate long descriptions
pdf_df["ItemDesc"] = pdf_df["ItemDesc"].apply(lambda x: str(x)[:80] + "..." if len(str(x)) > 80 else str(x))

# Convert to list for reportlab
data = [pdf_df.columns.tolist()] + pdf_df.astype(str).values.tolist()

# Create table with better styling
table = Table(data, repeatRows=1)

table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 10),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
    ("TOPPADDING", (0, 0), (-1, 0), 12),
]))

# Color rows based on status
for i, row in pdf_df.iterrows():
    row_num = i + 1  # +1 because header is row 0
    if row["Stock_Status"] == "INSUFFICIENT":
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, row_num), (-1, row_num), colors.HexColor("#fee2e2")),
        ]))
    elif row["Total_Closing_Stock"] > 0:
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, row_num), (-1, row_num), colors.HexColor("#d1fae5")),
        ]))

elements.append(table)

# Add summary statistics
elements.append(Spacer(1, 20))
elements.append(
    Paragraph(
        f"<b>Summary Statistics:</b><br/>"
        f"Total Items Analyzed: {len(final_df)}<br/>"
        f"Items with INSUFFICIENT Stock: {(final_df['Stock_Status'] == 'INSUFFICIENT').sum()}<br/>"
        f"Items with SUFFICIENT Stock: {(final_df['Stock_Status'] == 'SUFFICIENT').sum()}<br/>"
        f"Total Balance Quantity: {final_df['Bal_Qty'].abs().sum():,.0f}<br/>"
        f"Total Closing Stock: {final_df['Total_Closing_Stock'].sum():,.0f}",
        styles["Normal"]
    )
)

# Build PDF
doc.build(elements)

print(f"PDF report created: {OUTPUT_PDF}")
print("\n" + "=" * 60)
print("Process completed successfully!")
print("=" * 60)
print(f"\nGenerated files:")
print(f"1. {OUTPUT_EXCEL}")
print(f"2. {OUTPUT_PDF}")