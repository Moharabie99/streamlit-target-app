import streamlit as st
import pandas as pd

st.set_page_config(page_title="Target Fulfillment App", layout="wide")
st.title("📊 Target Fulfillment & Next Month Target Calculator")

st.markdown("""
Upload the required Excel files from the sales team below.
- *sales.xlsx* – Sales transactions
- *routes.xlsx* – Route and rep mappings
- *target.xlsx* – Store and SKU monthly targets
""")

# File uploaders
sales_file = st.file_uploader("📁 Upload Sales File", type=["xlsx"], key="sales")
routes_file = st.file_uploader("📁 Upload Routes File", type=["xlsx"], key="routes")
target_file = st.file_uploader("📁 Upload Target File", type=["xlsx"], key="target")

# Read & preview uploaded data
if sales_file and routes_file and target_file:
    sales_df = pd.read_excel(sales_file)
    routes_df = pd.read_excel(routes_file)
    target_df = pd.read_excel(target_file)

    st.success("✅ Files uploaded successfully! Here's a quick preview:")

    with st.expander("📋 Preview: Sales Data"):
        st.dataframe(sales_df)

    with st.expander("🗺 Preview: Routes Data"):
        st.dataframe(routes_df)

    with st.expander("🎯 Preview: Target Data"):
        st.dataframe(target_df)

    if st.button("➡ Proceed to KPI Calculation"):
        st.session_state["sales_df"] = sales_df
        st.session_state["routes_df"] = routes_df
        st.session_state["target_df"] = target_df
        st.rerun()
else:
    st.warning("⏳ Waiting for all 3 files to be uploaded...")
# Get uploaded data from session
sales = st.session_state["sales_df"]
routes = st.session_state["routes_df"]
target = st.session_state["target_df"]

# Merge with target on Store_type_id and SKU
sales = sales.merge(target[['store_type_id', 'store_target']].dropna(), on='store_type_id', how='left')
sales = sales.merge(target[['SKU', 'SKU_target']].dropna(), on='SKU', how='left')

# Calculate fulfillment percentages
sales['store_target_fulfillment_%'] = round((sales['order_value'] / sales['store_target']) * 100, 2)
sales['sku_target_fulfillment_%'] = round((sales['order_value'] / sales['SKU_target']) * 100, 2)

# Calculate next month targets
def compute_next_target(actual, target):
    if pd.isna(target) or pd.isna(actual):
        return None
    diff = target - actual
    return actual + diff if diff > 0 else actual  # fill underperformance, hold overachievement

sales['next_month_store_target'] = sales.apply(lambda x: compute_next_target(x['order_value'], x['store_target']), axis=1)
sales['next_month_sku_target'] = sales.apply(lambda x: compute_next_target(x['order_value'], x['SKU_target']), axis=1)

# Select relevant output columns
output_df = sales[[
    'rep_name', 'store_name', 'SKU', 'order_value',
    'store_target', 'store_target_fulfillment_%', 'next_month_store_target',
    'SKU_target', 'sku_target_fulfillment_%', 'next_month_sku_target'
]]

st.subheader("✅ KPI Calculation Results")
st.dataframe(output_df)

# Save to Excel
from io import BytesIO
import openpyxl

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    output_df.to_excel(writer, index=False, sheet_name='KPI_Report')

st.download_button(
    label="📥 Download KPI Report",
    data=buffer,
    file_name="monthly_kpi_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)    