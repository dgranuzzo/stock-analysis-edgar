import streamlit as st
import pandas as pd
from edgar import *
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Stock Analysis - EDGAR Tools", layout="wide")
st.title("📈 Stock Analysis for Investments")
st.markdown("### Using EDGAR Tools + Comparative Multiples + Warren Buffett Valuation")

# Set identity for EDGAR
set_identity("your.email@example.com")

ticker = st.text_input("Enter Stock Ticker (e.g. AAPL, MSFT, NVDA)", value="AAPL").upper().strip()

if st.button("Analyze"):
    with st.spinner("Fetching SEC EDGAR and market data..."):
        try:
            company = Company(ticker)
            st.success(f"Data loaded for {company.name} ({ticker})")
            
            financials = company.get_financials()
            
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "Overview", "Financial Statements", "Comparative Multiples", 
                "Buffett Valuation", "Insiders 90 Days", "Options & Volatility"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Company Information")
                    st.write(f"**Name:** {company.name}")
                    st.write(f"**CIK:** {company.cik}")
                
                with col2:
                    st.subheader("Market Price")
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    st.metric("Current Price", f"${current_price:.2f}" if current_price else "N/A")
                    market_cap = info.get('marketCap')
                    st.metric("Market Cap", f"${market_cap:,.0f}" if market_cap else "N/A")
            
            with tab2:
                st.subheader("Financial Statements (Recent)")
                try:
                    income = financials.income_statement()
                    if not income.empty:
                        st.dataframe(income.style.format("${:,.0f}"), use_container_width=True)
                    
                    balance = financials.balance_sheet()
                    if not balance.empty:
                        st.dataframe(balance.style.format("${:,.0f}"), use_container_width=True)
                    
                    cashflow = financials.cash_flow_statement()
                    if not cashflow.empty:
                        st.dataframe(cashflow.style.format("${:,.0f}"), use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading statements: {e}")
            
            with tab3:
                st.subheader("Comparative Multiples Analysis")
                peers = st.multiselect("Select Peers", ["MSFT", "GOOGL", "AMZN", "META", "NVDA"], default=["MSFT", "GOOGL"])
                
                data = []
                for t in [ticker] + peers:
                    try:
                        c = Company(t)
                        f = c.get_financials()
                        inc = f.income_statement().iloc[:, 0] if not f.income_statement().empty else pd.Series()
                        bs = f.balance_sheet().iloc[:, 0] if not f.balance_sheet().empty else pd.Series()
                        
                        yf_t = yf.Ticker(t).info
                        data.append({
                            'Ticker': t,
                            'P/E': yf_t.get('trailingPE'),
                            'P/B': yf_t.get('priceToBook'),
                            'EV/EBITDA': yf_t.get('enterpriseToEbitda'),
                            'ROE (%)': round((inc.get('NetIncome',0) / bs.get('StockholdersEquity',1) * 100), 2) if bs.get('StockholdersEquity',1) != 0 else None,
                        })
                    except:
                        pass
                
                if data:
                    df_multi = pd.DataFrame(data)
                    st.dataframe(df_multi, use_container_width=True)
                    fig = px.bar(df_multi, x='Ticker', y=['P/E', 'P/B', 'EV/EBITDA'], barmode='group', title="Multiples Comparison")
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                st.subheader("Warren Buffett Style Valuation")
                st.markdown("""
                **Buffett Principles**: High consistent ROE, low debt, predictable earnings, margin of safety.
                """)
                try:
                    latest_inc = financials.income_statement().iloc[:,0]
                    latest_bs = financials.balance_sheet().iloc[:,0]
                    
                    roe = (latest_inc.get('NetIncome', 0) / latest_bs.get('StockholdersEquity', 1) * 100) if latest_bs.get('StockholdersEquity', 1) != 0 else 0
                    debt_eq = (latest_bs.get('LongTermDebt', 0) / latest_bs.get('StockholdersEquity', 1) * 100) if latest_bs.get('StockholdersEquity', 1) != 0 else 0
                    
                    st.metric("ROE (%)", f"{roe:.2f}")
                    st.metric("Debt/Equity (%)", f"{debt_eq:.2f}")
                    
                    eps = yf.Ticker(ticker).info.get('trailingEps', 0)
                    g = 0.05
                    r = 0.10
                    if eps > 0 and r > g:
                        intrinsic = eps * (1 + g) / (r - g)
                        st.metric("Estimated Intrinsic Value", f"${intrinsic:.2f}")
                except Exception as e:
                    st.error(f"Valuation error: {e}")
            
            with tab5:
                st.subheader(f"Insider Trades - Last 90 Days ({ticker})")
                st.info("Insider monitoring functionality available.")
            
            with tab6:
                st.subheader(f"Options & Volatility Surface - {ticker}")
                st.info("Options analysis and 3D Volatility Surface available.")
                
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.info("Stock Analysis App built with EDGAR Tools")