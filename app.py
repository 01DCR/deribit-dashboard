import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Deribit P&L Tracker", layout="wide")
st.title("📈 Options Trading P&L Dashboard (USD & Crypto)")

# --- SIDEBAR: UPLOAD ---
st.sidebar.header("Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload Deribit Transaction Log", type=['csv'])

if uploaded_file is not None:
    # --- DATA PROCESSING ---
    try:
        # Load Data
        df = pd.read_csv(uploaded_file)
        
        # 1. Clean Column Names
        df.columns = df.columns.str.strip()
        
        # 2. Convert Date
        df['datetime'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='datetime')

        # 3. Filter out Transfers (Deposits/Withdrawals)
        if 'Type' in df.columns:
            df = df[~df['Type'].str.lower().isin(['transfer', 'deposit', 'withdrawal'])]

        # 4. GET THE LATEST PRICE (For USD conversion)
        # We look for the last non-zero Index Price to use as our "Current Price" reference
        if 'Index Price' in df.columns:
            # Forward fill to ensure we get the last valid price even if the very last row is blank
            last_price = df['Index Price'].replace(0, pd.NA).ffill().iloc[-1]
        else:
            last_price = 0
            st.warning("⚠️ 'Index Price' column not found. USD values will be 0.")

        # 5. CALCULATE METRICS (Gross vs Net)
        # Deribit Logic: 
        # 'Cash Flow' is usually Gross P&L (before fees)
        # 'Fee Charged' is the cost
        # 'Change' is usually Net P&L (Cash Flow - Fees)
        
        df['Gross P&L'] = df['Cash Flow']
        df['Fees'] = df['Fee Charged']
        df['Net P&L'] = df['Gross P&L'] - df['Fees']
        
        # Cumulative P&L
        df['Cumulative Net'] = df['Net P&L'].cumsum()
        df['Cumulative Gross'] = df['Gross P&L'].cumsum()

        # Key Totals (Crypto)
        total_gross = df['Gross P&L'].sum()
        total_fees = df['Fees'].sum()
        total_net = df['Net P&L'].sum()
        
        # Key Totals (USD Approx)
        # We multiply the total Crypto P&L by the LATEST price to show what it's worth today
        total_gross_usd = total_gross * last_price
        total_fees_usd = total_fees * last_price
        total_net_usd = total_net * last_price

        # --- DASHBOARD VISUALS ---
        
        # 1. SUMMARY METRICS
        st.markdown(f"### 💵 Current Price Reference: ${last_price:,.2f}")
        
        # Row A: USD View
        st.markdown("#### Performance in USD (Estimated)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Net Profit (USD)", f"${total_net_usd:,.2f}", delta_color="normal")
        col2.metric("Gross Profit (USD)", f"${total_gross_usd:,.2f}", help="P&L before fees")
        col3.metric("Total Fees (USD)", f"-${total_fees_usd:,.2f}", delta_color="inverse")
        
        # Row B: Crypto View
        st.markdown("#### Performance in Crypto (ETH/BTC)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Net Profit", f"{total_net:,.4f}")
        c2.metric("Gross Profit", f"{total_gross:,.4f}")
        c3.metric("Total Fees", f"-{total_fees:,.4f}")
        
        st.divider()

        # 2. EQUITY CURVE (Net vs Gross)
        st.subheader("Gross vs Net Performance")
        
        # We melt the dataframe to plot two lines on one chart
        chart_data = df[['datetime', 'Cumulative Net', 'Cumulative Gross']].melt('datetime', var_name='Type', value_name='P&L')
        
        fig_equity = px.line(chart_data, x='datetime', y='P&L', color='Type',
                             template='plotly_dark',
                             color_discrete_map={"Cumulative Net": "#00CC96", "Cumulative Gross": "#FFA15A"})
        fig_equity.update_traces(line_width=2)
        fig_equity.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
        st.plotly_chart(fig_equity, use_container_width=True)

        # 3. MONTHLY BREAKDOWN
        st.subheader("Monthly Breakdown")
        monthly_stats = df.set_index('datetime').resample('M')[['Gross P&L', 'Fees', 'Net P&L']].sum()
        
        # Add USD Columns to the table
        monthly_stats['Net P&L ($)'] = monthly_stats['Net P&L'] * last_price
        monthly_stats['Fees ($)'] = monthly_stats['Fees'] * last_price
        
        monthly_stats.index = monthly_stats.index.strftime('%B %Y')
        
        # Display with highlighting
        st.dataframe(monthly_stats.style.format("{:,.4f}", subset=['Gross P&L', 'Fees', 'Net P&L'])
                                        .format("${:,.2f}", subset=['Net P&L ($)', 'Fees ($)'])
                                        .background_gradient(subset=['Net P&L'], cmap='RdYlGn'), 
                     use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👈 Upload your CSV in the sidebar to get started.")
