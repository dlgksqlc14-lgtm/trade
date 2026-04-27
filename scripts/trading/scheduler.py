import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import deque
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler

from scripts.trading.collector import (
    fetch_live_krx_market_data,
    fetch_live_crypto_market_data,
    fetch_kospi_daily_change,
    fetch_kis_cash_balance,
    get_universe,
    refresh_universe_cache,
    fdr_quick_screen,
)
from scripts.trading.trade_signal import generate_krx_signal, generate_crypto_signal, SignalType
from scripts.trading.order import PortfolioState, OrderManager
from scripts.trading.risk import RiskManager
from scripts.trading.notifier import send_alert

with open('scripts/trading/config.yaml') as f:
    CONFIG = yaml.safe_load(f)


portfolio = PortfolioState(capital=0)
order_mgr = OrderManager(virtual=False)
risk_mgr = RiskManager(
    initial_capital=0,
    daily_loss_limit_pct=CONFIG['risk']['daily_loss_limit_pct'] * 100,
)

STATE_FILE = 'scripts/trading/state.json'
EMERGENCY_FLAG = 'scripts/trading/emergency_close.flag'
LOGS_FILE = 'scripts/trading/logs.json'

_log_buffer: deque = deque(maxlen=100)


def log_event(symbol: str, price: float, deviation: float, signal: str, action: str = '', reason: str = ''):
    entry = {
        'time': datetime.now().strftime('%H:%M:%S'),
        'symbol': symbol,
        'price': price,
        'deviation': round(deviation, 2),
        'signal': signal,
        'action': action,
        'reason': reason,
    }
    _log_buffer.append(entry)
    with open(LOGS_FILE, 'w') as f:
        json.dump(list(_log_buffer), f, ensure_ascii=False)


def save_state():
    with open(STATE_FILE, 'w') as f:
        json.dump(portfolio.to_dict(), f, ensure_ascii=False, indent=2)


def check_emergency_close() -> bool:
    import os
    if os.path.exists(EMERGENCY_FLAG):
        os.remove(EMERGENCY_FLAG)
        return True
    return False


def run_krx_check():
    daily_limit_hit = risk_mgr.is_daily_limit_hit()

    if check_emergency_close():
        _close_all_krx()
        return

    market_drop = fetch_kospi_daily_change()
    market_halt = market_drop <= CONFIG['krx']['market_drop_threshold']
    if market_halt:
        send_alert(f"[KRX] 코스피 급락 {market_drop:.1f}% — 신규 매수 보류")

    krx_cfg = CONFIG['krx']

    # Stage 1: FDR로 전체 유니버스 빠른 이격도 필터 (KIS 호출 없음)
    universe = get_universe()
    candidates = fdr_quick_screen(universe, krx_cfg['buy_threshold'], krx_cfg['ma_window'], krx_cfg['volume_ma_window'])
    candidate_symbols = [s for s, _ in candidates]
    print(f"[스캔] 유니버스 {len(universe)}개 → 임계값 이하 {len(candidate_symbols)}개")

    # 보유 종목은 매도/손절 판단을 위해 항상 포함
    held = [s for s in portfolio.positions if '/' not in s]
    symbols = list(dict.fromkeys(candidate_symbols + held))  # 순서 유지 + 중복 제거

    if not symbols:
        print("[스캔] 매수 후보 없음 (전 종목 MA 위)")
        return

    # Stage 2: 후보 + 보유 종목에만 KIS 실시간 가격 조회
    from scripts.trading.collector import get_kis_token
    get_kis_token()

    def fetch_krx(symbol):
        return symbol, fetch_live_krx_market_data(symbol, krx_cfg['ma_window'], krx_cfg['volume_ma_window'])

    with ThreadPoolExecutor(max_workers=min(len(symbols), 8)) as ex:
        futures = {ex.submit(fetch_krx, s): s for s in symbols}
        results = {}
        try:
            for fut in as_completed(futures, timeout=15):
                symbol = futures[fut]
                try:
                    _, data = fut.result()
                    results[symbol] = data
                except Exception as e:
                    send_alert(f"[오류] KRX {symbol}: {e}")
                    log_event(symbol, 0, 0, 'ERROR', str(e))
        except TimeoutError:
            timed_out = [futures[f] for f in futures if not f.done()]
            send_alert(f"[경고] KRX 조회 타임아웃: {timed_out}")
            for s in timed_out:
                log_event(s, 0, 0, 'ERROR', 'timeout')

    for symbol in symbols:
        if symbol not in results:
            continue
        try:
            data = results[symbol]
            pos = portfolio.positions.get(symbol)
            signal = generate_krx_signal(
                data, krx_cfg,
                has_position=pos is not None,
                added_once=pos.added_once if pos else False,
                avg_buy_price=pos.avg_price if pos else None,
            )

            if signal.type == SignalType.BUY and not market_halt and not daily_limit_hit and portfolio.can_open_position(CONFIG['portfolio']['max_positions']):
                amount = portfolio.capital * CONFIG['portfolio']['position_size_pct']
                ok = order_mgr.buy_krx(symbol, amount)
                if ok:
                    portfolio.open_position(symbol, data.price, CONFIG['portfolio']['position_size_pct'])
                    send_alert(f"[매수] {symbol} @ {data.price:,.0f}원 (이격률 {signal.deviation_rate:.1f}%)")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '매수' if ok else '매수실패', signal.reason)

            elif signal.type == SignalType.ADD and not market_halt and not daily_limit_hit and pos and not pos.added_once:
                amount = portfolio.capital * CONFIG['portfolio']['add_size_pct']
                ok = order_mgr.buy_krx(symbol, amount)
                if ok:
                    portfolio.add_to_position(symbol, data.price, CONFIG['portfolio']['add_size_pct'])
                    send_alert(f"[추가매수] {symbol} @ {data.price:,.0f}원")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '추가매수' if ok else '추가매수실패', signal.reason)

            elif signal.type in (SignalType.SELL, SignalType.STOP_LOSS) and pos:
                ok = order_mgr.sell_krx(symbol, pos.quantity)
                if ok:
                    pnl = portfolio.close_position(symbol, data.price)
                    risk_mgr.update_capital(portfolio.capital)
                    send_alert(f"[{signal.type.value}] {symbol} PnL: {pnl:.1f}%")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '매도' if ok else '매도실패', signal.reason)

            else:
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '', signal.reason)

        except Exception as e:
            send_alert(f"[오류] KRX {symbol}: {e}")
            log_event(symbol, 0, 0, 'ERROR', str(e))


