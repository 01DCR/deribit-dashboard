import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Deribit P&L Tracker", layout="wide")

st.title("📈 Options Trading P&L Dashboard")

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
        
        # 2. Convert Date (Format: "20 Dec 2025 08:00:00")
        df['datetime'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='datetime')

        # 3. Filter out Transfers (Deposits/Withdrawals)
        if 'Type' in df.columns:
            df = df[~df['Type'].str.lower().isin(['transfer', 'deposit', 'withdrawal'])]

        # 4. Calculate Metrics
        df['Net P&L'] = df['Change'] 
        df['Fees'] = df['Fee Charged']
        df['Cumulative P&L'] = df['Net P&L'].cumsum()

        # Key Stats
        total_pl = df['Net P&L'].sum()
        total_fees = df['Fees'].sum()
        total_trades = len(df[df['Type'] == 'trade'])

        # Win Rate
        df['Day'] = df['datetime'].dt.date
        daily_stats = df.groupby('Day')[['Net P&L', 'Fees']].sum()
        winning_days = len(daily_stats[daily_stats['Net P&L'] > 0])
        total_days = len(daily_stats)
        win_rate = (winning_days / total_days * 100) if total_days > 0 else 0

        # --- DASHBOARD VISUALS ---
        
        # Top Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Net Profit", f"{total_pl:,.4f}")
        col2.metric("Total Fees", f"{total_fees:,.4f}")
        col3.metric("Total Trades", f"{total_trades}")
        col4.metric("Win Rate", f"{win_rate:.1f}%")
        
        st.divider()

        # Equity Curve
        st.subheader("Account Growth")
        fig_equity = px.line(df, x='datetime', y='Cumulative P&L',
                             template='plotly_dark')
        fig_equity.update_traces(line_color='#00CC96', line_width=2)
        fig_equity.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
        st.plotly_chart(fig_equity, use_container_width=True)

        # Layout: Split bottom section into 2 columns
        row2_col1, row2_col2 = st.columns([2, 1])

        with row2_col1:
            st.subheader("Daily P&L")
            # Color logic
            daily_stats['Color'] = daily_stats['Net P&L'].apply(lambda x: '#00CC96' if x >= 0 else '#EF553B')
            fig_daily = px.bar(daily_stats.reset_index(), x='Day', y='Net P&L',
                               template='plotly_dark')
            fig_daily.update_traces(marker_color=daily_stats['Color'])
            st.plotly_chart(fig_daily, use_container_width=True)

        with row2_col2:
            st.subheader("Monthly Breakdown")
            monthly_stats = df.set_index('datetime').resample('M')[['Net P&L', 'Fees']].sum()
            monthly_stats.index = monthly_stats.index.strftime('%B %Y')
            # Display as a dataframe with highlighting
            st.dataframe(monthly_stats.style.background_gradient(subset=['Net P&L'], cmap='RdYlGn'), 
                         use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👈 Upload your CSV in the sidebar to get started.")