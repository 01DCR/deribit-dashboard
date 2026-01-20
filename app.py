import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Deribit P&L Tracker", layout="wide")
st.title("📈 Options Trading P&L Dashboard (Daily Close)")

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
        # Create a "Day" column for grouping
        df['Day'] = df['datetime'].dt.date
        df = df.sort_values(by='datetime')

        # 3. Filter out Transfers (Deposits/Withdrawals)
        if 'Type' in df.columns:
            df = df[~df['Type'].str.lower().isin(['transfer', 'deposit', 'withdrawal'])]

        # 4. GET THE LATEST PRICE (For USD conversion)
        if 'Index Price' in df.columns:
            # Forward fill to ensure we get the last valid price
            last_price = df['Index Price'].replace(0, pd.NA).ffill().iloc[-1]
        else:
            last_price = 0
            st.warning("⚠️ 'Index Price' column not found. USD values will be 0.")

        # 5. CALCULATE RAW METRICS
        df['Gross P&L'] = df['Cash Flow']
        df['Fees'] = df['Fee Charged']
        df['Net P&L'] = df['Gross P&L'] - df['Fees']

        # 6. GROUP BY DAY (The Fix for "Last Value of the Day")
        # Instead of cumsum on every trade, we sum the day's results first.
        daily_ledger = df.groupby('Day')[['Gross P&L', 'Fees', 'Net P&L']].sum()
        
        # Calculate Cumulative Results based on DAILY totals
        daily_ledger['Cumulative Net'] = daily_ledger['Net P&L'].cumsum()
        daily_ledger['Cumulative Gross'] = daily_ledger['Gross P&L'].cumsum()
        
        # Add USD Estimates to the Daily Ledger
        daily_ledger['Net ($)'] = daily_ledger['Net P&L'] * last_price
        daily_ledger['Fees ($)'] = daily_ledger['Fees'] * last_price
        daily_ledger['Gross ($)'] = daily_ledger['Gross P&L'] * last_price

        # --- DASHBOARD STATS ---
        
        # Key Totals
        total_net = daily_ledger['Net P&L'].sum()
        total_gross = daily_ledger['Gross P&L'].sum()
        total_fees = daily_ledger['Fees'].sum()
        
        total_net_usd = total_net * last_price
        total_gross_usd = total_gross * last_price
        total_fees_usd = total_fees * last_price

        # 1. SUMMARY METRICS
        st.markdown(f"### 💵 Current Price Reference: ${last_price:,.2f}")
        
        st.markdown("#### Performance in USD")
        col1, col2, col3 = st.columns(3)
        col1.metric("Net Profit (USD)", f"${total_net_usd:,.2f}", delta_color="normal")
        col2.metric("Gross Profit (USD)", f"${total_gross_usd:,.2f}", help="Before Fees")
        col3.metric("Total Fees (USD)", f"-${total_fees_usd:,.2f}", delta_color="inverse")
        
        st.divider()

        # 2. EQUITY CURVE (Daily Close)
        st.subheader("Account Growth (Daily Close)")
        
        # Prepare data for plotting
        # We reset index so 'Day' becomes a column we can plot
        plot_data = daily_ledger.reset_index()
        plot_data = plot_data[['Day', 'Cumulative Net', 'Cumulative Gross']].melt('Day', var_name='Type', value_name='P&L')
        
        fig_equity = px.line(plot_data, x='Day', y='P&L', color='Type',
                             template='plotly_dark',
                             title='Cumulative P&L (End of Day Value)',
                             color_discrete_map={"Cumulative Net": "#00CC96", "Cumulative Gross": "#FFA15A"})
        
        # Add markers so you can see the specific daily close points
        fig_equity.update_traces(mode="lines+markers", line_width=2)
        fig_equity.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
        st.plotly_chart(fig_equity, use_container_width=True)

        # 3. DAILY BREAKDOWN TABLE
        st.subheader("📝 Daily Ledger")
        
        # Format the dataframe for display
        # We sort descending so the most recent day is at the top
        display_table = daily_ledger.sort_index(ascending=False).copy()
        
        st.dataframe(
            display_table.style
            .format("{:,.4f}", subset=['Gross P&L', 'Fees', 'Net P&L'])
            .format("${:,.2f}", subset=['Gross ($)', 'Fees ($)', 'Net ($)'])
            .background_gradient(subset=['Net P&L'], cmap='RdYlGn'),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👈 Upload your CSV in the sidebar to get started.")
