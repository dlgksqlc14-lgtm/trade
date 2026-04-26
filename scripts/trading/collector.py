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
