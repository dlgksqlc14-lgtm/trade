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

    if has_position and avg_buy_price is not None:
        fixed_loss_pct = (data.price / avg_buy_price - 1) * 100
        if dev <= config['stop_loss_deviation'] or fixed_loss_pct <= config['stop_loss_fixed_pct']:
            return Signal(SignalType.STOP_LOSS, data.symbol, dev, data.price)

    if has_position and dev >= config['sell_threshold']:
        return Signal(SignalType.SELL, data.symbol, dev, data.price)

    if has_position and not added_once and dev <= config['add_threshold']:
        if vol_ratio >= config['volume_filter_multiplier']:
            return Signal(SignalType.ADD, data.symbol, dev, data.price)

    if not has_position and dev <= config['buy_threshold']:
        if vol_ratio >= config['volume_filter_multiplier']:
            return Signal(SignalType.BUY, data.symbol, dev, data.price)

    return Signal(SignalType.HOLD, data.symbol, dev, data.price)


def generate_crypto_signal(
    data: MarketData,
    config: dict,
    has_position: bool,
    added_once: bool,
    avg_buy_price: float | None,
) -> Signal:
    dev = calc_deviation_rate(data.price, data.ma)

    if has_position and avg_buy_price is not None:
        if dev <= config['stop_loss_deviation']:
            return Signal(SignalType.STOP_LOSS, data.symbol, dev, data.price)

    if has_position and dev >= config['sell_threshold']:
        return Signal(SignalType.SELL, data.symbol, dev, data.price)

    if has_position and not added_once and dev <= config['add_threshold']:
        return Signal(SignalType.ADD, data.symbol, dev, data.price)

    if not has_position and dev <= config['buy_threshold']:
        return Signal(SignalType.BUY, data.symbol, dev, data.price)

    return Signal(SignalType.HOLD, data.symbol, dev, data.price)
