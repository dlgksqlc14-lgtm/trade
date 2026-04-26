import pytest
from scripts.trading.trade_signal import (
    calc_deviation_rate,
    generate_krx_signal,
    generate_crypto_signal,
    MarketData,
    SignalType,
)

KRX_CONFIG = {
    'buy_threshold': -10.0,
    'add_threshold': -15.0,
    'sell_threshold': -2.0,
    'stop_loss_deviation': -25.0,
    'stop_loss_fixed_pct': -20.0,
    'volume_filter_multiplier': 1.5,
}

CRYPTO_CONFIG = {
    'buy_threshold': -12.0,
    'add_threshold': -20.0,
    'sell_threshold': -3.0,
    'stop_loss_deviation': -30.0,
}


def make_data(price: float, ma: float, volume: float = 1600, vol_ma: float = 1000) -> MarketData:
    return MarketData(symbol='TEST', price=price, ma=ma, volume=volume, vol_ma=vol_ma)


def test_calc_deviation_rate_negative():
    assert calc_deviation_rate(90, 100) == pytest.approx(-10.0)


def test_calc_deviation_rate_positive():
    assert calc_deviation_rate(110, 100) == pytest.approx(10.0)


def test_krx_buy_signal():
    # 이격률 -11%, 거래량 160% → BUY
    data = make_data(price=89, ma=100, volume=1600, vol_ma=1000)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=False, added_once=False, avg_buy_price=None)
    assert signal.type == SignalType.BUY


def test_krx_hold_when_volume_low():
    # 이격률 -11%지만 거래량 140% (필터 미달) → HOLD
    data = make_data(price=89, ma=100, volume=1400, vol_ma=1000)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=False, added_once=False, avg_buy_price=None)
    assert signal.type == SignalType.HOLD


def test_krx_add_signal():
    # 포지션 있고 이격률 -16%, 거래량 충분 → ADD
    data = make_data(price=84, ma=100, volume=1600, vol_ma=1000)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=True, added_once=False, avg_buy_price=90.0)
    assert signal.type == SignalType.ADD


def test_krx_no_add_when_already_added():
    # 이미 추가 매수 완료 → HOLD
    data = make_data(price=84, ma=100, volume=1600, vol_ma=1000)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=True, added_once=True, avg_buy_price=90.0)
    assert signal.type == SignalType.HOLD


def test_krx_sell_signal():
    # 포지션 있고 이격률 -1% → SELL
    data = make_data(price=99, ma=100)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=True, added_once=False, avg_buy_price=89.0)
    assert signal.type == SignalType.SELL


def test_krx_stop_loss_by_deviation():
    # 이격률 -26% → STOP_LOSS
    data = make_data(price=74, ma=100)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=True, added_once=False, avg_buy_price=89.0)
    assert signal.type == SignalType.STOP_LOSS


def test_krx_stop_loss_by_fixed_pct():
    # 매입가 100, 현재가 79 → -21% → STOP_LOSS (이격률은 -12%로 threshold 아님)
    data = make_data(price=79, ma=90)
    signal = generate_krx_signal(data, KRX_CONFIG, has_position=True, added_once=False, avg_buy_price=100.0)
    assert signal.type == SignalType.STOP_LOSS


def test_crypto_buy_signal():
    # 이격률 -13% → BUY (크립토는 볼륨 필터 없음)
    data = make_data(price=87, ma=100)
    signal = generate_crypto_signal(data, CRYPTO_CONFIG, has_position=False, added_once=False, avg_buy_price=None)
    assert signal.type == SignalType.BUY


def test_crypto_stop_loss():
    # 이격률 -31% → STOP_LOSS
    data = make_data(price=69, ma=100)
    signal = generate_crypto_signal(data, CRYPTO_CONFIG, has_position=True, added_once=False, avg_buy_price=80.0)
    assert signal.type == SignalType.STOP_LOSS
