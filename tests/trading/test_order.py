import pytest
from scripts.trading.order import Position, PortfolioState

PORTFOLIO_CONFIG = {
    'max_positions': 4,
    'position_size_pct': 0.22,
    'add_size_pct': 0.11,
}


def test_open_position():
    state = PortfolioState(capital=1_000_000)
    state.open_position('005930', price=70000.0, size_pct=0.22)
    assert '005930' in state.positions
    assert state.positions['005930'].avg_price == pytest.approx(70000.0)
    assert state.capital == pytest.approx(1_000_000 - 1_000_000 * 0.22)


def test_close_position_profit():
    state = PortfolioState(capital=1_000_000)
    state.open_position('005930', price=70000.0, size_pct=0.22)
    pnl = state.close_position('005930', price=77000.0)
    assert pnl == pytest.approx(10.0, abs=0.1)
    assert '005930' not in state.positions


def test_close_position_loss():
    state = PortfolioState(capital=1_000_000)
    state.open_position('005930', price=70000.0, size_pct=0.22)
    pnl = state.close_position('005930', price=63000.0)
    assert pnl == pytest.approx(-10.0, abs=0.1)


def test_can_open_position_max():
    state = PortfolioState(capital=1_000_000)
    for i in range(4):
        state.open_position(f'STOCK{i}', price=100.0, size_pct=0.22)
    assert not state.can_open_position(max_positions=4)


def test_add_to_position():
    state = PortfolioState(capital=1_000_000)
    state.open_position('BTC/USDT', price=100.0, size_pct=0.22)
    state.add_to_position('BTC/USDT', price=80.0, size_pct=0.11)
    pos = state.positions['BTC/USDT']
    assert pos.added_once is True
    assert 80.0 < pos.avg_price < 100.0


def test_portfolio_total_value():
    state = PortfolioState(capital=1_000_000)
    state.open_position('TEST', price=1000.0, size_pct=0.22)
    value = state.total_value({'TEST': 1100.0})
    assert value > 1_000_000
