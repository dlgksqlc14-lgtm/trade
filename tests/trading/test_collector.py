import pandas as pd
import pytest
from scripts.trading.collector import prepare_market_data
from scripts.trading.signal import MarketData


def test_prepare_market_data_basic():
    df = pd.DataFrame({
        'close': [100.0] * 26,
        'volume': [1000.0] * 26,
    })
    data = prepare_market_data('TEST', df, ma_window=25, vol_window=20)
    assert data.symbol == 'TEST'
    assert data.price == pytest.approx(100.0)
    assert data.ma == pytest.approx(100.0)
    assert data.vol_ma == pytest.approx(1000.0)


def test_prepare_market_data_insufficient_rows():
    df = pd.DataFrame({'close': [100.0] * 10, 'volume': [1000.0] * 10})
    with pytest.raises(ValueError, match="insufficient data"):
        prepare_market_data('TEST', df, ma_window=25, vol_window=20)


def test_prepare_market_data_uses_last_row():
    prices = [100.0] * 25 + [89.0]
    df = pd.DataFrame({'close': prices, 'volume': [1000.0] * 26})
    data = prepare_market_data('TEST', df, ma_window=25, vol_window=20)
    assert data.price == pytest.approx(89.0)
    assert data.ma > 89.0  # MA는 89보다 높음
