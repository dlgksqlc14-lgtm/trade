from dataclasses import dataclass, field
import pandas as pd
from scripts.trading.trade_signal import generate_krx_signal, generate_crypto_signal, SignalType
from scripts.trading.collector import prepare_market_data


@dataclass
class Trade:
    symbol: str
    entry_price: float
    exit_price: float
    entry_date: str
    exit_date: str
    pnl_pct: float
    exit_reason: str  # "SELL" or "STOP_LOSS"


@dataclass
class BacktestResult:
    total_return_pct: float
    mdd_pct: float
    win_rate_pct: float
    total_trades: int
    trades: list[Trade] = field(default_factory=list)

    def print_summary(self):
        print(f"총 수익률: {self.total_return_pct:.2f}%")
        print(f"최대 낙폭(MDD): {self.mdd_pct:.2f}%")
        print(f"승률: {self.win_rate_pct:.1f}%")
        print(f"총 거래 수: {self.total_trades}")
        if self.trades:
            avg_pnl = sum(t.pnl_pct for t in self.trades) / len(self.trades)
            print(f"평균 수익률/거래: {avg_pnl:.2f}%")


class BacktestEngine:
    def __init__(self, config: dict, initial_capital: float = 1_000_000, signal_fn=None):
        self.config = config
        self.initial_capital = initial_capital
        self.signal_fn = signal_fn or generate_krx_signal

    def run(self, df: pd.DataFrame, symbol: str) -> BacktestResult:
        ma_window = self.config['ma_window']
        vol_window = self.config.get('volume_ma_window', ma_window)
        min_rows = max(ma_window, vol_window) + 1

        capital = self.initial_capital
        position_price: float | None = None
        entry_date: str = ""
        added_once = False
        trades: list[Trade] = []
        equity_curve: list[float] = [capital]

        for i in range(min_rows - 1, len(df)):
            window_df = df.iloc[:i + 1]
            try:
                market_data = prepare_market_data(symbol, window_df, ma_window, vol_window)
            except ValueError:
                continue

            date = str(df.index[i]) if hasattr(df.index[i], '__str__') else str(i)

            signal = self.signal_fn(
                market_data,
                self.config,
                has_position=position_price is not None,
                added_once=added_once,
                avg_buy_price=position_price,
            )

            if signal.type == SignalType.BUY and position_price is None:
                position_price = market_data.price
                entry_date = date

            elif signal.type == SignalType.ADD and position_price is not None and not added_once:
                position_price = (position_price + market_data.price) / 2
                added_once = True

            elif signal.type in (SignalType.SELL, SignalType.STOP_LOSS) and position_price is not None:
                pnl_pct = (market_data.price / position_price - 1) * 100
                capital *= (1 + pnl_pct / 100)
                trades.append(Trade(
                    symbol=symbol,
                    entry_price=position_price,
                    exit_price=market_data.price,
                    entry_date=entry_date,
                    exit_date=date,
                    pnl_pct=pnl_pct,
                    exit_reason=signal.type.value,
                ))
                position_price = None
                added_once = False

            equity_curve.append(capital)

        total_return_pct = (capital / self.initial_capital - 1) * 100
        mdd_pct = self._calc_mdd(equity_curve)
        wins = [t for t in trades if t.pnl_pct > 0]
        win_rate_pct = len(wins) / len(trades) * 100 if trades else 0.0

        return BacktestResult(
            total_return_pct=total_return_pct,
            mdd_pct=mdd_pct,
            win_rate_pct=win_rate_pct,
            total_trades=len(trades),
            trades=trades,
        )

    def _calc_mdd(self, equity_curve: list[float]) -> float:
        if not equity_curve:
            return 0.0
        peak = equity_curve[0]
        max_drawdown = 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown
