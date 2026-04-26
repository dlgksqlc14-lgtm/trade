# Auto Trading System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** BNF 이격도 기반 역추세 자동매매 시스템을 단계적으로 구현한다 — Phase 1 백테스트로 전략 수익성 검증 후, Phase 2+3에서 실거래 자동화와 대시보드까지 완성한다.

**Architecture:** Signal Engine이 이격도를 계산해 시그널을 생성하고, Order Manager가 포지션을 관리하며 거래소 API에 주문을 전송한다. Scheduler가 전체 파이프라인을 주기적으로 실행하고, FastAPI 대시보드가 현황을 표시한다. 스케줄러와 대시보드는 `state.json`을 통해 상태를 공유한다.

**Tech Stack:** Python 3.11+, pandas, FinanceDataReader (KRX 히스토리컬), pykis (KIS 실시간), ccxt (Binance), APScheduler, FastAPI + Jinja2

---

## File Map

| 파일 | 역할 |
|------|------|
| `scripts/trading/config.yaml` | 전략 파라미터 (이격도 임계값, 포지션 사이즈 등) |
| `scripts/trading/.env.example` | API 키 템플릿 (git 포함) |
| `scripts/trading/.env` | 실제 API 키 (gitignore) |
| `scripts/trading/signal.py` | `MarketData`, `Signal`, `SignalType`, `generate_krx_signal`, `generate_crypto_signal` |
| `scripts/trading/collector.py` | `fetch_krx_ohlcv`, `fetch_crypto_ohlcv`, `prepare_market_data`, `fetch_live_krx_market_data`, `fetch_live_crypto_market_data` |
| `scripts/trading/backtest.py` | `Trade`, `BacktestResult`, `BacktestEngine` |
| `scripts/trading/order.py` | `Position`, `PortfolioState`, `OrderManager` |
| `scripts/trading/risk.py` | `RiskManager` |
| `scripts/trading/notifier.py` | `send_alert` |
| `scripts/trading/scheduler.py` | APScheduler 메인 루프, `state.json` 갱신 |
| `scripts/trading/dashboard.py` | FastAPI 앱, `state.json` 읽기 |
| `scripts/trading/templates/index.html` | 대시보드 HTML |
| `scripts/trading/requirements.txt` | 의존성 목록 |
| `scripts/trading/deploy.sh` | AWS EC2 배포 스크립트 |
| `tests/trading/test_signal.py` | signal.py 단위 테스트 |
| `tests/trading/test_collector.py` | collector.py 단위 테스트 |
| `tests/trading/test_backtest.py` | backtest.py 테스트 |
| `tests/trading/test_order.py` | order.py 테스트 |
| `tests/trading/test_risk.py` | risk.py 테스트 |

---

## ⚠️ Phase 체크포인트

**Task 1~4 완료 후 백테스트 결과를 반드시 확인하세요.**
다음 기준을 모두 충족할 때만 Task 5 이후(실거래)로 진행합니다:
- 총 수익률 > 0%
- 최대 낙폭(MDD) < 20%
- 승률 > 50%
- 총 거래 수 > 10 (충분한 샘플)

---

## Phase 1: 백테스트

### Task 1: 프로젝트 스캐폴딩

**Files:**
- Create: `scripts/trading/config.yaml`
- Create: `scripts/trading/.env.example`
- Create: `scripts/trading/requirements.txt`
- Create: `tests/trading/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p scripts/trading tests/trading scripts/trading/templates
touch tests/trading/__init__.py
```

- [ ] **Step 2: config.yaml 작성**

`scripts/trading/config.yaml`:
```yaml
krx:
  ma_window: 25
  buy_threshold: -10.0
  add_threshold: -15.0
  sell_threshold: -2.0
  stop_loss_deviation: -25.0
  stop_loss_fixed_pct: -20.0
  volume_filter_multiplier: 1.5
  volume_ma_window: 20
  market_drop_threshold: -3.0

crypto:
  symbols:
    - BTC/USDT
    - ETH/USDT
  ma_window: 20
  buy_threshold: -12.0
  add_threshold: -20.0
  sell_threshold: -3.0
  stop_loss_deviation: -30.0

portfolio:
  max_positions: 4
  position_size_pct: 0.22
  add_size_pct: 0.11

risk:
  daily_loss_limit_pct: 0.05
```

