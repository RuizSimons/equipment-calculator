import streamlit as st
import pandas as pd
import datetime
import io

# --- HELPER FUNCTIONS ---
def calculate_pmt(annual_rate, months, principal):
    """Calculates the monthly payment for a loan."""
    if principal <= 0:
        return 0.0
    if annual_rate == 0:
        return principal / months
    monthly_rate = (annual_rate / 100) / 12
    return principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Equipment Sales & CVA Calculator", layout="wide", initial_sidebar_state="expanded")

# --- SIDEBAR: DEALER INPUTS (BACK-END) ---
st.sidebar.header("⚙️ Dealer Inputs (Internal)")
st.sidebar.markdown("---")

st.sidebar.subheader("Equipment Details")
model = st.sidebar.text_input("Machine Model", "Caterpillar 730 ADT")
current_smu = st.sidebar.number_input("Start SMU (Hours)", min_value=0, value=2500, step=100)
dealer_cost = st.sidebar.number_input("Dealer Cost ($)", min_value=0.0, value=250000.0, step=1000.0)
desired_margin = st.sidebar.number_input("Desired Margin (%)", min_value=0.0, value=15.0, step=1.0)

st.sidebar.subheader("Financing & Terms")
term_length = st.sidebar.number_input("Term Length (Months)", min_value=1, value=36, step=12)
down_payment = st.sidebar.number_input("Down Payment ($)", min_value=0.0, value=0.0, step=1000.0)
interest_rate = st.sidebar.number_input("Annual Interest Rate (APR %)", min_value=0.0, value=6.5, step=0.1)
depreciation_rate = st.sidebar.number_input("Annual Depreciation Rate (%)", min_value=0.0, value=12.0, step=1.0, help="Adjust this based on Expected End SMU.")

st.sidebar.subheader("Rental & RPO")
monthly_rental_rate = st.sidebar.number_input("Standard Monthly RPO Rate ($)", min_value=0.0, value=12000.0, step=500.0)
short_term_uplift = st.sidebar.number_input("Short-Term Rental Uplift (%)", min_value=0.0, value=15.0, step=1.0, help="Markup applied to straight rentals compared to RPO.")
equity_factor = st.sidebar.number_input("Rental Equity Factor (%)", min_value=0.0, value=80.0, step=5.0, help="Percentage of rental payment applied to principal.")
conversion_month = st.sidebar.number_input("RPO Conversion Month", min_value=1, value=6, step=1)

st.sidebar.subheader("Customer Value Agreement (CVA)")
expected_usage = st.sidebar.number_input("Expected Monthly Usage (Hours)", min_value=1, value=150, step=10)
pm_cost_per_hour = st.sidebar.number_input("Internal PM Cost per Hour ($)", min_value=0.0, value=15.0, step=1.0)
cva_margin = st.sidebar.number_input("CVA Margin (%)", min_value=0.0, value=20.0, step=1.0)

# --- BACKGROUND CALCULATIONS ---
# 1. Base Numbers
sale_price = dealer_cost * (1 + (desired_margin / 100))
cva_cost_per_month = expected_usage * pm_cost_per_hour * (1 + (cva_margin / 100))
expected_end_smu = current_smu + (expected_usage * term_length)

# 2. Straight Rental Option
straight_rental_rate = monthly_rental_rate * (1 + (short_term_uplift / 100))
rental_total_monthly = straight_rental_rate + cva_cost_per_month

# 3. Rent-to-Buy (RPO) Option
rpo_total_monthly = monthly_rental_rate + cva_cost_per_month
equity_built = conversion_month * monthly_rental_rate * (equity_factor / 100)
buyout_price = max(0, sale_price - equity_built)

# 4. Finance & Repurchase Option
amount_financed = max(0, sale_price - down_payment)
finance_pmt = calculate_pmt(interest_rate, term_length, amount_financed)
finance_total_monthly = finance_pmt + cva_cost_per_month
repurchase_value = sale_price * ((1 - (depreciation_rate / 100)) ** (term_length / 12))


# --- MAIN PAGE: CUSTOMER REPORT (FRONT-END) ---
st.title(f"📊 Equipment Acquisition & CVA Report: {model}")

# Top Metrics Row for SMU and Term Context
st.markdown("### 🚜 Machine Usage Profile")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Start SMU", f"{current_smu:,} hrs")
m2.metric("Est. Monthly Usage", f"{expected_usage:,} hrs")
m3.metric("Term Length", f"{term_length} Months")
m4.metric("Expected End SMU", f"{expected_end_smu:,} hrs")

st.markdown("---")

# Layout with 3 columns for the options
col1, col2, col3 = st.columns(3)

