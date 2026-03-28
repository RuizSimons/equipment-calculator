import streamlit as st
import pandas as pd
import datetime

# --- HELPER FUNCTIONS ---
def calculate_pmt(annual_rate, months, principal):
    """Calculates the monthly payment for a loan."""
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
current_smu = st.sidebar.number_input("Current SMU (Hours)", min_value=0, value=2500, step=100)
dealer_cost = st.sidebar.number_input("Dealer Cost ($)", min_value=0.0, value=250000.0, step=1000.0)
desired_margin = st.sidebar.number_input("Desired Margin (%)", min_value=0.0, value=15.0, step=1.0)

st.sidebar.subheader("Financing & Terms")
term_length = st.sidebar.number_input("Term Length (Months)", min_value=1, value=36, step=12)
interest_rate = st.sidebar.number_input("Annual Interest Rate (APR %)", min_value=0.0, value=6.5, step=0.1)
depreciation_rate = st.sidebar.number_input("Annual Depreciation Rate (%)", min_value=0.0, value=12.0, step=1.0)

st.sidebar.subheader("Rental & RPO")
monthly_rental_rate = st.sidebar.number_input("Standard Monthly Rental ($)", min_value=0.0, value=12000.0, step=500.0)
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

# 2. Straight Rental Option
rental_total_monthly = monthly_rental_rate + cva_cost_per_month

# 3. Rent-to-Buy (RPO) Option
equity_built = conversion_month * monthly_rental_rate * (equity_factor / 100)
buyout_price = max(0, sale_price - equity_built)

# 4. Finance & Repurchase Option
finance_pmt = calculate_pmt(interest_rate, term_length, sale_price)
finance_total_monthly = finance_pmt + cva_cost_per_month
repurchase_value = sale_price * ((1 - (depreciation_rate / 100)) ** (term_length / 12))


# --- MAIN PAGE: CUSTOMER REPORT (FRONT-END) ---
st.title(f"📊 Equipment Acquisition & CVA Report: {model}")
st.write(f"**Current SMU:** {current_smu:,} hours | **Term Length:** {term_length} Months | **Est. Usage:** {expected_usage} hrs/mo")
st.markdown("---")

# Layout with 3 columns for the options
col1, col2, col3 = st.columns(3)

# Option 1: Rental
with col1:
    st.subheader("1️⃣ Straight Rental")
    st.write("Best for short-term needs without long-term commitment.")
    st.metric("Monthly Equipment Payment", f"${monthly_rental_rate:,.2f}")
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
    st.metric("Total Monthly Out-of-Pocket", f"${rental_total_monthly:,.2f}")
    st.metric(f"Equity Built (by Month {conversion_month})", f"${equity_built:,.2f}")
    st.success(f"**Final Buyout Price:** ${buyout_price:,.2f}")

# Option 3: Finance & Repurchase
with col3:
    st.subheader("3️⃣ Finance & Repurchase")
    st.write(f"Long-term ownership with guaranteed exit strategy after {term_length} months.")
    st.metric("Monthly Finance Payment", f"${finance_pmt:,.2f}")
    st.metric("Monthly CVA (Maintenance)", f"${cva_cost_per_month:,.2f}")
    st.divider()
    st.metric("Total Monthly Out-of-Pocket", f"${finance_total_monthly:,.2f}")
    st.metric("Target Sale Price", f"${sale_price:,.2f}")
    st.success(f"**Est. Repurchase Value:** ${repurchase_value:,.2f}")

st.markdown("---")

# --- GENERATE DOWNLOADABLE REPORT ---
st.subheader("📥 Download Customer Report")
st.write("Generate a clean CSV file to share with your customer.")

# Create a DataFrame for the report
report_data = {
    "Description": [
        "Machine Model", 
        "Current SMU", 
        "Term Length (Months)", 
        "Monthly Equipment Payment", 
        "Monthly CVA Cost", 
        "Total Monthly Out-of-Pocket", 
        "Equity Built", 
        "Buyout / Repurchase Value"
    ],
    "1. Straight Rental": [
        model, str(current_smu), str(term_length), 
        f"${monthly_rental_rate:,.2f}", f"${cva_cost_per_month:,.2f}", f"${rental_total_monthly:,.2f}", 
        "$0.00", "N/A"
    ],
    "2. Rent-to-Buy (RPO)": [
        model, str(current_smu), str(term_length), 
        f"${monthly_rental_rate:,.2f}", f"${cva_cost_per_month:,.2f}", f"${rental_total_monthly:,.2f}", 
        f"${equity_built:,.2f}", f"Buyout: ${buyout_price:,.2f}"
    ],
    "3. Finance & Repurchase": [
        model, str(current_smu), str(term_length), 
        f"${finance_pmt:,.2f}", f"${cva_cost_per_month:,.2f}", f"${finance_total_monthly:,.2f}", 
        "Builds Ownership", f"Repurchase: ${repurchase_value:,.2f}"
    ]
}

df_report = pd.DataFrame(report_data)

# Convert DataFrame to CSV
csv = df_report.to_csv(index=False).encode('utf-8')

# Download Button
st.download_button(
    label="Download Customer Proposal (CSV)",
    data=csv,
    file_name=f"{model.replace(' ', '_')}_Proposal_{datetime.date.today()}.csv",
    mime="text/csv",
)