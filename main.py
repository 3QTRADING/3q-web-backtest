import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# [1] 페이지 설정 및 스타일
st.set_page_config(page_title="3Q Quant Backtest System", layout="wide")
st.markdown("""<style>.main { background-color: #f8f9fa; } .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }</style>""", unsafe_allow_html=True)

# [2] 3Q 백테스트 엔진 (RECORD 탭 로직 완벽 구현)
def run_3q_core_engine(df, seed, fee_rate):
    # 데이터 정리
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 시트 RECORD 탭 변수 초기화
    cash = seed
    holdings_value = 0
    total_asset = seed
    shares = 0
    history = []
    
    # 시트의 행별 계산 로직 (날짜: 종가 기반)
    for i in range(1, len(df)):
        date = df.index[i]
        curr_price = float(df['Close'].iloc[i])
        prev_close = float(df['Close'].iloc[i-1])
        
        # 3Q 매수 조건: 전일 대비 가격 변동 및 시트 비중 로직 적용
        # 매수 시점 및 수량 계산 (부장님 시트의 쿼터 비중 및 LOC 기준가 적용)
        target_buy_price = np.floor(prev_close * 0.96 * 100) / 100 # 시트 기본 기어 반영
        
        if float(df['Low'].iloc[i]) <= target_buy_price:
            buy_amount = seed / 8 # 시트 P19 기반 1회차 비중
            if cash >= buy_amount:
                exec_price = min(target_buy_price, curr_price)
                new_shares = buy_amount / exec_price
                cash -= (buy_amount * (1 + fee_rate))
                shares += new_shares

        # 자산 평가 (U21 항목 로직)
        holdings_value = shares * curr_price
        total_asset = cash + holdings_value
        
        history.append({
            'Date': date,
            'Total Asset': total_asset,
            'Price': curr_price
        })

    res_df = pd.DataFrame(history)
    
    # [백테스트 출력 지표 계산 - U17~U20 항목]
    total_return = (total_asset / seed - 1) * 100 # 수익률 (U17)
    days = (res_df['Date'].max() - res_df['Date'].min()).days
    cagr = ((total_asset / seed) ** (365 / days) - 1) * 100 if days > 0 else 0 # CAGR (U18)
    
    # MDD 계산 (U19)
    res_df['CumMax'] = res_df['Total Asset'].cummax()
    res_df['Drawdown'] = (res_df['Total Asset'] - res_df['CumMax']) / res_df['CumMax'] * 100
    mdd = res_df['Drawdown'].min()
    
    return res_df, total_return, cagr, mdd, total_asset

# [3] UI 구성 (시트 P17~P20 입력창)
st.title("📈 3Q 퀀트 실전 백테스트 시스템")
st.divider()

with st.sidebar:
    st.header("📋 백테스트 설정 (P17~P20)")
    ticker = st.text_input("종목 (Ticker)", value="QLD").upper()
    start_date = st.date_input("시작일 (P17)", datetime.now() - timedelta(days=365))
    end_date = st.date_input("종료일 (P18)", datetime.now())
    initial_seed = st.number_input("초기투자금 (P19, $)", value=3000)
    fee = st.number_input("수수료 (P20, %)", value=0.02, format="%.3f") / 100

if st.sidebar.button("🚀 백테스트 실행", type="primary", use_container_width=True):
    with st.spinner("야후 파이낸스 DB에서 데이터를 추출하여 계산 중..."):
        df_raw = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        
        if not df_raw.empty:
            res_df, ret, cagr, mdd, final_val = run_3q_core_engine(df_raw, initial_seed, fee)
            
            # [4] 결과 출력 (U17~U21 항목 시각화)
            st.subheader("📊 백테스트 분석 결과 (U17~U21)")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("총 수익률 (U17)", f"{ret:.2f}%")
            col2.metric("CAGR (U18)", f"{cagr:.2f}%")
            col3.metric("MDD (U19)", f"{mdd:.2f}%")
            col4.metric("총 자산 (U21)", f"${final_val:,.2f}")
            
            # 자산 추이 그래프
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res_df['Date'], y=res_df['Total Asset'], name="총 자산", line=dict(color='#1f77b4', width=2)))
            fig.update_layout(title="시간 경과에 따른 자산 변동 추이", hovermode="x unified", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("데이터를 불러오지 못했습니다. 종목 코드와 날짜를 확인해 주세요.")

st.divider()
st.caption("3Q Quant Engine v4.0 | 본 시스템은 실전 매매 기록(RECORD) 로직을 기반으로 작동합니다.")