- [ ] **Step 3: .env.example 작성**

`scripts/trading/.env.example`:
```
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCOUNT_NO=your_account_number
KIS_VIRTUAL=true

BINANCE_API_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret
BINANCE_TESTNET=true

KAKAO_ACCESS_TOKEN=your_kakao_token
```

- [ ] **Step 4: requirements.txt 작성**

`scripts/trading/requirements.txt`:
```
finance-datareader>=0.9.0
pykis>=1.0.0
ccxt>=4.0.0
pandas>=2.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
apscheduler>=3.10.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
requests>=2.31.0
jinja2>=3.1.0
pytest>=7.0.0
```

- [ ] **Step 5: .gitignore에 .env 추가**

`.gitignore` 파일에 다음 줄이 없으면 추가:
```
scripts/trading/.env
scripts/trading/state.json
scripts/trading/emergency_close.flag
```

- [ ] **Step 6: 의존성 설치**

```bash
pip install -r scripts/trading/requirements.txt
```

Expected: 오류 없이 설치 완료

- [ ] **Step 7: 커밋**

```bash
git add scripts/trading/config.yaml scripts/trading/.env.example scripts/trading/requirements.txt tests/trading/__init__.py .gitignore
git commit -m "feat: add trading project scaffold and config"
```

---

### Task 2: Signal Engine

**Files:**
- Create: `scripts/trading/signal.py`
- Create: `tests/trading/test_signal.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/trading/test_signal.py`:
```python
import pytest
from scripts.trading.signal import (
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
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/trading/test_signal.py -v
```
Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: signal.py 구현**

`scripts/trading/signal.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/trading/test_signal.py -v
```
Expected: 10개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add scripts/trading/signal.py tests/trading/test_signal.py
git commit -m "feat: add signal engine with BNF deviation rate strategy"
```

---

### Task 3: Historical Data Collector

**Files:**
- Create: `scripts/trading/collector.py`
- Create: `tests/trading/test_collector.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/trading/test_collector.py`:
```python
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
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/trading/test_collector.py -v
```
Expected: `ImportError`

- [ ] **Step 3: collector.py 구현 (historical 부분)**

`scripts/trading/collector.py`:
```python
import pandas as pd
import FinanceDataReader as fdr
import ccxt
from scripts.trading.signal import MarketData


def fetch_krx_ohlcv(symbol: str, days: int = 800) -> pd.DataFrame:
    """KRX 종목 일봉 데이터. symbol 예: '005930' (삼성전자)"""
    df = fdr.DataReader(symbol)
    df.columns = [c.lower() for c in df.columns]
    df = df[['close', 'volume']].dropna()
    return df.tail(days)


def fetch_crypto_ohlcv(symbol: str, days: int = 730) -> pd.DataFrame:
    """Binance 일봉 데이터. symbol 예: 'BTC/USDT'"""
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, '1d', limit=days)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df[['close', 'volume']]


def fetch_kospi_daily_change() -> float:
    """코스피 지수 당일 등락률(%) 반환. 장 종료 전에는 전일 대비 현재 등락률."""
    df = fdr.DataReader('^KS11')
    df.columns = [c.lower() for c in df.columns]
    if 'change' in df.columns:
        return float(df['change'].iloc[-1]) * 100
    close = df['close']
    return float((close.iloc[-1] / close.iloc[-2] - 1) * 100)


def prepare_market_data(
    symbol: str,
    df: pd.DataFrame,
    ma_window: int = 25,
    vol_window: int = 20,
) -> MarketData:
    min_rows = max(ma_window, vol_window) + 1
    if len(df) < min_rows:
        raise ValueError(f"insufficient data: need {min_rows} rows, got {len(df)}")

    ma = df['close'].rolling(ma_window).mean().iloc[-1]
    vol_ma = df['volume'].rolling(vol_window).mean().iloc[-1]
    price = float(df['close'].iloc[-1])
    volume = float(df['volume'].iloc[-1])

    return MarketData(symbol=symbol, price=price, ma=float(ma), volume=volume, vol_ma=float(vol_ma))
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/trading/test_collector.py -v
```
Expected: 3개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add scripts/trading/collector.py tests/trading/test_collector.py
git commit -m "feat: add historical data collector for KRX and Binance"
```

---

### Task 4: Backtest Engine

**Files:**
- Create: `scripts/trading/backtest.py`
- Create: `tests/trading/test_backtest.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/trading/test_backtest.py`:
```python
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
    # 25일 MA = 100, 26번째 가격 89 (이격률 -11%) → 매수
    # 이후 99 (이격률 -1%) → 매도
    prices = [100.0] * 25 + [89.0] + [99.0] * 10
    df = pd.DataFrame({'close': prices, 'volume': [2000.0] * len(prices)})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    assert result.total_trades >= 1
    winning_trades = [t for t in result.trades if t.pnl_pct > 0]
    assert len(winning_trades) >= 1


def test_backtest_stop_loss():
    # 매수 후 -26% 이격 → 손절
    prices = [100.0] * 25 + [89.0] + [74.0] * 5
    df = pd.DataFrame({'close': prices, 'volume': [2000.0] * len(prices)})
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
    # 자본이 1000 → 800 → 900 이면 MDD = 20%
    prices = [100.0] * 25 + [89.0] + [74.0] + [99.0] * 3
    df = pd.DataFrame({'close': prices, 'volume': [2000.0] * len(prices)})
    engine = BacktestEngine(KRX_CONFIG, initial_capital=1_000_000)
    result = engine.run(df, 'TEST')
    assert result.mdd_pct >= 0
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/trading/test_backtest.py -v
```
Expected: `ImportError`

- [ ] **Step 3: backtest.py 구현**

`scripts/trading/backtest.py`:
```python
from dataclasses import dataclass, field
import pandas as pd
from scripts.trading.signal import generate_krx_signal, SignalType
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
    def __init__(self, config: dict, initial_capital: float = 1_000_000):
        self.config = config
        self.initial_capital = initial_capital

    def run(self, df: pd.DataFrame, symbol: str) -> BacktestResult:
        ma_window = self.config['ma_window']
        vol_window = self.config['volume_ma_window']
        min_rows = max(ma_window, vol_window) + 1

        capital = self.initial_capital
        position_price: float | None = None
        entry_date: str = ""
        added_once = False
        trades: list[Trade] = []
        equity_curve: list[float] = [capital]

        for i in range(min_rows, len(df)):
            window_df = df.iloc[:i + 1]
            try:
                market_data = prepare_market_data(symbol, window_df, ma_window, vol_window)
            except ValueError:
                continue

            date = str(df.index[i]) if hasattr(df.index[i], '__str__') else str(i)

            signal = generate_krx_signal(
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/trading/test_backtest.py -v
```
Expected: 5개 테스트 모두 PASS

- [ ] **Step 5: 실제 데이터로 백테스트 수동 실행**

Python REPL에서:
```python
import yaml
from scripts.trading.collector import fetch_krx_ohlcv, fetch_crypto_ohlcv
from scripts.trading.backtest import BacktestEngine

with open('scripts/trading/config.yaml') as f:
    config = yaml.safe_load(f)

# 삼성전자 3년 백테스트
df_samsung = fetch_krx_ohlcv('005930', days=800)
engine = BacktestEngine(config['krx'], initial_capital=1_000_000)
result = engine.run(df_samsung, '005930')
result.print_summary()

# BTC 2년 백테스트
df_btc = fetch_crypto_ohlcv('BTC/USDT', days=730)
engine_crypto = BacktestEngine(config['crypto'], initial_capital=1_000_000)
result_btc = engine_crypto.run(df_btc, 'BTC/USDT')
result_btc.print_summary()
```

Expected output 예시:
```
총 수익률: 12.50%
최대 낙폭(MDD): 8.30%
승률: 65.0%
총 거래 수: 20
평균 수익률/거래: 0.63%
```

- [ ] **Step 6: 커밋**

```bash
git add scripts/trading/backtest.py tests/trading/test_backtest.py
git commit -m "feat: add backtest engine with MDD and win rate report"
```

---

## ⚠️ Phase 1 완료 — 전략 수익성 확인 후 Phase 2 진행

---

## Phase 2: 실거래 시스템

### Task 5: Live Data Collector

**Files:**
- Modify: `scripts/trading/collector.py`
- Modify: `tests/trading/test_collector.py`

- [ ] **Step 1: .env 파일 생성 (실제 API 키 입력)**

```bash
cp scripts/trading/.env.example scripts/trading/.env
# 편집기로 .env를 열어 실제 KIS App Key, App Secret, 계좌번호 입력
# Binance API Key, Secret 입력
```

- [ ] **Step 2: 실패 테스트 추가**

`tests/trading/test_collector.py` 하단에 추가:
```python
from unittest.mock import patch, MagicMock


def test_prepare_market_data_with_updated_price():
    # 마지막 close를 실시간 가격으로 교체하는 패턴 검증
    df = pd.DataFrame({'close': [100.0] * 26, 'volume': [1000.0] * 26})
    df_copy = df.copy()
    df_copy.iloc[-1, df_copy.columns.get_loc('close')] = 95.0
    data = prepare_market_data('TEST', df_copy, ma_window=25, vol_window=20)
    assert data.price == pytest.approx(95.0)
    assert data.ma == pytest.approx(100.0)  # MA는 업데이트 전 값 기준
```

- [ ] **Step 3: 실패 확인**

```bash
pytest tests/trading/test_collector.py::test_prepare_market_data_with_updated_price -v
```
Expected: FAIL (함수가 없으므로)

- [ ] **Step 4: collector.py에 live 함수 추가**

`scripts/trading/collector.py` 상단 import 뒤에 추가:
```python
import os
from dotenv import load_dotenv

load_dotenv('scripts/trading/.env')
```

`scripts/trading/collector.py` 하단에 추가:
```python
def get_kis_client():
    from pykis import PyKis
    return PyKis(
        app_key=os.getenv('KIS_APP_KEY'),
        app_secret=os.getenv('KIS_APP_SECRET'),
        account_no=os.getenv('KIS_ACCOUNT_NO'),
        virtual=os.getenv('KIS_VIRTUAL', 'true').lower() == 'true',
    )


def fetch_live_krx_market_data(symbol: str, ma_window: int = 25, vol_window: int = 20) -> MarketData:
    """KIS API 현재가로 마지막 행을 교체한 MarketData 반환"""
    days = max(ma_window, vol_window) + 5
    df = fetch_krx_ohlcv(symbol, days=days)
    kis = get_kis_client()
    quote = kis.stock(symbol).quote()
    df = df.copy()
    df.iloc[-1, df.columns.get_loc('close')] = float(quote.price)
    df.iloc[-1, df.columns.get_loc('volume')] = float(quote.volume)
    return prepare_market_data(symbol, df, ma_window, vol_window)


def fetch_live_crypto_market_data(symbol: str, ma_window: int = 20, vol_window: int = 20) -> MarketData:
    """ccxt로 현재가를 가져와 마지막 행을 교체한 MarketData 반환"""
    days = max(ma_window, vol_window) + 5
    df = fetch_crypto_ohlcv(symbol, days=days)
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_SECRET'),
    })
    if os.getenv('BINANCE_TESTNET', 'true').lower() == 'true':
        exchange.set_sandbox_mode(True)
    ticker = exchange.fetch_ticker(symbol)
    df = df.copy()
    df.iloc[-1, df.columns.get_loc('close')] = float(ticker['last'])
    return prepare_market_data(symbol, df, ma_window, vol_window)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
pytest tests/trading/test_collector.py -v
```
Expected: 모든 테스트 PASS

- [ ] **Step 6: 커밋**

```bash
git add scripts/trading/collector.py tests/trading/test_collector.py
git commit -m "feat: add live data collector for KIS and Binance"
```

---

### Task 6: Order Manager + Position Tracker

**Files:**
- Create: `scripts/trading/order.py`
- Create: `tests/trading/test_order.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/trading/test_order.py`:
```python
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
    assert 80.0 < pos.avg_price < 100.0  # 평균 단가는 두 가격 사이


def test_portfolio_total_value():
    state = PortfolioState(capital=1_000_000)
    state.open_position('TEST', price=1000.0, size_pct=0.22)
    value = state.total_value({'TEST': 1100.0})
    assert value > 1_000_000
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/trading/test_order.py -v
```
Expected: `ImportError`

- [ ] **Step 3: order.py 구현**

