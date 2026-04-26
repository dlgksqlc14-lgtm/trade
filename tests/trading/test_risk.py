from scripts.trading.risk import RiskManager


def test_daily_loss_not_exceeded():
    rm = RiskManager(initial_capital=1_000_000, daily_loss_limit_pct=5.0)
    rm.update_capital(980_000)  # -2%
    assert not rm.is_daily_limit_hit()


def test_daily_loss_exceeded():
    rm = RiskManager(initial_capital=1_000_000, daily_loss_limit_pct=5.0)
    rm.update_capital(940_000)  # -6%
    assert rm.is_daily_limit_hit()


def test_reset_daily():
    rm = RiskManager(initial_capital=1_000_000, daily_loss_limit_pct=5.0)
    rm.update_capital(940_000)
    assert rm.is_daily_limit_hit()
    rm.reset_daily(new_capital=940_000)
    assert not rm.is_daily_limit_hit()


def test_exact_boundary():
    rm = RiskManager(initial_capital=1_000_000, daily_loss_limit_pct=5.0)
    rm.update_capital(950_000)  # 정확히 -5%
    assert rm.is_daily_limit_hit()
