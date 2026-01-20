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

        #
