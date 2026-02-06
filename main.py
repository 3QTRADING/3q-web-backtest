import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 3Q 퀀트 백테스트 엔진 로직
def run_3q_backtest(df, seed, gear_params, fee=0.0002):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    cash, inventory, history = seed, [], []
    for i in range(1, len(df)):
        prev_close = float(df['Close'].iloc[i-1])
        curr_low, curr_high, curr_close = float(df['Low'].iloc[i]), float(df['High'].iloc[i]), float(df['Close'].iloc[i])
        target_buy = np.floor(prev_close * (1 + gear_params['buy']) * 100) / 100
        if curr_low <= target_buy and cash >= seed/8:
            exec_price = min(target_buy, curr_close)
            units = (seed/8) / exec_price
            cash -= (seed/8 * (1 + fee))
            target_sell = round(exec_price * (1 + gear_params['sell']), 2)
            inventory.append({'units': units, 'target_sell': target_sell})
        new_inv = []
        for item in inventory:
            if curr_high >= item['target_sell']: cash += (item['units'] * item['target_sell'] * (1 - fee))
            else: new_inv.append(item)
        inventory = new_inv
        history.append({'Date': df.index[i], 'Total': cash + sum(idx['units'] * curr_close for idx in inventory)})
    return pd.DataFrame(history)

st.title("🚀 3Q 퀀트 실전 백테스트")
st.sidebar.header("⚙️ 전략 설정")
ticker = st.sidebar.text_input("종목 심볼", value="QLD").upper()
seed = st.sidebar.number_input("시작 원금 ($)", value=3000)
buy_r = st.sidebar.slider("매수 목표 (%)", 0.0, 10.0, 4.0) / 100
sell_r = st.sidebar.slider("익절 목표 (%)", 0.0, 10.0, 3.7) / 100
s_date = st.sidebar.date_input("시작일", datetime.now() - timedelta(days=365))
e_date = st.sidebar.date_input("종료일", datetime.now())

if st.sidebar.button("📊 백테스트 실행"):
    df = yf.download(ticker, start=s_date, end=e_date, auto_adjust=True)
    if not df.empty:
        res = run_3q_backtest(df, seed, {'buy': buy_r, 'sell': sell_r})
        st.metric("최종 자산", f"${res['Total'].iloc[-1]:,.2f}")
        st.line_chart(res.set_index('Date'))
