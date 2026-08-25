# ============================================
# B2B Invoices : Data Cleaning & Sales Analytics
# ============================================

## IMPORT LIBRARIES
import pandas as pd
import numpy as np

## READ CSV
df = pd.read_csv('b2b_invoices.csv')
print(df.head())
print(df.info())
#print(df.describe())


# ----------------
## TEXT EDITING
# ----------------

print("\nTEXT EDITING")

# Trim whitespace
df['category'] = df['category'].str.strip()
df['customer'] = df['customer'].str.strip()
df['product'] = df['product'].str.strip()
df['segment'] = df['segment'].str.strip()

# Look for typo
print("\nTotal categories found in raw data:", df['category'].nunique())
print(df['category'].unique())
print("Total segments found in raw data:", df['segment'].nunique())
print(df['segment'].unique())
print("Total customers found in raw data:", df['customer'].nunique())
print(df['customer'].unique())
print("Total products found in raw data:", df['product'].nunique())
print(df['product'].unique())

# Fix categories
from difflib import get_close_matches
accurate_categories = [                                                     # categories I know are correct
    'paper & tissue', 'cleaning supplies', 'breakroom supplies',
    'copy paper', 'office products'
]
def fix_category(valuecategory):
    if pd.isnull(valuecategory):                                           # if value is Nan, keep it like this
        return valuecategory
    match = get_close_matches(valuecategory, accurate_categories, n=1, cutoff=0.6)   # compare value with correct categories (similarity score at least 60%, return 1 value)
    return match[0] if match else valuecategory                            # if match has something in it return 1 element in the list, else return original value

df['category'] = df['category'].apply(fix_category)                         # apply function to every category
print("Total categories found after data preprocessing:", df['category'].nunique())    # check n. of categories after processing (should be 5)

# Fix segments (same as categories)
accurate_segments = ['segA', 'segB', 'segC', 'segD']
def fix_segment(valuesegment):
    if pd.isnull(valuesegment):
        return valuesegment
    match = get_close_matches(valuesegment, accurate_segments, n=1, cutoff=0.5)
    return match[0] if match else valuesegment

df['segment'] = df['segment'].apply(fix_segment)
print("Total segments found after data preprocessing:", df['segment'].nunique())

# Fix customer and product
from difflib import SequenceMatcher

def find_similar_group(value, known_values, soglia=0.85):                # compare 2 str with similarity score at least 85%
    for v in known_values:
        if SequenceMatcher(None, value, v).ratio() >= soglia:
            return v
    return value

# Fix customer
customer_count = df['customer'].dropna().value_counts()                  # sort values by frequency (the most common is likely the correct one)

cleaned_values_customer = []                        
for valuecustomer in customer_count.index:                              # iterate through names by frequency (from most to least common)
    match = find_similar_group(valuecustomer, cleaned_values_customer)    # for each one, check if it matches something already in clean_values
    cleaned_values_customer.append(match if match != valuecustomer else valuecustomer)

map_customer = dict(zip(customer_count.index,                           # build a dictionary mapping each original name (key) to its corrected version (value)
    [find_similar_group(v, list(dict.fromkeys(cleaned_values_customer))) for v in customer_count.index]))

df['customer'] = df['customer'].map(map_customer).fillna(df['customer'])
df['customer'] = df['customer'].replace({
    'Dazzling Janitors of Foerstdale': 'Dazzling Janitors of Forestdale'})     # typo missed by the automatic process
print("Total customers found after data preprocessing:", df['customer'].nunique())   
print(sorted(df['customer'].dropna().unique())[:30])       

# Fix product (same as product)
product_count = df['product'].dropna().value_counts()  # <- aggiunto dropna()
cleaned_values_product = []
for valueproduct in product_count.index:
    match = find_similar_group(valueproduct, cleaned_values_product)
    cleaned_values_product.append(match if match != valueproduct else valueproduct)

mappa_product = dict(zip(product_count.index, 
    [find_similar_group(v, list(dict.fromkeys(cleaned_values_product))) for v in product_count.index]))

df['product'] = df['product'].map(mappa_product).fillna(df['product'])
print("Total producs found after data preprocessing:", df['product'].nunique())
print(sorted(df['product'].dropna().unique())[:30])


# ----------------
## MISSING VALUES
# ----------------

print("\nMISSING VALUES")

# Check missing values before changes
print("\nMissing values (from raw data):") 
print(df.isnull().sum())

