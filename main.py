# @title 🚀 3Q 트리니티 Pro (Algori-C 스타일 웹버전)
# ⚠️ 이 코드를 구글 코랩에 붙여넣고 실행하세요.

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

# ---------------------------------------------------------
# [1] 엔진 설정 (정부장님 룰 100% 반영)
# ---------------------------------------------------------
SPLIT_DB = {"2025-11-20": 2.0}
SND_DB = {
    "25.01.06": "D", "25.01.13": "D", "25.01.21": "N", "25.01.27": "S",
    "25.02.03": "D", "25.02.10": "N", "25.02.18": "D", "25.02.24": "S",
    "25.03.03": "D", "25.03.10": "D", "25.03.17": "D", "25.03.24": "D",
    "25.03.31": "D", "25.04.07": "D", "25.04.14": "S", "25.04.21": "D",
    "25.04.28": "S", "25.05.05": "S", "25.05.12": "S", "25.05.19": "N",
    "25.05.27": "D"
}

def get_snd_mode(d):
    t = d.strftime("%y.%m.%d")
    for k in sorted(SND_DB.keys(), reverse=True):
        if k <= t: return SND_DB[k]
    return "N"

def run_simulation(df, start_seed):
    cash = start_seed
    op_seed = start_seed
    positions = []
    history = []
    cycle = 6
    profit_accum = 0
    day_cnt = 0

    PARAMS = {
        "S": {"buy": 0.04, "sell": 0.037, "moc": 17},
        "D": {"buy": 0.006, "sell": 0.010, "moc": 25},
        "N": {"buy": 0.05, "sell": 0.030, "moc": 2}
    }

    for i in range(1, len(df)):
        date = df.index[i]
        d_str = date.strftime("%Y-%m-%d")

        # 스플릿
        if d_str in SPLIT_DB:
            ratio = SPLIT_DB[d_str]
            for pos in positions:
                pos['qty'] *= ratio
                pos['buy_p'] /= ratio
                pos['target'] /= ratio

        # 데이터
        O = float(df['Open'].iloc[i])
        H = float(df['High'].iloc[i])
        L = float(df['Low'].iloc[i])
        C = float(df['Close'].iloc[i])
        PrevC = float(df['Close'].iloc[i-1])

        mode = get_snd_mode(date)
        p = PARAMS.get(mode, PARAMS["N"])

        # 1. 시드 갱신
        day_cnt += 1
        if day_cnt >= cycle:
            if profit_accum > 0: op_seed += profit_accum * 0.9
            else: op_seed += profit_accum * 0.2
            profit_accum = 0
            day_cnt = 0

        # 2. 매도
        next_pos = []
        for pos in positions:
            sold = False
            if H >= pos['target']: # 목표가
                sell_p = max(pos['target'], O)
                amt = pos['qty'] * sell_p
                cash += amt
                profit_accum += (amt - pos['qty']*pos['buy_p'])
                sold = True
            elif not sold: # MOC
                held = (date - pos['date']).days
                if held > pos['moc']:
                    sell_p = C
                    amt = pos['qty'] * sell_p
                    cash += amt
                    profit_accum += (amt - pos['qty']*pos['buy_p'])
                    sold = True
            if not sold: next_pos.append(pos)
        positions = next_pos

        # 3. 매수
        tier = len(positions) + 1
        if tier <= 8:
            target_buy = PrevC * (1 - p["buy"])
            if L <= target_buy:
                if tier in [1,2,3,4,7]: qty = 1
                else:
                    base = op_seed / 8
                    if tier==5: mul=3.6
                    elif tier==6: mul=3.0
                    elif tier==8: mul=4.0
                    else: mul=0
                    qty = int((base * mul) / target_buy)
                
                if qty < 1: qty = 1
                buy_p = min(target_buy, O)
                cost = qty * buy_p
                
                if cash >= cost:
                    cash -= cost
                    positions.append({
                        'date': date, 'buy_p': buy_p, 'qty': qty,
                        'target': buy_p * (1 + p["sell"]), 'moc': p['moc'], 'tier': tier
                    })

        # 자산 기록
        equity = sum([ps['qty'] * C for ps in positions])
        total = cash + equity
        history.append({'Date': date, 'Total': total, 'Cash': cash, 'Equity': equity, 'Tier': tier})

    return pd.DataFrame(history)

# ---------------------------------------------------------
# [2] 웹사이트 UI 구성 (Algori-C 스타일)
# ---------------------------------------------------------
st.set_page_config(page_title="3Q Quant Backtest", layout="wide")

# 사이드바 (입력창)
with st.sidebar:
    st.title("🎛️ 설정 패널")
    st.info("Algori-C 스타일 백테스트")
    
    uploaded_file = st.file_uploader("📂 RAW.csv 업로드", type=['csv'])
    start_seed = st.number_input("투자 원금 ($)", value=10000, step=1000)
    
    st.divider()
    st.caption("Developed by Jeongbujang")

# 메인 화면
if uploaded_file is not None:
    # 데이터 로드
    df = pd.read_csv(uploaded_file)
    df.columns = [c.upper().strip() for c in df.columns]
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.set_index('DATE').sort_index()
    df = df.rename(columns={'OPEN':'Open','HIGH':'High','LOW':'Low','CLOSE':'Close'})
    df = df[df.index >= "2025-01-02"]

    # 엔진 실행
    with st.spinner("백테스트 엔진 가동 중..."):
        res = run_simulation(df, start_seed)

    # --- [1] 상단 요약 카드 ---
    final_bal = res['Total'].iloc[-1]
    total_ret = (final_bal - start_seed) / start_seed * 100
    mdd = ((res['Total'] / res['Total'].cummax()) - 1).min() * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("최종 자산", f"${final_bal:,.0f}")
    col2.metric("총 수익률", f"{total_ret:.2f}%", delta_color="normal")
    col3.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%", delta_color="inverse")
    col4.metric("총 거래일", f"{len(res)}일")

    # --- [2] 메인 인터랙티브 차트 (Plotly) ---
    st.subheader("📈 자산 추이 그래프")
    
    fig = go.Figure()
    # 총자산 선
    fig.add_trace(go.Scatter(
        x=res['Date'], y=res['Total'], mode='lines', name='총자산',
        line=dict(color='#00CC96', width=2)
    ))
    # 현금 비중 (영역)
    fig.add_trace(go.Scatter(
        x=res['Date'], y=res['Cash'], mode='none', name='보유 현금',
        fill='tozeroy', fillcolor='rgba(99, 110, 250, 0.2)'
    ))
    
    fig.update_layout(
        height=500,
        hovermode="x unified", # 마우스 올리면 정보 다 뜸
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- [3] 상세 데이터 ---
    st.subheader("📋 일별 상세 데이터")
    st.dataframe(res.set_index("Date"), use_container_width=True)

else:
    # 파일 없을 때 대기 화면
    st.markdown("""
    ### 👋 안녕하세요, 정부장님.
    왼쪽 사이드바에 **`RAW.csv`** 파일을 올려주시면 분석이 시작됩니다.
    
    **특징:**
    - 엑셀과 100% 동일한 로직 적용
    - 인터랙티브 차트 (확대/축소 가능)
    - 모바일에서도 확인 가능
    """)
