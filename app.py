import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# ---------------------------
# Helper Functions
# ---------------------------

def get_ticker(company_name):
    search = yf.Tickers(company_name)
    symbols = list(search.tickers.keys())
    return symbols[0] if symbols else None

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, period="5y"):
    time.sleep(1)

    data = yf.Ticker(ticker + ".NS").history(period=period)

    if data.empty:
        data = yf.Ticker(ticker + ".BO").history(period=period)

    if data.empty:
        data = yf.Ticker(ticker).history(period=period)

    return data


def calculate_daily_returns(data):
    return data.pct_change().dropna()

def calculate_cumulative_returns(returns):
    return (1 + returns).cumprod() - 1

def calculate_cagr(data):
    start_price = data.iloc[0, 0]
    end_price = data.iloc[-1, 0]
    n_years = len(data) / 252
    return (end_price / start_price) ** (1 / n_years) - 1

def calculate_volatility(returns):
    return returns.std() * np.sqrt(252)

def calculate_max_drawdown(data):
    cumulative = data / data.cummax()
    drawdown = cumulative - 1
    return drawdown.min()

@st.cache_data(ttl=3600)
def fetch_market_data(period="5y"):
    time.sleep(1)
    return yf.Ticker("^NSEI").history(period=period)


def calculate_beta(stock_returns, market_returns):
    cov = np.cov(stock_returns, market_returns)[0][1]
    var = np.var(market_returns)
    return cov / var

def interpret_beta(beta):
    if beta > 1:
        return "Aggressive (more volatile than market)"
    elif beta < 1:
        return "Defensive (less volatile than market)"
    else:
        return "Moves with the market"

# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="Stock Risk & Return Analyzer", layout="wide")
st.title("📊 Stock Risk & Return Analyzer")

company_name = st.text_input(
    "Enter Company Name",
    placeholder="e.g. Reliance Industries, TCS, Infosys, Apple"
)

analyze = st.button("Analyze")

if analyze and company_name:
    with st.spinner("Fetching data & running analysis..."):
        ticker = get_ticker(company_name)

        if ticker is None:
            st.error("Could not resolve ticker. Try a different company name.")
        else:
            data = fetch_stock_data(ticker)

            if data.empty:
                st.error("No price data found for this company.")
            else:
                # Clean
                data = data[['Close']].dropna()

                # Calculations
                returns = calculate_daily_returns(data)
                cumulative_returns = calculate_cumulative_returns(returns)
                cagr = calculate_cagr(data)
                vol = calculate_volatility(returns).values[0]
              mdd = calculate_max_drawdown(data)
              mdd = mdd.item()


                # Market & Beta
                market = fetch_market_data()
                market = market[['Close']].dropna()
                market_returns = calculate_daily_returns(market)

                combined = pd.concat([returns, market_returns], axis=1, join="inner")
                combined.columns = ["Stock", "Market"]

                beta = calculate_beta(combined["Stock"], combined["Market"])
                beta_text = interpret_beta(beta)

                # ---------------------------
                # Display
                # ---------------------------

                st.subheader(f"📌 Analysis for: {company_name}")
                st.caption(f"Resolved Ticker: {ticker}")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("CAGR", f"{cagr*100:.2f}%")
                c2.metric("Volatility", f"{vol*100:.2f}%")
                c3.metric("Max Drawdown", f"{mdd*100:.2f}%")
                c4.metric("Beta", f"{beta:.2f}")

                st.write(f"**Beta Interpretation:** {beta_text}")

                st.divider()

                left, right = st.columns(2)

                with left:
                    st.write("📈 Stock Price")
                    st.line_chart(data)

                with right:
                    st.write("📈 Cumulative Returns")
                    st.line_chart(cumulative_returns)

                st.divider()

                st.write("📊 Stock vs Market Returns (Daily)")
                st.line_chart(combined)