`scripts/trading/order.py`:
```python
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

load_dotenv('scripts/trading/.env')


@dataclass
class Position:
    symbol: str
    avg_price: float
    quantity: float
    added_once: bool = False


@dataclass
class PortfolioState:
    capital: float
    positions: dict[str, Position] = field(default_factory=dict)

    def can_open_position(self, max_positions: int) -> bool:
        return len(self.positions) < max_positions

    def open_position(self, symbol: str, price: float, size_pct: float):
        amount = self.capital * size_pct
        quantity = amount / price
        self.positions[symbol] = Position(symbol=symbol, avg_price=price, quantity=quantity)
        self.capital -= amount

    def add_to_position(self, symbol: str, price: float, size_pct: float):
        pos = self.positions[symbol]
        add_amount = self.capital * size_pct
        add_qty = add_amount / price
        total_qty = pos.quantity + add_qty
        pos.avg_price = (pos.avg_price * pos.quantity + price * add_qty) / total_qty
        pos.quantity = total_qty
        pos.added_once = True
        self.capital -= add_amount

    def close_position(self, symbol: str, price: float) -> float:
        pos = self.positions.pop(symbol)
        pnl_pct = (price / pos.avg_price - 1) * 100
        self.capital += pos.quantity * price
        return pnl_pct

    def total_value(self, current_prices: dict[str, float]) -> float:
        pos_value = sum(
            pos.quantity * current_prices.get(symbol, pos.avg_price)
            for symbol, pos in self.positions.items()
        )
        return self.capital + pos_value

    def to_dict(self) -> dict:
        return {
            'capital': self.capital,
            'positions': {
                s: {'avg_price': p.avg_price, 'quantity': p.quantity, 'added_once': p.added_once}
                for s, p in self.positions.items()
            },
        }


class OrderManager:
    def __init__(self, virtual: bool = True):
        self.virtual = virtual

    def buy_krx(self, symbol: str, amount: float) -> bool:
        from scripts.trading.collector import get_kis_client
        try:
            kis = get_kis_client()
            stock = kis.stock(symbol)
            price = float(stock.quote().price)
            qty = int(amount / price)
            if qty < 1:
                return False
            stock.buy(qty=qty)
            return True
        except Exception as e:
            print(f"[OrderManager] KRX 매수 실패 {symbol}: {e}")
            return False

    def sell_krx(self, symbol: str, quantity: float) -> bool:
        from scripts.trading.collector import get_kis_client
        try:
            kis = get_kis_client()
            kis.stock(symbol).sell(qty=int(quantity))
            return True
        except Exception as e:
            print(f"[OrderManager] KRX 매도 실패 {symbol}: {e}")
            return False

    def buy_crypto(self, symbol: str, amount: float) -> bool:
        import ccxt
        try:
            exchange = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET'),
            })
            if os.getenv('BINANCE_TESTNET', 'true').lower() == 'true':
                exchange.set_sandbox_mode(True)
            exchange.create_market_buy_order(symbol, amount)
            return True
        except Exception as e:
            print(f"[OrderManager] Crypto 매수 실패 {symbol}: {e}")
            return False

    def sell_crypto(self, symbol: str, quantity: float) -> bool:
        import ccxt
        try:
            exchange = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET'),
            })
            if os.getenv('BINANCE_TESTNET', 'true').lower() == 'true':
                exchange.set_sandbox_mode(True)
            exchange.create_market_sell_order(symbol, quantity)
            return True
        except Exception as e:
            print(f"[OrderManager] Crypto 매도 실패 {symbol}: {e}")
            return False
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/trading/test_order.py -v
```
Expected: 6개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add scripts/trading/order.py tests/trading/test_order.py
git commit -m "feat: add order manager and portfolio state tracker"
```

---

### Task 7: Risk Manager

**Files:**
- Create: `scripts/trading/risk.py`
- Create: `tests/trading/test_risk.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/trading/test_risk.py`:
```python
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
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/trading/test_risk.py -v
```

- [ ] **Step 3: risk.py 구현**

`scripts/trading/risk.py`:
```python
class RiskManager:
    def __init__(self, initial_capital: float, daily_loss_limit_pct: float):
        self.daily_start_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_loss_limit_pct = daily_loss_limit_pct

    def update_capital(self, capital: float):
        self.current_capital = capital

    def is_daily_limit_hit(self) -> bool:
        loss_pct = (self.current_capital / self.daily_start_capital - 1) * 100
        return loss_pct <= -self.daily_loss_limit_pct

    def reset_daily(self, new_capital: float):
        self.daily_start_capital = new_capital
        self.current_capital = new_capital
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/trading/test_risk.py -v
```
Expected: 4개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add scripts/trading/risk.py tests/trading/test_risk.py
git commit -m "feat: add risk manager with daily loss limit"
```