def run_crypto_check():
    if risk_mgr.is_daily_limit_hit():
        return

    if check_emergency_close():
        _close_all_crypto()
        return

    crypto_cfg = CONFIG['crypto']
    for symbol in CONFIG['crypto']['symbols']:
        try:
            data = fetch_live_crypto_market_data(symbol, crypto_cfg['ma_window'])
            pos = portfolio.positions.get(symbol)
            signal = generate_crypto_signal(
                data, crypto_cfg,
                has_position=pos is not None,
                added_once=pos.added_once if pos else False,
                avg_buy_price=pos.avg_price if pos else None,
            )

            if signal.type == SignalType.BUY and portfolio.can_open_position(CONFIG['portfolio']['max_positions']):
                amount = portfolio.capital * CONFIG['portfolio']['position_size_pct']
                if order_mgr.buy_crypto(symbol, amount):
                    portfolio.open_position(symbol, data.price, CONFIG['portfolio']['position_size_pct'])
                    send_alert(f"[매수] {symbol} @ {data.price:,.2f} (이격률 {signal.deviation_rate:.1f}%)")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '매수', signal.reason)

            elif signal.type == SignalType.ADD and pos and not pos.added_once:
                amount = portfolio.capital * CONFIG['portfolio']['add_size_pct']
                if order_mgr.buy_crypto(symbol, amount):
                    portfolio.add_to_position(symbol, data.price, CONFIG['portfolio']['add_size_pct'])
                    send_alert(f"[추가매수] {symbol} @ {data.price:,.2f}")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '추가매수', signal.reason)

            elif signal.type in (SignalType.SELL, SignalType.STOP_LOSS) and pos:
                if order_mgr.sell_crypto(symbol, pos.quantity):
                    pnl = portfolio.close_position(symbol, data.price)
                    risk_mgr.update_capital(portfolio.capital)
                    send_alert(f"[{signal.type.value}] {symbol} PnL: {pnl:.1f}%")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '매도', signal.reason)

            else:
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '', signal.reason)

        except Exception as e:
            send_alert(f"[오류] Crypto {symbol}: {e}")
            log_event(symbol, 0, 0, 'ERROR', str(e))


def _close_all_krx():
    for symbol, pos in list(portfolio.positions.items()):
        if '/' not in symbol:
            order_mgr.sell_krx(symbol, pos.quantity)
            portfolio.close_position(symbol, pos.avg_price)
    save_state()
    send_alert("[긴급청산] KRX 전체 포지션 청산 완료")


def _close_all_crypto():
    for symbol, pos in list(portfolio.positions.items()):
        if '/' in symbol:
            order_mgr.sell_crypto(symbol, pos.quantity)
            portfolio.close_position(symbol, pos.avg_price)
    save_state()
    send_alert("[긴급청산] Crypto 전체 포지션 청산 완료")


def reset_daily():
    risk_mgr.reset_daily(portfolio.capital)


scheduler = BlockingScheduler(
    timezone='Asia/Seoul',
    job_defaults={'misfire_grace_time': 30},
)
if CONFIG['crypto'].get('enabled', True):
    scheduler.add_job(run_crypto_check, 'interval', minutes=1)
scheduler.add_job(run_krx_check, 'cron', day_of_week='mon-fri', hour='9-15', minute='*', max_instances=1, coalesce=True)
scheduler.add_job(refresh_universe_cache, 'cron', hour=8, minute=50)  # 장 시작 전 유니버스 갱신
scheduler.add_job(reset_daily, 'cron', hour=0, minute=0)

if __name__ == '__main__':
    capital = fetch_kis_cash_balance()
    if capital <= 0:
        print(f"[경고] 잔고 조회 실패 또는 잔고 없음 ({capital}원) — 계속 진행")
    portfolio.capital = capital
    risk_mgr.reset_daily(capital)
    save_state()
    print(f"트레이딩 시스템 시작 (잔고: {capital:,.0f}원)")
    send_alert(f"트레이딩 시스템 시작 (잔고: {capital:,.0f}원)")
    universe = get_universe()
    print(f"[유니버스] {len(universe)}개 종목 로드 완료")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        send_alert("트레이딩 시스템 종료")
        print("종료")
