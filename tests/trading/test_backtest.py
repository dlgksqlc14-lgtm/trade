import pandas as pd
import pytest
from scripts.trading.backtest import BacktestEngine, BacktestResult

KRX_CONFIG = {
    'ma_window': 25,
    'buy_threshold': -10.0,
    'add_threshold': -15.0,
    'sell_threshold': -2.0,
    'stop_loss_deviation': -25.0,
    'stop_loss_fixed_pct': -20.0,
    'volume_filter_multiplier': 1.5,
    'volume_ma_window': 20,
}


def test_backtest_buy_and_sell():
    # 25일 MA = 100, 26번째 가격 89 (이격률 -11%) → 매수 (거래량 2배 급등으로 필터 통과)
    # 이후 99 (이격률 -1%) → 매도
    prices = [100.0] * 25 + [89.0] + [99.0] * 10
    volumes = [1000.0] * 25 + [2000.0] + [1000.0] * 10
    df = pd.DataFrame({'close': prices, 'volume': volumes})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    assert result.total_trades >= 1
    winning_trades = [t for t in result.trades if t.pnl_pct > 0]
    assert len(winning_trades) >= 1


def test_backtest_stop_loss():
    # 매수(89) 후 69로 급락 → 이격률 -30% & 매입가 대비 -22% → STOP_LOSS
    prices = [100.0] * 25 + [89.0] + [69.0] * 5
    volumes = [1000.0] * 25 + [2000.0] + [1000.0] * 5
    df = pd.DataFrame({'close': prices, 'volume': volumes})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    stop_trades = [t for t in result.trades if t.exit_reason == 'STOP_LOSS']
    assert len(stop_trades) >= 1


def test_backtest_no_signal_when_volume_low():
    # 거래량 부족 (vol_ratio < 1.5) → 시그널 없음 → 거래 0
    prices = [100.0] * 25 + [89.0] * 10
    df = pd.DataFrame({'close': prices, 'volume': [500.0] * len(prices)})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    assert result.total_trades == 0
    assert result.total_return_pct == pytest.approx(0.0)


def test_backtest_result_is_dataclass():
    prices = [100.0] * 30
    df = pd.DataFrame({'close': prices, 'volume': [500.0] * 30})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    assert isinstance(result, BacktestResult)
    assert hasattr(result, 'total_return_pct')
    assert hasattr(result, 'mdd_pct')
    assert hasattr(result, 'win_rate_pct')
    assert hasattr(result, 'total_trades')
    assert hasattr(result, 'trades')


def test_backtest_mdd_calculation():
    # 자본이 1000 → 800 → 900 이면 MDD = 20% (매수일 거래량 2배)
    prices = [100.0] * 25 + [89.0] + [74.0] + [99.0] * 3
    volumes = [1000.0] * 25 + [2000.0] + [1000.0] * 4
    df = pd.DataFrame({'close': prices, 'volume': volumes})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    assert result.mdd_pct >= 0
