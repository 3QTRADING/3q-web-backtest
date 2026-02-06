import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

# ==========================================
# [1] 기본 설정 및 데이터베이스
# ==========================================
st.set_page_config(page_title="3Q Trinity Precision V3", layout="wide")
st.title("🚀 3Q 트리니티 정밀 검증 시스템 (Excel Sync Ver.)")

# 1. 분할(Split) DB (엑셀 SPLIT 시트 + 미래 예측 반영)
SPLIT_DB = {
    "2012-05-11": 2.0,
    "2015-05-20": 2.0,
    "2017-07-17": 2.0,
    "2022-01-24": 2.0, 
    "2025-11-20": 2.0  # 엑셀 시트상의 미래 예측 데이터
}

# 2. SND 모드 DB (전체 기간)
SND_DB = {
    "18.01.02": "D", "18.01.08": "N", "18.01.16": "D", "18.01.22": "N", "18.01.29": "D",
    "18.02.05": "D", "18.02.12": "D", "18.02.20": "S", "18.02.26": "S", "18.03.05": "N",
    "18.03.12": "S", "18.03.19": "N", "18.03.26": "D", "18.04.02": "N", "18.04.09": "N",
    "18.04.16": "N", "18.04.23": "D", "18.04.30": "D", "18.05.07": "N", "18.05.14": "S",
    "18.05.21": "S", "18.05.29": "N", "18.06.04": "N", "18.06.11": "N", "18.06.18": "D",
    "18.06.25": "D", "18.07.02": "N", "18.07.09": "S", "18.07.16": "S", "18.07.23": "N",
    "18.07.30": "S", "18.08.06": "N", "18.08.13": "D", "18.08.20": "D", "18.08.27": "S",
    "18.09.04": "S", "18.09.10": "D", "18.09.17": "N", "18.09.24": "D", "18.10.01": "N",
    "18.10.08": "S", "18.10.15": "D", "18.10.22": "S", "18.10.29": "D", "18.11.05": "S",
    "18.11.12": "D", "18.11.19": "S", "18.11.26": "D", "18.12.03": "S", "18.12.10": "D",
    "18.12.17": "S", "18.12.24": "D", "18.12.31": "S", "19.01.07": "S", "19.01.14": "S",
    "19.01.22": "N", "19.01.28": "S", "19.02.04": "S", "19.02.11": "N", "19.02.19": "S",
    "19.02.25": "N", "19.03.04": "N", "19.03.11": "D", "19.03.18": "S", "19.03.25": "D",
    "19.04.01": "S", "19.04.08": "D", "19.04.15": "S", "19.04.22": "D", "19.04.29": "D",
    "19.05.06": "D", "19.05.13": "D", "19.05.20": "D", "19.05.28": "D", "19.06.03": "D",
    "19.06.10": "S", "19.06.17": "S", "19.06.24": "N", "19.07.01": "S", "19.07.08": "S",
    "19.07.15": "N", "19.07.22": "S", "19.07.29": "S", "19.08.05": "D", "19.08.12": "D",
    "19.08.19": "N", "19.08.26": "S", "19.09.03": "S", "19.09.09": "S", "19.09.16": "D",
    "19.09.23": "D", "19.09.30": "D", "19.10.07": "N", "19.10.14": "S", "19.10.21": "N",
    "19.10.28": "S", "19.11.04": "N", "19.11.11": "S", "19.11.18": "N", "19.11.25": "D",
    "19.12.02": "N", "19.12.09": "D", "19.12.16": "N", "19.12.23": "D", "19.12.30": "N",
    "20.01.06": "D", "20.01.13": "D", "20.01.21": "D", "20.01.27": "D", "20.02.03": "D",
    "20.02.10": "N", "20.02.18": "D", "20.02.24": "D", "20.03.02": "N", "20.03.09": "D",
    "20.03.16": "D", "20.03.23": "D", "20.03.30": "S", "20.04.06": "D", "20.04.13": "S",
    "20.04.20": "N", "20.04.27": "D", "20.05.04": "D", "20.05.11": "N", "20.05.18": "D",
    "20.05.26": "N", "20.06.01": "N", "20.06.08": "S", "20.06.15": "N", "20.06.22": "S",
    "20.06.29": "N", "20.07.06": "D", "20.07.13": "N", "20.07.20": "D", "20.07.27": "D",
    "20.08.03": "D", "20.08.10": "D", "20.08.17": "D", "20.08.24": "D", "20.08.31": "D",
    "20.09.08": "D", "20.09.14": "D", "20.09.21": "S", "20.09.28": "D", "20.10.05": "S",
    "20.10.12": "D", "20.10.19": "D", "20.10.26": "D", "20.11.02": "D", "20.11.09": "N",
    "20.11.16": "D", "20.11.23": "N", "20.11.30": "D", "20.12.07": "N", "20.12.14": "D",
    "20.12.21": "N", "20.12.28": "D", "21.01.04": "N", "21.01.11": "D", "21.01.19": "D",
    "21.01.25": "D", "21.02.01": "D", "21.02.08": "D", "21.02.16": "D", "21.02.22": "D",
    "21.03.01": "D", "21.03.08": "D", "21.03.15": "N", "21.03.22": "S", "21.03.29": "N",
    "21.04.05": "N", "21.04.12": "N", "21.04.19": "D", "21.04.26": "N", "21.05.03": "N",
    "21.05.10": "S", "21.05.17": "D", "21.05.24": "D", "21.06.01": "N", "21.06.07": "S",
    "21.06.14": "S", "21.06.21": "D", "21.06.28": "S", "21.07.06": "N", "21.07.12": "N",
    "21.07.19": "D", "21.07.26": "S", "21.08.02": "S", "21.08.09": "S", "21.08.16": "D",
    "21.08.23": "N", "21.08.30": "N", "21.09.07": "D", "21.09.13": "N", "21.09.20": "N",
    "21.09.27": "N", "21.10.04": "D", "21.10.11": "D", "21.10.18": "S", "21.10.25": "S",
    "21.11.01": "N", "21.11.08": "N", "21.11.15": "D", "21.11.22": "N", "21.11.29": "D",
    "21.12.06": "D", "21.12.13": "D", "21.12.20": "D", "21.12.27": "N", "22.01.03": "D",
    "22.01.10": "N", "22.01.18": "D", "22.01.24": "D", "22.01.31": "D", "22.02.07": "S",
    "22.02.14": "D", "22.02.22": "S", "22.02.28": "D", "22.03.07": "S", "22.03.14": "D",
    "22.03.21": "S", "22.03.28": "D", "22.04.04": "D", "22.04.11": "D", "22.04.18": "S",
    "22.04.25": "D", "22.05.02": "S", "22.05.09": "D", "22.05.16": "D", "22.05.23": "S",
    "22.05.31": "S", "22.06.06": "D", "22.06.13": "S", "22.06.21": "D", "22.06.27": "S",
    "22.07.05": "D", "22.07.11": "S", "22.07.18": "S", "22.07.25": "S", "22.08.01": "N",
    "22.08.08": "S", "22.08.15": "N", "22.08.22": "D", "22.08.29": "D", "22.09.06": "D",
    "22.09.12": "D", "22.09.19": "N", "22.09.26": "N", "22.10.03": "D", "22.10.10": "N",
    "22.10.17": "D", "22.10.24": "N", "22.10.31": "D", "22.11.07": "N", "22.11.14": "S",
    "22.11.21": "D", "22.11.28": "N", "22.12.05": "N", "22.12.12": "S", "22.12.19": "D",
    "22.12.27": "N", "23.01.03": "S", "23.01.09": "S", "23.01.17": "N", "23.01.23": "S",
    "23.01.30": "D", "23.02.06": "S", "23.02.13": "D", "23.02.21": "D", "23.02.27": "N",
    "23.03.06": "N", "23.03.13": "N", "23.03.20": "S", "23.03.27": "N", "23.04.03": "S",
    "23.04.10": "D", "23.04.17": "D", "23.04.24": "D", "23.05.01": "N", "23.05.08": "N",
    "23.05.15": "D", "23.05.22": "S", "23.05.30": "S", "23.06.05": "S", "23.06.12": "D",
    "23.06.20": "S", "23.06.26": "D", "23.07.03": "S", "23.07.10": "D", "23.07.17": "N",
    "23.07.24": "D", "23.07.31": "N", "23.08.07": "D", "23.08.14": "D", "23.08.21": "N",
    "23.08.28": "N", "23.09.05": "N", "23.09.11": "N", "23.09.18": "D", "23.09.25": "D",
    "23.10.02": "N", "23.10.09": "D", "23.10.16": "N", "23.10.23": "D", "23.10.30": "N",
    "23.11.06": "S", "23.11.13": "N", "23.11.20": "S", "23.11.27": "S", "23.12.04": "N",
    "23.12.11": "N", "23.12.18": "S", "23.12.26": "N", "24.01.02": "S", "24.01.08": "D",
    "24.01.16": "S", "24.01.22": "D", "24.01.29": "S", "24.02.05": "D", "24.02.12": "S",
    "24.02.20": "D", "24.02.26": "D", "24.03.04": "D", "24.03.11": "D", "24.03.18": "D",
    "24.03.25": "D", "24.04.01": "D", "24.04.08": "D", "24.04.15": "D", "24.04.22": "D",
    "24.04.29": "S", "24.05.06": "S", "24.05.13": "S", "24.05.20": "N", "24.05.28": "S",
    "24.06.03": "N", "24.06.10": "N", "24.06.17": "S", "24.06.24": "N", "24.07.01": "D",
    "24.07.08": "N", "24.07.15": "N", "24.07.22": "D", "24.07.29": "S", "24.08.05": "D",
    "24.08.12": "N", "24.08.19": "S", "24.08.26": "N", "24.09.03": "D", "24.09.09": "D",
    "24.09.16": "D", "24.09.23": "D", "24.09.30": "N", "24.10.07": "N", "24.10.14": "D",
    "24.10.21": "D", "24.10.28": "D", "24.11.04": "D", "24.11.11": "S", "24.11.18": "D",
    "24.11.25": "D", "24.12.02": "D", "24.12.09": "N", "24.12.16": "S", "24.12.23": "D",
    "24.12.30": "N", "25.01.06": "D", "25.01.13": "D", "25.01.21": "N", "25.01.27": "S",
    "25.02.03": "D", "25.02.10": "N", "25.02.18": "D", "25.02.24": "S", "25.03.03": "D",
    "25.03.10": "D", "25.03.17": "D", "25.03.24": "D", "25.03.31": "D", "25.04.07": "D",
    "25.04.14": "S", "25.04.21": "D", "25.04.28": "S", "25.05.05": "S", "25.05.12": "S",
    "25.05.19": "N", "25.05.27": "D", "25.06.02": "N", "25.06.09": "S", "25.06.16": "S",
    "25.06.23": "S", "25.06.30": "S", "25.07.07": "N", "25.07.14": "S", "25.07.21": "D",
    "25.07.28": "S", "25.08.04": "D", "25.08.11": "S", "25.08.18": "D", "25.08.25": "D",
    "25.09.02": "D", "25.09.08": "D", "25.09.15": "D", "25.09.22": "D", "25.09.29": "D",
    "25.10.06": "D", "25.10.13": "D", "25.10.20": "D", "25.10.27": "D", "25.11.03": "D",
    "25.11.10": "D", "25.11.17": "D", "25.11.24": "D", "25.12.01": "S", "25.12.08": "D",
    "25.12.15": "D", "25.12.22": "D", "25.12.29": "N", "26.01.05": "N", "26.01.12": "N",
    "26.01.20": "N", "26.01.26": "D", "26.02.02": "D"
}

