# B2B Invoices — Data Cleaning & Sales Analytics
A full data cleaning and analytics pipeline built on a messy, synthetic B2B sales dataset — using Python (pandas, NumPy, difflib) for cleaning and analysis, and Power BI for an interactive two-page dashboard.

## Objective
Take a deliberately messy sales dataset (missing values, mixed date formats, typos, duplicates, numeric inconsistencies) and turn it into a clean, validated dataset with a documented audit trail — then build a dashboard that reports both the sales insights and the data quality findings.

## Dataset
**Source:** [MockDataFaker — Sample Data for Data Cleaning Practice](https://mockdatafaker.com/sample/sample-data-for-data-cleaning-practice.html) (B2B distribution dataset, seed `cleanprac-demo`, "messy" option enabled)
Synthetic B2B sales dataset (~6,000 rows) with intentionally introduced data quality issues — missing values across most columns, three different date formats mixed in the same column, spelling typos and letter transpositions in text fields, exact and logical duplicate rows, and numeric inconsistencies.
| Column | Description |
|---|---|
| order_date / ship_date | Order and shipment dates |
| invoice_no | Invoice identifier |
| customer_id / customer | Customer identifiers |
| product_id / product | Product identifiers |
| category / segment | Product category and customer segment |
| quantity, unit_cost, unit_price | Order line details |
| revenue, cost, margin | Financial figures |

## Python Pipeline — `b2b_invoices.py`
Processing order matters here: text cleaning runs **before** missing-value imputation, so that `groupby`-based fills correctly group rows that share the same (now standardized) customer/product/category name.
1. **Text editing** — whitespace trimming; typo correction using `difflib.get_close_matches` (category, segment) against a known reference list, and `difflib.SequenceMatcher` (customer, product) grouping variants by frequency, assuming the most common spelling is correct
2. **Missing values** — cross-column recovery via `groupby().transform(ffill/bfill)` (e.g. recovering `invoice_no` from `customer_id` + `order_date`), and formula-based recovery for numeric fields (`revenue = quantity × unit_price`, and reverse combinations); remaining unrecoverable rows handled case by case (one row dropped, a few filled with "Unknown")
3. **Dates** — mixed-format parsing with `pd.to_datetime(..., format='mixed')`; anomalous months (~68 rows on order_date, ~78 on ship_date) diagnosed as day/month transposition and corrected by inversion, confirmed by checking they collapse into the plausible month range
4. **Numeric validation** — cross-checks that `revenue = quantity × unit_price`, `margin = revenue − cost`, `cost = quantity × unit_cost` all hold; all rows passed
5. **Outlier detection** — revenue and quantity outliers computed **per category** (mean + 3×std within each category, not on the whole dataset, since price/quantity ranges differ by product type); investigated the overlap to confirm quantity anomalies (data-entry errors) as the main driver of revenue outliers
6. **Duplicate detection** — 120 exact duplicate rows removed; one true data inconsistency found and corrected (same invoice + product_id assigned two different categories); remaining "duplicate" invoice+product combinations confirmed as legitimate multi-line orders
7. **Feature engineering** — `margin_pct`, `shipping_days`, `order_month`, `order_year`
8. **Aggregate analysis** — total revenue/margin, revenue by category/segment, top 10 customers/products, monthly trend, average shipping days by category
9. **Export** — `B2B_Invoices_Report.xlsx`, multi-sheet

## Output Report — `B2B_Invoices_Report.xlsx`
- **Dataset** — full cleaned dataset with all calculated columns and outlier flags
- **Revenue Outliers / Quantity Outliers** — flagged anomalies, not removed, for manual review
- **Removed Duplicates** — audit trail of the 120 exact duplicates dropped
- **Revenue by Category / Segment, Top 10 Customers, Top 10 Products, Monthly Revenue** — summary sheets

## Key Findings
- **64 revenue outliers**, of which **54** overlap with quantity outliers — anomalous revenue is mostly explained by unusually high order quantities (up to 850 units against a category mean of ~6–10), likely data-entry errors, not price issues
- **120 exact duplicate rows** removed; **1** genuine category-assignment inconsistency corrected
- **segA** accounts for 74% of rows and 87% of total revenue — consistent with it being the core/enterprise customer segment, not a data quality issue
- All numeric relationships (revenue, cost, margin) validated with zero discrepancies after cleaning

## Power BI Dashboard
Two-page interactive report, styled with the **[Dark Ruby — Premium Dark Theme for Executive & Procurement Dashboards](https://community.fabric.microsoft.com/discussions/ThemesGallery/dark-ruby-–-premium-dark-theme-for-executive--procurement-dashboards/5287105)** theme.
**Page 1 — Sales Overview**
- KPI cards: Total Invoices, Total Customers, Total Categories, Total Revenue, Margin Percentage
- Revenue by Customer (Top 10) — funnel-style horizontal bar
- Revenue Composition by Category/Segment — decomposition tree
- Quantity by Category and Revenue by Category — area charts
- Average Shipping Days by Category
- Slicers: Order Month, Categories
**Page 2 — Data Quality**
- KPI cards: Total Rows Processed, Duplicates Removed, Revenue Outliers Flagged, Quantity Outliers Flagged
- Donut chart: Clean Rows vs Flagged Rows
- Flagged Transactions table — invoice, customer, product, category, quantity, revenue, and both outlier flags, filtered to rows with at least one anomaly (via a calculated `Any Flag` column combining `revenue_outlier` OR `quantity_outlier`)
**Key DAX measures**, e.g.:
```dax
Total Rows Processed = COUNTROWS('Dataset')
Duplicates Removed = COUNTROWS('Removed Duplicates')
Revenue Outliers Flagged = CALCULATE(COUNTROWS('Dataset'), 'Dataset'[revenue_outlier] = "Yes")
Quantity Outliers Flagged = CALCULATE(COUNTROWS('Dataset'), 'Dataset'[quantity_outlier] = "Yes")
Clean Rows = [Total Rows Processed] - [Flagged Rows]
```
**Calculated column**, used to filter the Flagged Transactions table:
```dax
Any Flag = IF('Dataset'[revenue_outlier] = "Yes" || 'Dataset'[quantity_outlier] = "Yes", "Yes", "No")
```

## Repository Contents
- `b2b_invoices.csv` — raw, unprocessed source dataset
- `b2b_invoices.py` — full Python cleaning and analysis pipeline
- `B2B_Invoices_Report.xlsx` — multi-sheet export (cleaned dataset, outliers, removed duplicates, summary tables); kept alongside the `.pbix` as a lightweight, universally readable deliverable and audit trail, since the `.pbix` requires Power BI to open and doesn't render in a GitHub preview
- `B2B Invoices.pbix` — interactive two-page Power BI dashboard

## Tools Used
Python (pandas, NumPy, difflib), Excel, Power BI

## Notes
Project built for practice ahead of a Data Analyst internship in Audit/Finance, as a follow-up to the Accounts Payable audit analytics project — this one specifically focused on messy, real-world-style data quality issues rather than a pre-cleaned dataset.
