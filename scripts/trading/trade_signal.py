from dataclasses import dataclass
from enum import Enum


class SignalType(str, Enum):
    BUY = "BUY"
    ADD = "ADD"
    SELL = "SELL"
    STOP_LOSS = "STOP_LOSS"
    HOLD = "HOLD"


@dataclass
class MarketData:
    symbol: str
    price: float
    ma: float
    volume: float
    vol_ma: float


@dataclass
class Signal:
    type: SignalType
    symbol: str
    deviation_rate: float
    price: float
    reason: str = ""


def calc_deviation_rate(price: float, ma: float) -> float:
    return (price / ma - 1) * 100


def generate_krx_signal(
    data: MarketData,
    config: dict,
    has_position: bool,
    added_once: bool,
    avg_buy_price: float | None,
) -> Signal:
    dev = calc_deviation_rate(data.price, data.ma)
    vol_ratio = data.volume / data.vol_ma if data.vol_ma > 0 else 0

    def sig(t, reason):
        return Signal(t, data.symbol, dev, data.price, reason)

    if has_position and avg_buy_price is not None:
        fixed_loss_pct = (data.price / avg_buy_price - 1) * 100
        if dev <= config['stop_loss_deviation'] or fixed_loss_pct <= config['stop_loss_fixed_pct']:
            return sig(SignalType.STOP_LOSS, f"손실 이격 {dev:+.1f}% / 보유손실 {fixed_loss_pct:+.1f}%")

    if has_position and dev >= config['sell_threshold']:
        return sig(SignalType.SELL, f"이격 {dev:+.1f}% ≥ {config['sell_threshold']:+.1f}%")

    if has_position and not added_once and dev <= config['add_threshold']:
        if vol_ratio >= config['volume_filter_multiplier']:
            return sig(SignalType.ADD, f"이격 {dev:+.1f}% ≤ {config['add_threshold']:+.1f}%")
        return sig(SignalType.HOLD, f"추가매수 이격 충족({dev:+.1f}%) 거래량 부족({vol_ratio:.1f}x)")

    if not has_position and dev <= config['buy_threshold']:
        if vol_ratio >= config['volume_filter_multiplier']:
            return sig(SignalType.BUY, f"이격 {dev:+.1f}% ≤ {config['buy_threshold']:+.1f}%")
        return sig(SignalType.HOLD, f"매수 이격 충족({dev:+.1f}%) 거래량 부족({vol_ratio:.1f}x)")

    if has_position:
        return sig(SignalType.HOLD, f"이격 {dev:+.1f}% (매도기준 {config['sell_threshold']:+.1f}%)")
    return sig(SignalType.HOLD, f"이격 {dev:+.1f}% (매수기준 {config['buy_threshold']:+.1f}%)")


def generate_crypto_signal(
    data: MarketData,
    config: dict,
    has_position: bool,
    added_once: bool,
    avg_buy_price: float | None,
) -> Signal:
    dev = calc_deviation_rate(data.price, data.ma)

    def sig(t, reason):
        return Signal(t, data.symbol, dev, data.price, reason)

    if has_position and avg_buy_price is not None:
        fixed_loss_pct = (data.price / avg_buy_price - 1) * 100
        if dev <= config['stop_loss_deviation']:
            return sig(SignalType.STOP_LOSS, f"손실 이격 {dev:+.1f}% / 보유손실 {fixed_loss_pct:+.1f}%")

    if has_position and dev >= config['sell_threshold']:
        return sig(SignalType.SELL, f"이격 {dev:+.1f}% ≥ {config['sell_threshold']:+.1f}%")

    if has_position and not added_once and dev <= config['add_threshold']:
        return sig(SignalType.ADD, f"이격 {dev:+.1f}% ≤ {config['add_threshold']:+.1f}%")

    if not has_position and dev <= config['buy_threshold']:
        return sig(SignalType.BUY, f"이격 {dev:+.1f}% ≤ {config['buy_threshold']:+.1f}%")

    if has_position:
        return sig(SignalType.HOLD, f"이격 {dev:+.1f}% (매도기준 {config['sell_threshold']:+.1f}%)")
    return sig(SignalType.HOLD, f"이격 {dev:+.1f}% (매수기준 {config['buy_threshold']:+.1f}%)")