def get_snd_mode(target_date):
    sorted_keys = sorted(SND_DB.keys(), reverse=True)
    t_str = target_date.strftime("%y.%m.%d")
    for k in sorted_keys:
        if k <= t_str: return SND_DB[k]
    return "N"

# ==========================================
# [2] 3Q 정밀 엔진 (Excel Sync)
# ==========================================
def run_3q_precision_engine(df, seed, fee, comp_p, comp_l, cycle_d, user_compare_list=None):
    cash = seed
    operating_seed = seed
    history = []
    accumulated_profit = 0
    update_counter = 0

    # 포지션 관리 리스트
    # {buy_date, buy_price, qty, target_price, moc_limit_days, mode}
    positions = []

    # 파라미터 정의 (S, D, N)
    PARAMS = {
        "S": {"buy": 0.04,  "sell": 0.037, "moc": 17},
        "D": {"buy": 0.006, "sell": 0.010, "moc": 25},
        "N": {"buy": 0.05,  "sell": 0.030, "moc": 2}
    }

    # 엑셀 검증용: 사용자 입력 데이터가 있으면 인덱싱 준비
    comp_idx = 0
    
    # ----------------------------------------
    # [Start] 시뮬레이션 루프
    # ----------------------------------------
    for i in range(1, len(df)):
        current_date = df.index[i]
        date_str = current_date.strftime("%Y-%m-%d")

        # 1. Split Check (분할 반영)
        if date_str in SPLIT_DB:
            ratio = SPLIT_DB[date_str]
            for pos in positions:
                pos['qty'] = pos['qty'] * ratio
                pos['buy_price'] = pos['buy_price'] / ratio
                pos['target_price'] = pos['target_price'] / ratio

        # 2. 데이터 로드 (현재 봉)
        prev_close = float(df['Close'].iloc[i-1])
        curr_open = float(df['Open'].iloc[i])
        curr_low = float(df['Low'].iloc[i])
        curr_high = float(df['High'].iloc[i])
        curr_close = float(df['Close'].iloc[i])

        mode = get_snd_mode(current_date)
        p = PARAMS.get(mode, PARAMS["N"])

        # 3. 시드 갱신 (복리)
        update_counter += 1
        if update_counter >= cycle_d:
            if accumulated_profit > 0:
                operating_seed += (accumulated_profit * comp_p)
            else:
                operating_seed += (accumulated_profit * comp_l)
            accumulated_profit = 0
            update_counter = 0

        # 4. [매도 체크] (Sell Logic)
        next_positions = []
        for pos in positions:
            is_sold = False
            
            # (A) 목표가 익절
            # 엑셀 로직: IF(High > Target, ...)
            if curr_high >= pos['target_price']:
                # 갭상승 보정: 시가가 목표가보다 높으면 시가 체결
                sell_price = pos['target_price']
                if curr_open > sell_price: sell_price = curr_open 
                
                sell_val = pos['qty'] * sell_price
                profit = sell_val - (pos['qty'] * pos['buy_price'])
                
                cash += sell_val * (1 - fee)
                accumulated_profit += profit
                is_sold = True
            
            # (B) MOC 만기 청산
            elif not is_sold:
                held_days = (current_date - pos['buy_date']).days
                if held_days >= pos['moc_limit_days']:
                    sell_val = pos['qty'] * curr_close
                    profit = sell_val - (pos['qty'] * pos['buy_price'])
                    
                    cash += sell_val * (1 - fee)
                    accumulated_profit += profit
                    is_sold = True
            
            if not is_sold:
                next_positions.append(pos)
        
        positions = next_positions

        # 5. [매수 체크] (Buy Logic)
        target_buy_price = prev_close * (1 - p["buy"])
        current_tier_index = len(positions) + 1

        # 엑셀 로직: IF(Low < Target, ...)
        if curr_low <= target_buy_price and current_tier_index <= 8:
            
            # 티어별 배수
            if current_tier_index in [1, 2, 3, 4, 7]: unit_multiplier = 1.0
            elif current_tier_index == 5: unit_multiplier = 3.6
            elif current_tier_index == 6: unit_multiplier = 3.0
            elif current_tier_index == 8: unit_multiplier = 4.0
            else: unit_multiplier = 1.0

            buy_amt = (operating_seed / 8) * unit_multiplier
            # [중요] 수량 계산은 타겟가 기준 (엑셀 floor 함수 등 고려하여 int 처리)
            buy_qty = int(buy_amt / target_buy_price)
            if buy_qty < 1: buy_qty = 1

            # 갭하락 보정: 시가가 타겟가보다 낮으면 시가 체결
            buy_price = target_buy_price
            if curr_open < target_buy_price: buy_price = curr_open

            buy_cost = buy_qty * buy_price

            if cash >= buy_cost:
                cash -= buy_cost
                
                new_pos = {
                    'buy_date': current_date,
                    'buy_price': buy_price,
                    'qty': buy_qty,
                    'target_price': buy_price * (1 + p["sell"]),
                    'moc_limit_days': p["moc"],
                    'tier': current_tier_index,
                    'mode': mode
                }
                positions.append(new_pos)

        # 6. 자산 평가 및 기록
        equity_val = sum([p['qty'] * curr_close for p in positions])
        total_asset = cash + equity_val
        
        # 7. 검증 데이터와 비교
        diff_flag = ""
        user_val = 0.0
        if user_compare_list and comp_idx < len(user_compare_list):
            user_val = user_compare_list[comp_idx]
            # 오차범위 1달러 이상이면 불일치로 간주
            if abs(total_asset - user_val) > 1.0:
                diff_flag = "❌ 불일치"
            else:
                diff_flag = "✅ 일치"
            comp_idx += 1

        history.append({
            'Date': current_date, 
            'Total': total_asset, 
            'Mode': mode, 
            'Active_Tiers': len(positions),
            'Excel_Value': user_val if user_compare_list else 0,
            'Sync_Status': diff_flag
        })
        
    return pd.DataFrame(history)