# Option 1: Rental
with col1:
    st.subheader("1️⃣ Straight Rental")
    st.write(f"Short-term rate (Includes {short_term_uplift}% uplift).")
    st.metric("Monthly Equipment Payment", f"${straight_rental_rate:,.2f}")
    st.metric("Monthly CVA (Maintenance)", f"${cva_cost_per_month:,.2f}")
    st.divider()
    st.metric("Total Monthly Out-of-Pocket", f"${rental_total_monthly:,.2f}")
    st.metric("Equity Built", "$0.00")
    st.info("No buyout or repurchase options apply.")

# Option 2: Rent-to-Buy (RPO)
with col2:
    st.subheader("2️⃣ Rent-to-Buy (RPO)")
    st.write(f"Build equity while renting. Assuming buyout at month {conversion_month}.")
    st.metric("Monthly Equipment Payment", f"${monthly_rental_rate:,.2f}")
    st.metric("Monthly CVA (Maintenance)", f"${cva_cost_per_month:,.2f}")
    st.divider()
    st.metric("Total Monthly Out-of-Pocket", f"${rpo_total_monthly:,.2f}")
    st.metric(f"Equity Built (by Month {conversion_month})", f"${equity_built:,.2f}")
    st.success(f"**Final Buyout Price:** ${buyout_price:,.2f}")

# Option 3: Finance & Repurchase
with col3:
    st.subheader("3️⃣ Finance & Repurchase")
    st.write(f"Long-term ownership with exit strategy after {term_length} months.")
    st.metric("Amount Financed", f"${amount_financed:,.2f}", help=f"Sale Price (${sale_price:,.2f}) - Down Payment (${down_payment:,.2f})")
    st.metric("Monthly Finance Payment", f"${finance_pmt:,.2f}")
    st.metric("Monthly CVA (Maintenance)", f"${cva_cost_per_month:,.2f}")
    st.divider()
    st.metric("Total Monthly Out-of-Pocket", f"${finance_total_monthly:,.2f}")
    st.success(f"**Est. Repurchase Value:** ${repurchase_value:,.2f}")

st.markdown("---")

# --- GENERATE DOWNLOADABLE EXCEL REPORT ---
st.subheader("📥 Download Customer Report")
st.write("Generate a clean Excel (.xlsx) file to share with your customer.")

# Create a DataFrame for the report
report_data = {
    "Description": [
        "Machine Model", 
        "Start SMU (Hours)",
        "Expected End SMU (Hours)",
        "Term Length (Months)", 
        "Amount Financed",
        "Monthly Equipment Payment", 
        "Monthly CVA Cost", 
        "Total Monthly Out-of-Pocket", 
        "Equity Built", 
        "Buyout / Repurchase Value"
    ],
    "1. Straight Rental": [
        model, f"{current_smu:,}", f"{expected_end_smu:,}", str(term_length), 
        "N/A",
        f"${straight_rental_rate:,.2f}", f"${cva_cost_per_month:,.2f}", f"${rental_total_monthly:,.2f}", 
        "$0.00", "N/A"
    ],
    "2. Rent-to-Buy (RPO)": [
        model, f"{current_smu:,}", f"{expected_end_smu:,}", str(term_length), 
        "N/A",
        f"${monthly_rental_rate:,.2f}", f"${cva_cost_per_month:,.2f}", f"${rpo_total_monthly:,.2f}", 
        f"${equity_built:,.2f}", f"Buyout: ${buyout_price:,.2f}"
    ],
    "3. Finance & Repurchase": [
        model, f"{current_smu:,}", f"{expected_end_smu:,}", str(term_length), 
        f"${amount_financed:,.2f}",
        f"${finance_pmt:,.2f}", f"${cva_cost_per_month:,.2f}", f"${finance_total_monthly:,.2f}", 
        "Builds Ownership", f"Repurchase: ${repurchase_value:,.2f}"
    ]
}

df_report = pd.DataFrame(report_data)

# Convert DataFrame to Excel in memory
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df_report.to_excel(writer, index=False, sheet_name='Proposal')
    
    # Auto-adjust column widths for better Excel readability
    worksheet = writer.sheets['Proposal']
    for idx, col in enumerate(df_report.columns):
        series = df_report[col]
        max_len = max((
            series.astype(str).map(len).max(),
            len(str(series.name))
        )) + 2
        worksheet.column_dimensions[chr(65 + idx)].width = max_len

# Download Button
st.download_button(
    label="Download Customer Proposal (Excel)",
    data=buffer.getvalue(),
    file_name=f"{model.replace(' ', '_')}_Proposal_{datetime.date.today()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
