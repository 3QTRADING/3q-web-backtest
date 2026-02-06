import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# [1] 웹 화면 기본 설정
st.set_page_config(page_title="3Q Quant Pro Backtest", layout="wide")
st.title("🚀 3Q 퀀트 실전 백테스트 시스템")
st.info("시트의 복리 연산 및 운영 자금 갱신 로직이 엔진 내부에 탑재되어 있습니다.")

# [2] 3Q 핵심 백테스트 엔진
def run_3q_pro_engine(df, initial_seed, fee_rate, settings):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 내부 변수 설정
    operating_capital = initial_seed  # 운영 기준 자금 (Q)
    cash = initial_seed
    shares = 0
    realized_profit_pool = 0         # 주기에 반영될 누적 수익
    history = []
    
    day_count = 0
    update_cycle = settings['cycle'] # 반영 주기

    for i in range(1, len(df)):
        date = df.index[i]
        prev_close = float(df['Close'].iloc[i-1])
        curr_low = float(df['Low'].iloc[i])
        curr_high = float(df['High'].iloc[i])
        curr_close = float(df['Close'].iloc[i])
        
        # 1. 자금 갱신 로직 (설정된 주기마다 복리 반영)
        day_count += 1
        if day_count >= update_cycle:
            # 이익/손실 재투자 여부에 따라 운영 자금(Q) 업데이트
            if (realized_profit_pool > 0 and settings['reinvest_profit']) or \
               (realized_profit_pool < 0 and settings['reinvest_loss']):
                operating_capital += realized_profit_pool
                cash += realized_profit_pool # 실질 현금에 수익 편입
                realized_profit_pool = 0
            day_count = 0

        # 2. 매수 로직 (운영 자금의 1/8 비중)
        buy_target = np.floor(prev_close * 0.96 * 100) / 100 
        if curr_low <= buy_target:
            buy_amount = operating_capital / 8 
            if cash >= buy_amount:
                exec_price = min(buy_target, curr_close)
                qty = buy_amount / exec_price
                cash -= (buy_amount * (1 + fee_rate))
                shares += qty

        # 3. 매도 로직 (수익 실현 및 풀 적립)
        sell_target = round(prev_close * 1.037, 2)
        if curr_high >= sell_target and shares > 0:
            sell_value = shares * sell_target * (1 - fee_rate)
            # 투자 원본 대비 수익금 계산 (U20 누적실현 로직)
            profit = sell_value - (operating_capital / 8)
            realized_profit_pool += profit
            cash += sell_value
            shares = 0

        # 4. 일일 자산 평가 기록 (U21)
        daily_total = cash + (shares * curr_close)
        history.append({'날짜': date, '총자산': daily_total, '누적수익': daily_total - initial_seed})

    res_df = pd.DataFrame(history)
    
    # 최종 결과 지표 계산
    final_asset = res_df['총자산'].iloc[-1]
    total_ret = (final_asset / initial_seed - 1) * 100
    
    # CAGR 계산
    total_days = (res_df['날짜'].max() - res_df['날짜'].min()).days
    cagr = ((final_asset / initial_seed) ** (365 / total_days) - 1) * 100 if total_days > 0 else 0
    
    # MDD 계산
    res_df['최고점'] = res_df['총자산'].cummax()
    res_df['낙폭'] = (res_df['총자산'] - res_df['최고점']) / res_df['최고점'] * 100
    mdd = res_df['낙폭'].min()
    
    return res_df, total_ret, cagr, mdd, final_asset

# [3] 사이드바 설정 (전문 용어로 구성)
with st.sidebar:
    st.header("📝 백테스트 설정")
    ticker = st.text_input("분석 종목 (예: QLD)", value="QLD").upper()
    col_d1, col_d2 = st.columns(2)
    s_date = col_d1.date_input("시작일", datetime.now() - timedelta(days=365))
    e_date = col_d2.date_input("종료일", datetime.now())
    
    seed = st.number_input("초기 자본 ($)", value=3000, step=100)
    fee = st.number_input("거래 수수료 (%)", value=0.02, format="%.3f") / 100
    
    st.divider()
    st.header("🔄 자금 운영 전략")
    r18 = st.toggle("이익 발생 시 재투자", value=True)
    r19 = st.toggle("손실 발생 시 원금 조정", value=True)
    r20 = st.number_input("운영 자금 갱신 주기 (일)", value=20, min_value=1)

# [4] 실행 및 결과 출력
if st.button("📊 백테스트 실행", type="primary", use_container_width=True):
    with st.spinner("야후 파이낸스 DB 연동 중..."):
        df_stock = yf.download(ticker, start=s_date, end=e_date, auto_adjust=True)
        
        if not df_stock.empty:
            settings = {'reinvest_profit': r18, 'reinvest_loss': r19, 'cycle': r20}
            results, ret, cagr, mdd, final = run_3q_pro_engine(df_stock, seed, fee, settings)
            
            # 최종 지표 (U17~U21)
            st.subheader("🏁 분석 결과 리포트")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 수익률", f"{ret:.2f}%")
            m2.metric("연평균 수익률 (CAGR)", f"{cagr:.2f}%")
            m3.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
            m4.metric("최종 자산 평가액", f"${final:,.2f}")
            
            # 자산 추이 차트
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=results['날짜'], y=results['총자산'], name="자산 변화", line=dict(color="#3b82f6")))
            fig.update_layout(hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("데이터 로드에 실패했습니다.")