# Invoice_no missing (check customer_id and order_id)
df['invoice_no'] = df.groupby(['customer_id', 'order_date'], dropna=False)['invoice_no'].transform(lambda x: x.ffill().bfill())
# Customer_id missing (check invoice_no and order_id)
df['customer_id'] = df.groupby('invoice_no', dropna=False)['customer_id'].transform(lambda x: x.ffill().bfill())
# Order_date missing (check customer_id and invoice_no)
df['order_date'] = df.groupby(['invoice_no', 'customer_id'], dropna=False)['order_date'].transform(lambda x: x.ffill().bfill())
# Customer missing (check customer_id and invoice_no, customer_id)
df['customer'] = df.groupby(['invoice_no', 'customer_id', 'order_date'], dropna=False)['customer'].transform(lambda x: x.ffill().bfill())
# Product missing (check product_id)
df['product'] = df.groupby('product_id', dropna=False)['product'].transform(lambda x: x.ffill().bfill())
# Category missing (check product)
df['category'] = df.groupby('product', dropna=False)['category'].transform(lambda x: x.ffill().bfill())
# Product_id missing (check product)
df['product_id'] = df.groupby('product', dropna=False)['product_id'].transform(lambda x: x.ffill().bfill())
# Segment missing (check category)
df['segment'] = df.groupby('category', dropna=False)['segment'].transform(lambda x: x.ffill().bfill())
# Ship_date missing (check invoice_no, order_id, customer_id, order_date)
df['ship_date'] = df.groupby(['invoice_no', 'customer_id', 'order_date'], dropna=False)['ship_date'].transform(lambda x: x.ffill().bfill())

# Revenue missing --> Revenue: Quantity × Unit Price
df['revenue'] = df['revenue'].fillna(df['quantity'] * df['unit_price'])
# Revenue missing --> Revenue: Cost + Margin 
df['revenue'] = df['revenue'].fillna(df['cost'] + df['margin'])
# Cost Missing --> Cost : Quantity × Unit Cost
df['cost'] = df['cost'].fillna(df['quantity'] * df['unit_cost'])
# Cost Missing (2) --> Cost : Revenue - Margin
df['cost'] = df['cost'].fillna(df['revenue'] - df['margin'])
# Margin missing --> Margin: Revenue − Cost
df['margin'] = df['margin'].fillna(df['revenue'] - df['cost'])
# Quantity missing --> Revenue / Unit Price
df['quantity'] = df['quantity'].fillna(df['revenue'] / df['unit_price'])
# Quantity missing (2)--> Cost / Unit Cost 
df['quantity'] = df['quantity'].fillna(df['cost'] / df['unit_cost'])
# Unit Price missing --> Revenue / Quantity
df['unit_price'] = df['unit_price'].fillna(df['revenue'] / df['quantity'])
# Unit Cost missing --> Cost / Quantity
df['unit_cost'] = df['unit_cost'].fillna(df['cost'] / df['quantity'])

# Check missing values after changes
print("\nMissing values (after changes):")
print(df.isnull().sum())

# Check remaining missing values
print("\nRemaining missing values list (after changes):")
print(df[df.isnull().any(axis=1)])
# Drop line without numeric values
df = df.drop(index=4035)
# Fill product_id and customer missing values
df['product_id'] = df['product_id'].fillna('Unknown')
df['customer'] = df['customer'].fillna('Unknown')

# ----------------
## DATE
# ----------------

print("\nDATES")

# Date conversion
df['order_date'] = pd.to_datetime(df['order_date'], format='mixed')
df['ship_date'] = pd.to_datetime(df['ship_date'], format='mixed')

# Check dates with missing values
print("\nOrder_date with missing values:", df['order_date'].isnull().sum())
print("Ship_date with missing values:", df['ship_date'].isnull().sum())

# Check if dates are anomalous 
print("\n", df['order_date'].dt.to_period('M').value_counts())
# Isolate order_date rows falling outside the plausible months (July, August)
anomalous_months = df[~df['order_date'].dt.month.isin([7, 8])]
print(f"\nAnomalous months order_date: {len(anomalous_months) - df['order_date'].isnull().sum()}")
# Test hypothesis: day/month were swapped during parsing -> try inverting them
correct_date = anomalous_months['order_date'].apply(lambda d: d.replace(month=d.day, day=d.month) if d.day <= 12 else d)
# Check: after inversion, do these dates now fall into July/August?
print(f"New months they fall into:")
print(f"{correct_date.dt.month.value_counts()}")
# Apply the correction to the original dataframe
df.loc[anomalous_months.index, 'order_date'] = correct_date
# Verify: month distribution should now be clean, only July/August
print("Correct months order_date:")
print(df['order_date'].dt.to_period('M').value_counts())

