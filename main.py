import pandas as pd

def run_3q_backtest(data_list, initial_capital=10000):
    """
    정부장님의 3Q 전략 기반 동적 백테스트 엔진
    data_list: 날짜, 종가, 기어(S/D/N), 복리주기(True/False)가 포함된 리스트
    """
    capital = initial_capital  # 현재 가용 자산
    base_capital = initial_capital # 복리 기준 원금
    shares = 0 # 보유 주수
    entry_price = 0 # 진입가
    hold_days = 0 # 보유 기간
    
    # SND 설정값
    settings = {
        'S': {'buy_gap': 0.04, 'sell_gap': 0.037, 'moc_days': 17},
        'D': {'buy_gap': 0.006, 'sell_gap': 0.01, 'moc_days': 25},
        'N': {'buy_gap': 0.05, 'sell_gap': 0.03, 'moc_days': 2}
    }

    results = []

    for i in range(1, len(data_list)):
        day_data = data_list[i]
        prev_data = data_list[i-1]
        
        gear = day_data['gear']
        current_price = day_data['price']
        is_compound_step = day_data['compound'] # 복리 주기 체크
        
        # 1. 복리 원금 업데이트 (True일 때)
        if is_compound_step and shares == 0:
            base_capital = capital

        # 2. 매수 로직 (LOC): 전일 종가 대비 지정된 gap 이하일 때 진입
        if shares == 0:
            buy_target = prev_data['price'] * (1 - settings[gear]['buy_gap'])
            if current_price <= buy_target:
                shares = base_capital // current_price
                entry_price = current_price
                capital -= (shares * current_price)
                hold_days = 0
        
        # 3. 매도 로직 (LOC 익절 또는 MOC 기간 매도)
        elif shares > 0:
            hold_days += 1
            sell_target = entry_price * (1 + settings[gear]['sell_gap'])
            
            # 익절 조건 충족 또는 보유 일수 초과 시 매도
            if current_price >= sell_target or hold_days >= settings[gear]['moc_days']:
                capital += (shares * current_price)
                shares = 0
                entry_price = 0

        results.append({
            'date': day_data['date'],
            'price': current_price,
            'total_equity': capital + (shares * current_price),
            'gear': gear
        })

    return pd.DataFrame(results)