---

### Task 8: Notifier

**Files:**
- Create: `scripts/trading/notifier.py`

- [ ] **Step 1: notifier.py 작성**

`scripts/trading/notifier.py`:
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv('scripts/trading/.env')


def send_alert(message: str):
    token = os.getenv('KAKAO_ACCESS_TOKEN')
    if token:
        _send_kakao(message, token)
    else:
        print(f"[ALERT] {message}")


def _send_kakao(message: str, token: str):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "template_object": {
            "object_type": "text",
            "text": message,
            "link": {"web_url": "", "mobile_web_url": ""},
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Notifier] 카카오 전송 실패: {e}")
```

- [ ] **Step 2: 커밋**

```bash
git add scripts/trading/notifier.py
git commit -m "feat: add kakao notifier for trade alerts"
```

---

### Task 9: Scheduler (메인 루프)

**Files:**
- Create: `scripts/trading/scheduler.py`

- [ ] **Step 1: scheduler.py 작성**

`scripts/trading/scheduler.py`:
```python
import json
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler

from scripts.trading.collector import (
    fetch_live_krx_market_data,
    fetch_live_crypto_market_data,
    fetch_kospi_daily_change,
)
from scripts.trading.signal import generate_krx_signal, generate_crypto_signal, SignalType
from scripts.trading.order import PortfolioState, OrderManager
from scripts.trading.risk import RiskManager
from scripts.trading.notifier import send_alert

with open('scripts/trading/config.yaml') as f:
    CONFIG = yaml.safe_load(f)

# 시총 1000억 이상 대형주 (직접 선정)
KRX_SYMBOLS = ['005930', '000660', '035420', '051910', '006400', '028260', '105560', '055550']

portfolio = PortfolioState(capital=500_000)
order_mgr = OrderManager(virtual=True)
risk_mgr = RiskManager(
    initial_capital=portfolio.capital,
    daily_loss_limit_pct=CONFIG['risk']['daily_loss_limit_pct'] * 100,
)

STATE_FILE = 'scripts/trading/state.json'
EMERGENCY_FLAG = 'scripts/trading/emergency_close.flag'


def save_state():
    with open(STATE_FILE, 'w') as f:
        json.dump(portfolio.to_dict(), f, ensure_ascii=False, indent=2)


def check_emergency_close():
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
    for symbol in KRX_SYMBOLS:
        try:
            data = fetch_live_krx_market_data(symbol, krx_cfg['ma_window'], krx_cfg['volume_ma_window'])
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

            elif signal.type == SignalType.ADD and pos and not pos.added_once:
                amount = portfolio.capital * CONFIG['portfolio']['add_size_pct']
                if order_mgr.buy_krx(symbol, amount):
                    portfolio.add_to_position(symbol, data.price, CONFIG['portfolio']['add_size_pct'])
                    send_alert(f"[추가매수] {symbol} @ {data.price:,.0f}원")
                    save_state()

            elif signal.type in (SignalType.SELL, SignalType.STOP_LOSS) and pos:
                if order_mgr.sell_krx(symbol, pos.quantity):
                    pnl = portfolio.close_position(symbol, data.price)
                    risk_mgr.update_capital(portfolio.capital)
                    send_alert(f"[{signal.type.value}] {symbol} PnL: {pnl:.1f}%")
                    save_state()

        except Exception as e:
            send_alert(f"[오류] KRX {symbol}: {e}")


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

            elif signal.type == SignalType.ADD and pos and not pos.added_once:
                amount = portfolio.capital * CONFIG['portfolio']['add_size_pct']
                if order_mgr.buy_crypto(symbol, amount):
                    portfolio.add_to_position(symbol, data.price, CONFIG['portfolio']['add_size_pct'])
                    send_alert(f"[추가매수] {symbol} @ {data.price:,.2f}")
                    save_state()

            elif signal.type in (SignalType.SELL, SignalType.STOP_LOSS) and pos:
                if order_mgr.sell_crypto(symbol, pos.quantity):
                    pnl = portfolio.close_position(symbol, data.price)
                    risk_mgr.update_capital(portfolio.capital)
                    send_alert(f"[{signal.type.value}] {symbol} PnL: {pnl:.1f}%")
                    save_state()

        except Exception as e:
            send_alert(f"[오류] Crypto {symbol}: {e}")


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
    print("트레이딩 시스템 시작 (모의투자 모드)")
    send_alert("트레이딩 시스템 시작")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        send_alert("트레이딩 시스템 종료")
        print("종료")
