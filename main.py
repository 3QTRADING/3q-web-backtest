/**
 * 🚀 3Q 트리니티 V7 (컬럼 자동 인식 & 에러 방지판)
 * RAW 시트의 열 순서가 바뀌어도 알아서 찾아 계산합니다.
 */

function runTrinityEngine() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetRaw = ss.getSheetByName("RAW");
  const sheetRecord = ss.getSheetByName("RECORD");

  if (!sheetRaw || !sheetRecord) {
    Browser.msgBox("❌ 오류: 'RAW' 시트와 'RECORD' 시트가 없습니다. 이름을 확인해주세요.");
    return;
  }

  // 1. 데이터 로딩
  const data = sheetRaw.getDataRange().getValues();
  if (data.length < 2) {
    Browser.msgBox("❌ 오류: RAW 시트에 데이터가 없습니다.");
    return;
  }

  // 2. 컬럼 위치 찾기 (자동 인식)
  const headers = data[0].map(h => String(h).toUpperCase().trim());
  const idxDate = headers.indexOf("DATE");
  const idxOpen = headers.indexOf("OPEN");
  const idxHigh = headers.indexOf("HIGH");
  const idxLow = headers.indexOf("LOW");
  const idxClose = headers.indexOf("CLOSE");

  // 필수 컬럼 체크
  if (idxDate < 0 || idxOpen < 0 || idxHigh < 0 || idxLow < 0 || idxClose < 0) {
    Browser.msgBox("❌ 오류: RAW 시트 1행에 DATE, OPEN, HIGH, LOW, CLOSE 가 정확히 적혀있어야 합니다.");
    return;
  }

  // 3. 설정값 (정부장님 룰)
  let cash = 10000;      
  let op_seed = 10000;
  const cycle = 6;
  
  // SND 모드 스케줄
  const snd_schedule = {
    "25.01.06": "D", "25.01.13": "D", "25.01.21": "N", "25.01.27": "S",
    "25.02.03": "D", "25.02.10": "N", "25.02.18": "D", "25.02.24": "S",
    "25.03.03": "D", "25.03.10": "D", "25.03.17": "D", "25.03.24": "D",
    "25.03.31": "D", "25.04.07": "D", "25.04.14": "S", "25.04.21": "D",
    "25.04.28": "S", "25.05.05": "S", "25.05.12": "S", "25.05.19": "N",
    "25.05.27": "D"
  };

  const PARAMS = {
    "S": {buy: 0.04, sell: 0.037, moc: 17},
    "D": {buy: 0.006, sell: 0.010, moc: 25},
    "N": {buy: 0.05, sell: 0.030, moc: 2}
  };

  let positions = [];
  let logs = [];
  let profit_accum = 0;
  let day_cnt = 0;
  
  // 출력 헤더
  logs.push(["날짜", "모드", "티어", "이벤트", "현금", "주식평가금", "총자산"]);

  // --- 메인 루프 ---
  for (let i = 1; i < data.length; i++) {
    let row = data[i];
    let dateVal = row[idxDate];
    if (!(dateVal instanceof Date)) dateVal = new Date(dateVal);
    if (isNaN(dateVal.getTime())) continue;

    // 날짜 문자열 변환
    let y = dateVal.getFullYear().toString().slice(-2);
    let m = ("0" + (dateVal.getMonth() + 1)).slice(-2);
    let d = ("0" + dateVal.getDate()).slice(-2);
    let dateKey = `${y}.${m}.${d}`;         // YY.MM.DD (모드검색용)
    let dateStr = `20${y}-${m}-${d}`;       // YYYY-MM-DD (출력용)

    // 날짜 필터 (25년 1월 2일 부터)
    if (dateStr < "2025-01-02") continue;

    let O = Number(row[idxOpen]);
    let H = Number(row[idxHigh]);
    let L = Number(row[idxLow]);
    let C = Number(row[idxClose]);
    let prevC = (i > 1) ? Number(data[i-1][idxClose]) : O;

    // 모드 찾기
    let mode = "N";
    let sortedKeys = Object.keys(snd_schedule).sort().reverse();
    for (let k of sortedKeys) {
      if (k <= dateKey) { mode = snd_schedule[k]; break; }
    }
    let p = PARAMS[mode];
    let log_event = "";

    // 1. 시드 갱신
    day_cnt++;
    if (day_cnt >= cycle) {
      if (profit_accum > 0) op_seed += profit_accum * 0.9;
      else op_seed += profit_accum * 0.2;
      profit_accum = 0;
      day_cnt = 0;
    }

    // 2. 매도 (익절 & MOC)
    let next_pos = [];
    for (let pos of positions) {
      let sold = false;
      
      // 익절
      if (H >= pos.target) {
        let sell_p = Math.max(pos.target, O);
        let amt = pos.qty * sell_p;
        cash += amt;
        profit_accum += (amt - (pos.qty * pos.buy_p));
        sold = true;
        log_event += `[✅익절 T${pos.tier}] `;
      } 
      // MOC (보유일수 > moc제한)
      else if (!sold) {
        let held = Math.floor((dateVal - pos.buy_date) / (1000 * 60 * 60 * 24));
        if (held > pos.moc) {
          let sell_p = C;
          let amt = pos.qty * sell_p;
          cash += amt;
          profit_accum += (amt - (pos.qty * pos.buy_p));
          sold = true;
          log_event += `[⌛MOC T${pos.tier}] `;
        }
      }
      if (!sold) next_pos.push(pos);
    }
    positions = next_pos;

    // 3. 매수
    let tier = positions.length + 1;
    if (tier <= 8) {
      let target_buy = prevC * (1 - p.buy);
      
      if (L <= target_buy) {
        let buy_qty = 0;
        if ([1,2,3,4,7].includes(tier)) {
          buy_qty = 1;
        } else {
          let base = op_seed / 8;
          let mul = (tier === 5) ? 3.6 : (tier === 6 ? 3.0 : (tier === 8 ? 4.0 : 0));
          if (target_buy > 0) buy_qty = Math.floor((base * mul) / target_buy);
        }
        
        if (buy_qty < 1) buy_qty = 1;
        let buy_p = Math.min(target_buy, O);
        let cost = buy_qty * buy_p;
        
        // 잔고 체크
        if (cash >= cost) {
          cash -= cost;
          positions.push({
            buy_date: dateVal, buy_p: buy_p, qty: buy_qty,
            target: buy_p * (1 + p.sell), moc: p.moc, tier: tier
          });
          log_event += `[🛒매수 T${tier} ${buy_qty}주] `;
        }
      }
    }

    // 4. 기록
    let equity = positions.reduce((sum, pos) => sum + (pos.qty * C), 0);
    let total = cash + equity;
    
    logs.push([dateStr, mode, positions.length, log_event, cash, equity, total]);
  }

  // 5. 출력
  sheetRecord.clear();
  if (logs.length > 0) {
    sheetRecord.getRange(1, 1, logs.length, logs[0].length).setValues(logs);
    Browser.msgBox("✅ 완료! RECORD 시트를 확인하세요. 최종자산: $" + Math.round(logs[logs.length-1][6]));
  } else {
    Browser.msgBox("⚠️ 계산된 결과가 없습니다. 날짜나 데이터를 확인하세요.");
  }
}
