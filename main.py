import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# [1] 페이지 및 스타일 설정
st.set_page_config(page_title="3Q Quant Backtest System v4.5", layout="wide")

# [2] 3Q 복리 엔진 (R18~R20 로직 반영)
def run_3q_compound_engine(df, seed, fee_rate, r_params):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 초기 설정
    current_seed = seed      # 복리가 반영되어 변하는 현재 원금 (P19)
    cash = current_seed
    shares = 0
    history = []
    accumulated_profit = 0   # 누적 실현 손익
    
    # R20(갱신 주기) 카운트용
    days_counter = 0
    update_interval = r_params['update_cycle'] # R20

    for i in range(1, len(df)):
        date = df.index[i]
        curr_price = float(df['Close'].iloc[i])
        prev_close = float(df['Close'].iloc[i-1])
        low_price = float(df['Low'].iloc[i])
        high_price = float(df['High'].iloc[i])
        
        # 1. 갱신 주기(R20) 도래 시 원금 업데이트 로직
        days_counter += 1
        if days_counter >= update_interval:
            # 이익 복리(R18) 또는 손실 복리(R19) 반영 여부 체크
            if (accumulated_profit > 0 and r_params['comp_profit']) or \
               (accumulated_profit < 0 and r_params['comp_loss']):
                current_seed += accumulated_profit
                accumulated_profit = 0 # 반영 후 초기화
                cash = current_seed - (shares * curr_price) # 현금 재조정
            days_counter = 0

        # 2. 3Q 매수 로직 (LOC 기준가)
        target_buy = np.floor(prev_close * 0.96 * 100) / 100 # 기어 반영
        if low_price <= target_buy:
            buy_limit = current_seed / 8 # 갱신된 원금의 1/8 비중
            if cash >= buy_limit:
                exec_price = min(target_buy, curr_close)
                qty = buy_limit / exec_price
                cash -= (buy_limit * (1 + fee_rate))
                shares += qty

        # 3. 매도 로직 (시트 RECORD 탭 익절 로직 적용)
        # 매수가 대비 특정 수익률 도달 시 매도 로직 (예시: 3.7%)
        # 실제 시트의 RECORD 탭 매도 셀 구조에 맞춤
        target_sell = round(prev_close * 1.037, 2)
        if high_price >= target_sell and shares > 0:
            sell_proceeds = shares * target_sell
            profit = sell_proceeds - (shares * (sell_proceeds/shares) * fee_rate)
            accumulated_profit += (sell_proceeds - (current_seed/8)) # 간략화된 수익계산
            cash += sell_proceeds * (1 - fee_rate)
            shares = 0

        # 4. 자산 평가 (U21)
        total_asset = cash + (shares * curr_close)
        history.append({'Date': date, 'Total': total_asset, 'Price': curr_close})

    res_df = pd.DataFrame(history)
    
    # 최종 지표 계산 (U17~U21)
    final_val = res_df['Total'].iloc[-1]
    ret = (final_val / seed - 1) * 100
    days = (res_df['Date'].max() - res_df['Date'].min()).days
    cagr = ((final_val / seed) ** (365 / days) - 1) * 100 if days > 0 else 0
    res_df['CumMax'] = res_df['Total'].cummax()
    mdd = ((res_df['Total'] - res_df['CumMax']) / res_df['CumMax'] * 100).min()
    
    return res_df, ret, cagr, mdd, final_val

# [3] UI 구성
st.title("⚖️ 3Q 퀀트 정밀 백테스트 (복리 로직 적용)")

with st.sidebar:
    st.header("⚙️ 기본 설정 (P17~P20)")
    ticker = st.text_input("종목", value="QLD").upper()
    start_d = st.date_input("시작일 (P17)", datetime.now() - timedelta(days=365))
    end_d = st.date_input("종료일 (P18)", datetime.now())
    seed = st.number_input("초기투자금 (P19, $)", value=3000)
    fee = st.number_input("수수료 (P20, %)", value=0.02, format="%.3f") / 100
    
    st.header("🔄 복리 및 주기 (R18~R20)")
    r18 = st.checkbox("이익복리 반영 (R18)", value=True)
    r19 = st.checkbox("손실복리 반영 (R19)", value=True)
    r20 = st.number_input("Q 반영 갱신 주기 (R20, 일)", value=20)

if st.button("🚀 백테스트 실행", type="primary", use_container_width=True):
    df_raw = yf.download(ticker, start=start_d, end=end_d, auto_adjust=True)
    if not df_raw.empty:
        params = {'comp_profit': r18, 'comp_loss': r19, 'update_cycle': r20}
        res, ret, cagr, mdd, final = run_3q_compound_engine(df_raw, seed, fee, params)
        
        # 지표 출력 (U17~U21)
        st.subheader("📊 백테스트 출력 (U17~U21)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("수익률 (U17)", f"{ret:.2f}%")
        c2.metric("CAGR (U18)", f"{cagr:.2f}%")
        c3.metric("MDD (U19)", f"{mdd:.2f}%")
        c4.metric("총자산 (U21)", f"${final:,.2f}")
        
        st.line_chart(res.set_index('Date')['Total'])