```

- [ ] **Step 2: 모의투자 모드로 실행 확인**

```bash
# .env의 KIS_VIRTUAL=true, BINANCE_TESTNET=true 확인
python scripts/trading/scheduler.py
```
Expected: "트레이딩 시스템 시작 (모의투자 모드)" 출력, 스케줄러 실행

- [ ] **Step 3: 커밋**

```bash
git add scripts/trading/scheduler.py
git commit -m "feat: add APScheduler main trading loop with emergency close"
```

---

## Phase 3: 대시보드 + 배포

### Task 10: Web Dashboard

**Files:**
- Create: `scripts/trading/dashboard.py`
- Create: `scripts/trading/templates/index.html`

- [ ] **Step 1: dashboard.py 작성**

`scripts/trading/dashboard.py`:
```python
import json
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="scripts/trading/templates")
STATE_FILE = "scripts/trading/state.json"
EMERGENCY_FLAG = "scripts/trading/emergency_close.flag"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"capital": 0, "positions": {}}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": load_state()})


@app.get("/api/state")
async def get_state():
    return load_state()


@app.post("/api/emergency-close")
async def emergency_close():
    with open(EMERGENCY_FLAG, "w") as f:
        f.write("1")
    return {"status": "emergency close requested"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

- [ ] **Step 2: index.html 작성**

`scripts/trading/templates/index.html`:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Trading Dashboard</title>
  <style>
    body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; }
    h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
    .stat { display: inline-block; margin: 10px 20px 10px 0; }
    .stat strong { font-size: 1.4em; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }
    th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
    th { background: #f0f0f0; font-weight: bold; }
    .btn-danger { background: #e53e3e; color: white; padding: 12px 24px; border: none; cursor: pointer; border-radius: 4px; font-size: 1em; }
    .btn-danger:hover { background: #c53030; }
  </style>
</head>
<body>
  <h1>Trading Dashboard</h1>

  <div class="stat">잔고: <strong>{{ "{:,.0f}".format(state.capital) }}원</strong></div>
  <div class="stat">포지션 수: <strong>{{ state.positions | length }}</strong></div>

  <h2>현재 포지션</h2>
  <table>
    <tr><th>종목</th><th>평균 단가</th><th>수량</th><th>추가매수</th></tr>
    {% for symbol, pos in state.positions.items() %}
    <tr>
      <td>{{ symbol }}</td>
      <td>{{ "{:,.2f}".format(pos.avg_price) }}</td>
      <td>{{ "{:.6f}".format(pos.quantity) }}</td>
      <td>{{ "완료" if pos.added_once else "-" }}</td>
    </tr>
    {% else %}
    <tr><td colspan="4" style="text-align:center; color:#999">포지션 없음</td></tr>
    {% endfor %}
  </table>

  <button class="btn-danger" onclick="emergencyClose()">⚠️ 긴급 전체 청산</button>

  <script>
    function emergencyClose() {
      if (!confirm("모든 포지션을 즉시 청산합니다. 계속하시겠습니까?")) return;
      fetch('/api/emergency-close', { method: 'POST' })
        .then(r => r.json())
        .then(() => { alert("긴급 청산 요청 전송 완료. 다음 스케줄 사이클에서 실행됩니다."); })
        .catch(e => alert("오류: " + e));
    }
    setTimeout(() => location.reload(), 30000);
  </script>
</body>
</html>
```

- [ ] **Step 3: 대시보드 실행 확인**

```bash
python scripts/trading/dashboard.py
```
브라우저에서 `http://localhost:8080` 접속 → 포지션 테이블과 긴급 청산 버튼 확인

- [ ] **Step 4: 커밋**

```bash
git add scripts/trading/dashboard.py scripts/trading/templates/index.html
git commit -m "feat: add FastAPI dashboard with position view and emergency close"
```

---

### Task 11: AWS 배포

**Files:**
- Create: `scripts/trading/deploy.sh`

- [ ] **Step 1: AWS EC2 t3.micro 생성 (수동)**

AWS 콘솔 (`console.aws.amazon.com`) 에서:
1. EC2 → Launch Instance
2. AMI: **Ubuntu 22.04 LTS**
3. Instance type: **t3.micro**
4. Region: **ap-northeast-2 (Seoul)**
5. Key pair: 새로 생성 → `.pem` 파일 저장
6. Security Group 인바운드 규칙:
   - 포트 22 (SSH): 내 IP만
   - 포트 8080 (Dashboard): 내 IP만

- [ ] **Step 2: deploy.sh 작성**

`scripts/trading/deploy.sh`:
```bash
#!/bin/bash
# 사용법: ./scripts/trading/deploy.sh <EC2_PUBLIC_IP> <KEY_PEM_PATH>
set -e

EC2_IP=$1
KEY=$2

if [ -z "$EC2_IP" ] || [ -z "$KEY" ]; then
  echo "Usage: $0 <EC2_IP> <KEY_PEM>"
  exit 1
fi

echo "코드 전송 중..."
rsync -avz \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude 'state.json' \
  --exclude 'emergency_close.flag' \
  -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
  scripts/trading/ ubuntu@$EC2_IP:~/trading/
rsync -avz -e "ssh -i $KEY" tests/ ubuntu@$EC2_IP:~/tests/

echo "의존성 설치 중..."
ssh -i $KEY ubuntu@$EC2_IP "
  sudo apt-get update -q
  sudo apt-get install -y python3-pip python3-venv screen
  cd ~ && python3 -m venv venv
  ~/venv/bin/pip install -r ~/trading/requirements.txt -q
"

echo ""
echo "배포 완료!"
echo ""
echo "다음 단계:"
echo "  1. .env 파일 전송:"
echo "     scp -i $KEY scripts/trading/.env ubuntu@$EC2_IP:~/trading/.env"
echo "  2. EC2 접속:"
echo "     ssh -i $KEY ubuntu@$EC2_IP"
echo "  3. 스케줄러 실행:"
echo "     screen -S trader"
echo "     ~/venv/bin/python ~/trading/scheduler.py"
echo "     (Ctrl+A, D 로 detach)"
echo "  4. 대시보드 실행:"
echo "     screen -S dashboard"
echo "     ~/venv/bin/python ~/trading/dashboard.py"
```

- [ ] **Step 3: 실행 권한 부여 및 커밋**

```bash
chmod +x scripts/trading/deploy.sh
git add scripts/trading/deploy.sh
git commit -m "feat: add AWS EC2 deployment script"
```

- [ ] **Step 4: 배포 실행**

```bash
# .env를 EC2에 업로드 (코드와 분리)
scp -i <KEY>.pem scripts/trading/.env ubuntu@<EC2_IP>:~/trading/.env

# 코드 배포
./scripts/trading/deploy.sh <EC2_IP> <KEY>.pem
```

---

## 전체 테스트 실행

```bash
pytest tests/trading/ -v
```
Expected: 모든 테스트 PASS

---

## 주요 주의사항

| 항목 | 내용 |
|------|------|
| `pykis` 주문 API | `stock.buy(qty=N)` 시장가, `stock.sell(qty=N)` 시장가 — 실제 pykis 버전에 따라 파라미터 확인 필요 |
| KRX_SYMBOLS | 현재 하드코딩된 8개 종목 — 시가총액 1000억 이상 직접 선정. 확장 시 DART API로 자동화 가능 |
| 긴급 청산 타이밍 | 대시보드 버튼 → `emergency_close.flag` 생성 → 다음 스케줄 사이클(최대 1분)에서 실행 |
| 모의투자 → 실투자 전환 | `.env`에서 `KIS_VIRTUAL=false`, `BINANCE_TESTNET=false` 로 변경 |
