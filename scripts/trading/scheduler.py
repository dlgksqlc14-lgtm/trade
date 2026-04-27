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
)
from scripts.trading.trade_signal import generate_krx_signal, generate_crypto_signal, SignalType
from scripts.trading.order import PortfolioState, OrderManager
from scripts.trading.risk import RiskManager
from scripts.trading.notifier import send_alert

with open('scripts/trading/config.yaml') as f:
    CONFIG = yaml.safe_load(f)

# 시총 1000억 이상 대형주
KRX_SYMBOLS = ['005930', '000660', '035420', '051910', '006400', '028260', '105560', '055550']

_initial_capital = fetch_kis_cash_balance()
portfolio = PortfolioState(capital=_initial_capital)
order_mgr = OrderManager(virtual=False)
risk_mgr = RiskManager(
    initial_capital=portfolio.capital,
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
    if risk_mgr.is_daily_limit_hit():
        return

    if check_emergency_close():
        _close_all_krx()
        return

    market_drop = fetch_kospi_daily_change()
    if market_drop <= CONFIG['krx']['market_drop_threshold']:
        send_alert(f"[KRX] 코스피 급락 {market_drop:.1f}% — 신규 매수 보류")
        return

    krx_cfg = CONFIG['krx']

    def fetch_krx(symbol):
        return symbol, fetch_live_krx_market_data(symbol, krx_cfg['ma_window'], krx_cfg['volume_ma_window'])

    with ThreadPoolExecutor(max_workers=len(KRX_SYMBOLS)) as ex:
        futures = {ex.submit(fetch_krx, s): s for s in KRX_SYMBOLS}
        results = {}
        for fut in as_completed(futures):
            symbol = futures[fut]
            try:
                _, data = fut.result()
                results[symbol] = data
            except Exception as e:
                send_alert(f"[오류] KRX {symbol}: {e}")
                log_event(symbol, 0, 0, 'ERROR', str(e))

    for symbol in KRX_SYMBOLS:
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

            if signal.type == SignalType.BUY and portfolio.can_open_position(CONFIG['portfolio']['max_positions']):
                amount = portfolio.capital * CONFIG['portfolio']['position_size_pct']
                if order_mgr.buy_krx(symbol, amount):
                    portfolio.open_position(symbol, data.price, CONFIG['portfolio']['position_size_pct'])
                    send_alert(f"[매수] {symbol} @ {data.price:,.0f}원 (이격률 {signal.deviation_rate:.1f}%)")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '매수', signal.reason)

            elif signal.type == SignalType.ADD and pos and not pos.added_once:
                amount = portfolio.capital * CONFIG['portfolio']['add_size_pct']
                if order_mgr.buy_krx(symbol, amount):
                    portfolio.add_to_position(symbol, data.price, CONFIG['portfolio']['add_size_pct'])
                    send_alert(f"[추가매수] {symbol} @ {data.price:,.0f}원")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '추가매수', signal.reason)

            elif signal.type in (SignalType.SELL, SignalType.STOP_LOSS) and pos:
                if order_mgr.sell_krx(symbol, pos.quantity):
                    pnl = portfolio.close_position(symbol, data.price)
                    risk_mgr.update_capital(portfolio.capital)
                    send_alert(f"[{signal.type.value}] {symbol} PnL: {pnl:.1f}%")
                    save_state()
                log_event(symbol, data.price, signal.deviation_rate, signal.type.value, '매도', signal.reason)

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


scheduler = BlockingScheduler(timezone='Asia/Seoul')
scheduler.add_job(run_crypto_check, 'interval', minutes=1)
scheduler.add_job(run_krx_check, 'cron', day_of_week='mon-fri', hour='9-15', minute='5,15,25,35,45,55')
scheduler.add_job(reset_daily, 'cron', hour=0, minute=0)

if __name__ == '__main__':
    save_state()
    print("트레이딩 시스템 시작")
    send_alert("트레이딩 시스템 시작")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        send_alert("트레이딩 시스템 종료")
        print("종료")
