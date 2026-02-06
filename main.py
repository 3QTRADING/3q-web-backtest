import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ---------------------------------------------------------
# [1] 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="3Q Trinity V7 Web", layout="wide")
st.title("🚀 3Q 트리니티 V7 (웹 버전)")

# 스플릿 정보
SPLIT_DB = {"2025-11-20": 2.0}

# SND 스케줄 (25년 1월 ~)
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

# ---------------------------------------------------------
# [2] 엔진 로직 (V7: 컬럼 자동인식 & 티어별 비중)
# ---------------------------------------------------------
def run_simulation(df, start_seed):
    cash = start_seed
    op_seed = start_seed
    positions = []
    history = []
    
    cycle = 6
    profit_accum = 0
    day_cnt = 0
    
    # 파라미터
    PARAMS = {
        "S": {"buy": 0.04, "sell": 0.037, "moc": 17},
        "D": {"buy": 0.006, "sell": 0.010, "moc": 25},
        "N": {"buy": 0.05, "sell": 0.030, "moc": 2}
    }

    # 날짜별 루프
    for i in range(1, len(df)):
        date = df.index[i]
        d_str = date.strftime("%Y-%m-%d")

        # 1. 스플릿 반영
        if d_str in SPLIT_DB:
            ratio = SPLIT_DB[d_str]
            for pos in positions:
                pos['qty'] *= ratio
                pos['buy_p'] /= ratio
                pos['target'] /= ratio

        # 2. 데이터 로드 (컬럼 매핑됨)
        O = float(df['Open'].iloc[i])
        H = float(df['High'].iloc[i])
        L = float(df['Low'].iloc[i])
        C = float(df['Close'].iloc[i])
        PrevC = float(df['Close'].iloc[i-1])

        mode = get_snd_mode(date)
        p = PARAMS.get(mode, PARAMS["N"])

        # 3. 시드 갱신
        day_cnt += 1
        if day_cnt >= cycle:
            if profit_accum > 0: op_seed += profit_accum * 0.9
            else: op_seed += profit_accum * 0.2
            profit_accum = 0
            day_cnt = 0

        # 4. 매도 (목표가 -> MOC)
        next_pos = []
        for pos in positions:
            sold = False
            # A. 익절
            if H >= pos['target']:
                sell_p = max(pos['target'], O) # 갭상승 보정
                amt = pos['qty'] * sell_p
                cash += amt
                profit_accum += (amt - pos['qty']*pos['buy_p'])
                sold = True
            # B. MOC (다음날)
            elif not sold:
                held = (date - pos['date']).days
                if held > pos['moc']:
                    sell_p = C
                    amt = pos['qty'] * sell_p
                    cash += amt
                    profit_accum += (amt - pos['qty']*pos['buy_p'])
                    sold = True
            
            if not sold: next_pos.append(pos)
        positions = next_pos

        # 5. 매수
        tier = len(positions) + 1
        if tier <= 8:
            target_buy = PrevC * (1 - p["buy"])
            
            if L <= target_buy:
                # 티어별 수량 (정부장님 룰)
                if tier in [1, 2, 3, 4, 7]:
                    qty = 1
                else:
                    base = op_seed / 8
                    mul = 0
                    if tier == 5: mul = 3.6
                    elif tier == 6: mul = 3.0
                    elif tier == 8: mul = 4.0
                    
                    qty = int((base * mul) / target_buy)
                
                if qty < 1: qty = 1
                
                # 체결가 (갭락 보정)
                buy_p = min(target_buy, O)
                cost = qty * buy_p
                
                if cash >= cost:
                    cash -= cost
                    positions.append({
                        'date': date, 'buy_p': buy_p, 'qty': qty,
                        'target': buy_p * (1 + p["sell"]), 'moc': p['moc'], 'tier': tier
                    })

        # 기록
        equity = sum([ps['qty'] * C for ps in positions])
        total = cash + equity
        history.append({'Date': date, 'Total': total, 'Cash': cash, 'Equity': equity})

    return pd.DataFrame(history)

# ---------------------------------------------------------
# [3] UI (사용자 화면)
# ---------------------------------------------------------
with st.sidebar:
    st.header("🎛️ 설정")
    uploaded_file = st.file_uploader("RAW.csv 파일 업로드", type=['csv'])
    seed_input = st.number_input("시작 원금 ($)", value=10000)

if uploaded_file is not None:
    # 데이터 읽기 및 전처리 (컬럼 자동 인식)
    try:
        df = pd.read_csv(uploaded_file)
        # 컬럼명 대문자 변환 및 공백 제거
        df.columns = [c.upper().strip() for c in df.columns]
        
        if 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df.set_index('DATE').sort_index()
            
            # 컬럼 매핑 (어떤 이름이든 영어 표준으로 통일)
            # 사용자가 OPEN, HIGH 등을 썼다고 가정하고 매핑
            rename_map = {
                'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close',
                '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close'
            }
            df = df.rename(columns=rename_map)
            
            # 필수 컬럼 확인
            required = ['Open', 'High', 'Low', 'Close']
            if all(col in df.columns for col in required):
                # 25년 1월 2일 이후 필터링
                df = df[df.index >= "2025-01-02"]
                
                with st.spinner("분석 중..."):
                    res = run_simulation(df, seed_input)
                
                # 결과 출력
                last_val = res['Total'].iloc[-1]
                st.metric("최종 자산", f"${last_val:,.2f}", f"{(last_val/seed_input - 1)*100:.2f}%")
                
                st.line_chart(res.set_index('Date')['Total'])
                st.dataframe(res)
                
            else:
                st.error(f"CSV 파일에 다음 컬럼이 꼭 있어야 합니다: {required}")
        else:
            st.error("CSV 파일에 'DATE' 또는 '날짜' 컬럼이 없습니다.")
            
    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")
else:
    st.info("왼쪽에 RAW.csv 파일을 올려주세요.")