# Check if dates are anomalous 
print("\n", df['ship_date'].dt.to_period('M').value_counts())
# Same process for ship_date, plausible months are July, August, September (!remember to consider missing values)
anomalous_months_ship = df[~df['ship_date'].dt.month.isin([7, 8, 9])]
print(f"\nAnomalous months ship_date: {len(anomalous_months_ship) - (df['ship_date'].isnull().sum())}")
# Invert day/month where possible (skip NaT values with pd.notnull check)
correct_date_ship = anomalous_months_ship['ship_date'].apply(lambda d: d.replace(month=d.day, day=d.month) if pd.notnull(d) and d.day <= 12 else d)
print(f"New months they fall into:")
print(f"{correct_date_ship.dt.month.value_counts()}")
# Apply the correction
df.loc[anomalous_months_ship.index, 'ship_date'] = correct_date_ship
# Verify final distribution
print("Correct months ship_date:")
print(df['ship_date'].dt.to_period('M').value_counts())


# ----------------
## NUMERIC VALIDATION
# ----------------

print("\nNUMERICAL VALIDATION")

# check if revenue = quantity * unit_price (within a small tolerance for rounding)
df['revenue_check'] = df['quantity'] * df['unit_price']
mismatches_revenue = df[abs(df['revenue'] - df['revenue_check']) > 0.01]

# check if margin = revenue - cost
df['margin_check'] = df['revenue'] - df['cost']
mismatches_margin = df[abs(df['margin'] - df['margin_check']) > 0.01]

# check if cost = quantity * unit_cost
df['cost_check'] = df['quantity'] * df['unit_cost']
mismatches_cost = df[abs(df['cost'] - df['cost_check']) > 0.01]

if mismatches_revenue.empty:
    print("\nAll revenue figures check out")
else:
    print(mismatches_revenue)
if mismatches_margin.empty:
    print("All margin figures check out")
else:
    print(mismatches_margin)
if mismatches_cost.empty:
    print("All cost figures check out")
else:
    print(mismatches_cost)


# ----------------
## OUTLIER DETECTION
# ----------------

print("\nOUTLIER DETECTION")

# STEP 1: revenue outliers, calculated per category (not on the whole dataset, since different product categories have different price ranges)
category_stats = df.groupby('category')['revenue'].agg(['mean', 'std']).reset_index()
category_stats.columns = ['category', 'cat_mean_revenue', 'cat_std_revenue']
df = df.merge(category_stats, on='category', how='left')

df['revenue_limit'] = df['cat_mean_revenue'] + 3 * df['cat_std_revenue']
df['revenue_outlier'] = np.where(df['revenue'] > df['revenue_limit'], 'Yes', 'No')

print(f"\nRevenue outliers found: {(df['revenue_outlier'] == 'Yes').sum()}")

# STEP 2: investigate what's driving the revenue outliers
revenue_outliers = df[df['revenue_outlier'] == 'Yes'].sort_values('revenue', ascending=False)
print(revenue_outliers[['invoice_no', 'customer', 'product', 'category', 'quantity', 'unit_price', 'revenue']])

# check quantity distribution to confirm the hypothesis
print(df.groupby('category')['quantity'].describe())

# STEP 3: quantity outliers, same per-category logic
category_stats_qty = df.groupby('category')['quantity'].agg(['mean', 'std']).reset_index()
category_stats_qty.columns = ['category', 'cat_mean_qty', 'cat_std_qty']
df = df.merge(category_stats_qty, on='category', how='left')

df['quantity_limit'] = df['cat_mean_qty'] + 3 * df['cat_std_qty']
df['quantity_outlier'] = np.where(df['quantity'] > df['quantity_limit'], 'Yes', 'No')

print(f"Quantity outliers found: {(df['quantity_outlier'] == 'Yes').sum()}")

# STEP 4: confirm overlap — are revenue outliers mostly explained by quantity outliers?
overlap = df[(df['revenue_outlier'] == 'Yes') & (df['quantity_outlier'] == 'Yes')]
print(f"Revenue outliers also flagged as quantity outliers: {len(overlap)} out of {(df['revenue_outlier'] == 'Yes').sum()}")

# check the remaining 10 outliers not explaines by quantity 
unexplained = df[(df['revenue_outlier'] == 'Yes') & (df['quantity_outlier'] == 'No')]
print(unexplained[['invoice_no', 'customer', 'product', 'quantity', 'unit_price', 'revenue']])

# clean up helper columns used only for threshold calculation
df = df.drop(columns=['cat_mean_revenue', 'cat_std_revenue', 'revenue_limit',
                       'cat_mean_qty', 'cat_std_qty', 'quantity_limit'])


# ----------------
## DUPLICATE DETECTION
# ----------------

print("\nDUPLICATE DETECTION")

# find duplicate rows by invoice_no and product_id 
print("\nNumber of possible duplicates: ", df.duplicated(subset=['invoice_no', 'product_id']).sum())
logical_duplicates = df[df.duplicated(subset=['invoice_no', 'product_id'], keep=False)]
print("Possible duplicates: ", logical_duplicates[['invoice_no', 'customer', 'product_id', 'category', 'quantity']].sort_values('invoice_no'))