# ==========================================
# [3] 사이드바 설정
# ==========================================
with st.sidebar:
    st.header("📋 설정 패널")
    
    uploaded_file = st.file_uploader("📂 RAW.csv 업로드 (필수)", type=['csv'])
    
    seed = st.number_input("초기 원금 ($)", value=10000, step=1000)
    fee_rate = st.number_input("거래 수수료 (%)", value=0.0, format="%.3f") / 100
    
    st.divider()
    st.markdown("**복리 정책**")
    comp_profit = st.slider("이익 재투자 (%)", 0, 100, 90) / 100
    comp_loss = st.slider("손실 반영 (%)", 0, 100, 20) / 100
    update_cycle = st.number_input("갱신 주기 (일)", value=6, min_value=1)
    
    st.divider()
    st.markdown("**검증 데이터 입력**")
    excel_data_str = st.text_area("엑셀 자산열 복사/붙여넣기", 
                                  placeholder="$10,000\n$10,004\n...", height=150)

# ==========================================
# [4] 메인 실행 로직
# ==========================================
if st.button("📊 정밀 백테스트 실행", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.error("🚨 정확한 검증을 위해 'RAW.csv' 파일을 업로드해주세요.")
    else:
        with st.spinner("데이터 분석 및 엔진 가동 중..."):
            # A. 데이터 로드 및 전처리
            try:
                df_raw = pd.read_csv(uploaded_file)
                # 컬럼명 표준화 (공백제거, 대문자)
                df_raw.columns = [c.upper().strip() for c in df_raw.columns]
                
                # DATE 컬럼 처리
                if 'DATE' in df_raw.columns:
                    df_raw['DATE'] = pd.to_datetime(df_raw['DATE'])
                    df_raw = df_raw.set_index('DATE').sort_index()
                else:
                    st.error("CSV 파일에 'DATE' 컬럼이 없습니다.")
                    st.stop()
                
                # 필수 가격 컬럼 존재 확인 및 매핑
                req_cols = {'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close'}
                if not all(col in df_raw.columns for col in req_cols.keys()):
                    st.error(f"CSV 파일에 다음 컬럼이 모두 있어야 합니다: {list(req_cols.keys())}")
                    st.stop()
                
                df_raw = df_raw.rename(columns=req_cols)[['Open', 'High', 'Low', 'Close']]
                
                # B. 사용자 검증 데이터 파싱
                user_list = []
                if excel_data_str:
                    # $ , 줄바꿈 등 제거하고 숫자 리스트로 변환
                    cleaned = excel_data_str.replace("$", " ").replace(",", "").replace("\n", " ")
                    user_list = [float(x) for x in cleaned.split() if x.strip()]
                    
                    # 사용자가 입력한 데이터의 개수만큼만 날짜 슬라이싱 (시작일 맞추기 위함)
                    # *가정: 사용자가 입력한 첫 데이터가 시뮬레이션 시작일의 자산이라고 가정*
                    if len(user_list) > 0:
                        # 데이터의 끝에서부터 user_list 길이만큼만 가져와서 매칭해볼 수도 있고
                        # 혹은 2025-01-02 부터 시작한다고 가정할 수도 있음.
                        # 여기서는 정부장님 케이스(2025-01-02 시작)에 맞춰 25년 데이터 필터링
                        df_raw = df_raw[df_raw.index >= "2025-01-02"]

            except Exception as e:
                st.error(f"데이터 파일 읽기 오류: {e}")
                st.stop()

            # C. 엔진 실행
            res = run_3q_precision_engine(
                df_raw, seed, fee_rate, comp_profit, comp_loss, update_cycle, 
                user_compare_list=user_list
            )

            # D. 결과 출력
            if not res.empty:
                final_asset = res['Total'].iloc[-1]
                
                # 상단 메트릭
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("최종 자산", f"${final_asset:,.2f}")
                c2.metric("수익률", f"{(final_asset/seed - 1)*100:.2f}%")
                
                # 불일치 발생 여부 확인
                mismatch = res[res['Sync_Status'] == "❌ 불일치"]
                if not mismatch.empty:
                    first_fail_date = mismatch['Date'].iloc[0].strftime("%Y-%m-%d")
                    c3.metric("동기화 상태", "⚠️ 불일치 발생", delta_color="inverse")
                    c4.metric("최초 불일치일", first_fail_date)
                    st.error(f"🚨 **{first_fail_date}** 부터 엑셀값과 달라집니다. 아래 로그 탭에서 확인하세요.")
                else:
                    c3.metric("동기화 상태", "✅ 완전 일치")
                    if user_list:
                        st.success("🎉 축하합니다! 엑셀 자산 흐름과 100% 일치합니다.")

                # 탭 구성
                tab1, tab2, tab3 = st.tabs(["📊 차트 비교", "📝 상세 로그 (동기화)", "📂 원본 데이터"])
                
                with tab1:
                    chart_data = res.set_index('Date')[['Total']]
                    if user_list:
                        chart_data['Excel'] = res.set_index('Date')['Excel_Value']
                    st.line_chart(chart_data)
                
                with tab2:
                    st.markdown("### 🔍 일자별 상세 거래 및 검증 로그")
                    
                    # 표시할 컬럼 선택
                    cols = ['Date', 'Total', 'Excel_Value', 'Sync_Status', 'Active_Tiers', 'Mode']
                    
                    # 스타일링: 불일치 행 강조
                    def highlight_diff(row):
                        if row['Sync_Status'] == "❌ 불일치":
                            return ['background-color: #ffcccc'] * len(row)
                        return [''] * len(row)

                    st.dataframe(
                        res[cols].style.format({
                            'Total': "{:,.2f}", 
                            'Excel_Value': "{:,.2f}"
                        }).apply(highlight_diff, axis=1),
                        use_container_width=True,
                        height=600
                    )
                    
                with tab3:
                    st.dataframe(df_raw)
            else:
                st.warning("결과 데이터가 없습니다.")