# split by case
true_duplicates = df[df.duplicated(subset=['invoice_no', 'product_id', 'quantity', 'customer'], keep=False)]
print(f"True duplicates (identical rows): {len(true_duplicates)}")

# drop true duplicates
df = df.drop_duplicates(subset=['invoice_no', 'product_id', 'quantity', 'customer'], keep='first')

# check whats remaining: probably cases with same invoice+product, but different data values)
remaining = df[df.duplicated(subset=['invoice_no', 'product_id'], keep=False)]
print(f"Remaining inconsistent rows (same invoice+product, different data): {len(remaining)}")
print(remaining[['invoice_no', 'customer', 'product_id', 'category', 'quantity']].sort_values('invoice_no'))

# check if the problem is quantity (normal) or category (true error) 
check = df[df.duplicated(subset=['invoice_no', 'product_id'], keep=False)]
category_mismatch = check.groupby(['invoice_no', 'product_id'])['category'].nunique()
real_errors = category_mismatch[category_mismatch > 1]
print(real_errors)

# based on results: check if product_id 51 occurs elsewhere with a consisten category 
print(df[df['product_id'] == 51][['invoice_no', 'product', 'category']].drop_duplicates())
# based on results: apply changes
df.loc[(df['invoice_no'] == 575) & (df['product_id'] == 51) & (df['category'] == 'copy paper'), 'category'] = 'cleaning supplies'


# ----------------
## FEATURE ENGINEERING
# ----------------

print("\nFEATURE ENGINEERING")

# margin percentage
df['margin_pct'] = (df['margin'] / df['revenue']) * 100

# shipping time in days
df['shipping_days'] = (df['ship_date'] - df['order_date']).dt.days

# month/year for time-based analysis
df['order_month'] = df['order_date'].dt.to_period('M')
df['order_year'] = df['order_date'].dt.year

print("\n", df[['revenue', 'margin', 'margin_pct', 'shipping_days', 'order_month']].head())


# ----------------
## AGGREGATE ANALYSIS
# ----------------

print("\nAGGREGATE ANALYSIS")

# overall totals
total_revenue = df['revenue'].sum()
total_margin = df['margin'].sum()
avg_margin_pct = df['margin_pct'].mean()

print(f"\nTotal Revenue: {total_revenue:,.2f}")
print(f"Total Margin: {total_margin:,.2f}")
print(f"Average Margin %: {avg_margin_pct:.2f}%")

# revenue by category
revenue_by_category = df.groupby('category')['revenue'].sum().sort_values(ascending=False)
print(f"Revenue by Category: {revenue_by_category}")

# revenue by segment
revenue_by_segment = df.groupby('segment')['revenue'].sum().sort_values(ascending=False)
print(f"Revenue by Segment: {revenue_by_segment}")
# based on results: check n. of rows (to see if )
print(df['segment'].value_counts())

# top 10 customers by revenue
top_customers = df.groupby('customer')['revenue'].sum().sort_values(ascending=False).head(10)
print(f"Top 10 Customers: {top_customers}")

# top 10 products by revenue
top_products = df.groupby('product')['revenue'].sum().sort_values(ascending=False).head(10)
print(f"Top 10 Products: {top_products}")

# monthly revenue trend
monthly_revenue = df.groupby('order_month')['revenue'].sum()
print(f"Monthly Revenue Trend: {monthly_revenue}")

# average shipping days per category
avg_shipping_per_category = df.groupby('category')['shipping_days'].mean().round(2)
print(f"Avg Shipping Days per Category: {avg_shipping_per_category}")

# ----------------
## OUTPUT
# ----------------

print("\nEXPORT")

with pd.ExcelWriter("B2B_Invoices_Report.xlsx") as writer:

    # full cleaned dataset
    df.to_excel(writer, sheet_name="Dataset", index=False)

    # revenue outliers
    revenue_outliers.to_excel(writer, sheet_name="Revenue Outliers", index=False)
    # quantity outliers
    quantity_outliers = df[df['quantity_outlier'] == 'Yes'].sort_values('quantity', ascending=False)
    quantity_outliers.to_excel(writer, sheet_name="Quantity Outliers", index=False)

    # true duplicates removed (for reference/audit trail)
    true_duplicates.to_excel(writer, sheet_name="Removed Duplicates", index=False)

    # revenue by category
    revenue_by_category.to_excel(writer, sheet_name="Revenue by Category")

    # revenue by segment
    revenue_by_segment.to_excel(writer, sheet_name="Revenue by Segment")

    # top customers
    top_customers.to_excel(writer, sheet_name="Top 10 Customers")

    # top products
    top_products.to_excel(writer, sheet_name="Top 10 Products")

    # monthly trend
    monthly_revenue.to_excel(writer, sheet_name="Monthly Revenue")

print("\nReport successfully created: B2B_Invoices_Report.xlsx")