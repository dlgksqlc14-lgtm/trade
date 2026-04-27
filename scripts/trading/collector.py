import os
import pandas as pd
import FinanceDataReader as fdr
import ccxt
from dotenv import load_dotenv
from scripts.trading.trade_signal import MarketData

load_dotenv('scripts/trading/.env')


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


def _kis_base_url() -> str:
    virtual = os.getenv('KIS_VIRTUAL', 'true').lower() == 'true'
    return 'https://openapivts.koreainvestment.com:29443' if virtual else 'https://openapi.koreainvestment.com:9443'


_kis_token_cache: dict = {}


def get_kis_token() -> str:
    """KIS OAuth 액세스 토큰 발급 (만료 전까지 캐싱)"""
    import requests as req
    from datetime import datetime, timedelta

    cached = _kis_token_cache.get('token')
    expires_at = _kis_token_cache.get('expires_at')
    if cached and expires_at and datetime.now() < expires_at:
        return cached

    url = f"{_kis_base_url()}/oauth2/tokenP"
    body = {
        'grant_type': 'client_credentials',
        'appkey': os.getenv('KIS_APP_KEY'),
        'appsecret': os.getenv('KIS_APP_SECRET'),
    }
    resp = req.post(url, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _kis_token_cache['token'] = data['access_token']
    _kis_token_cache['expires_at'] = datetime.now() + timedelta(hours=23)
    return data['access_token']


def fetch_kis_price(symbol: str, token: str) -> tuple[float, float]:
    """KIS API로 현재가, 거래량 반환"""
    import requests as req
    url = f"{_kis_base_url()}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        'authorization': f'Bearer {token}',
        'appkey': os.getenv('KIS_APP_KEY'),
        'appsecret': os.getenv('KIS_APP_SECRET'),
        'tr_id': 'FHKST01010100',
    }
    params = {'fid_cond_mrkt_div_code': 'J', 'fid_input_iscd': symbol}
    resp = req.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    output = resp.json()['output']
    return float(output['stck_prpr']), float(output['acml_vol'])


def fetch_kis_cash_balance() -> float:
    """KIS API로 주문가능 예수금(원) 반환"""
    import requests as req
    virtual = os.getenv('KIS_VIRTUAL', 'true').lower() == 'true'
    token = get_kis_token()
    url = f"{_kis_base_url()}/uapi/domestic-stock/v1/trading/inquire-balance"
    account_no = os.getenv('KIS_ACCOUNT_NO', '')
    cano = account_no.replace('-', '')[:8]
    acnt_cd = account_no.split('-')[-1] if '-' in account_no else '01'
    headers = {
        'authorization': f'Bearer {token}',
        'appkey': os.getenv('KIS_APP_KEY'),
        'appsecret': os.getenv('KIS_APP_SECRET'),
        'tr_id': 'VTTC8434R' if virtual else 'TTTC8434R',
    }
    params = {
        'CANO': cano,
        'ACNT_PRDT_CD': acnt_cd,
        'AFHR_FLPR_YN': 'N',
        'OFL_YN': '',
        'INQR_DVSN': '02',
        'UNPR_DVSN': '01',
        'FUND_STTL_ICLD_YN': 'N',
        'FNCG_AMT_AUTO_RDPT_YN': 'N',
        'PRCS_DVSN': '01',
        'CTX_AREA_FK100': '',
        'CTX_AREA_NK100': '',
    }
    resp = req.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    output2 = resp.json().get('output2', [{}])
    return float(output2[0].get('dnca_tot_amt', 0)) if output2 else 0.0


def fetch_live_krx_market_data(symbol: str, ma_window: int = 25, vol_window: int = 20) -> MarketData:
    """KIS API 현재가로 마지막 행을 교체한 MarketData 반환"""
    days = max(ma_window, vol_window) + 5
    df = fetch_krx_ohlcv(symbol, days=days)
    token = get_kis_token()
    price, volume = fetch_kis_price(symbol, token)
    df = df.copy()
    df.iloc[-1, df.columns.get_loc('close')] = price
    df.iloc[-1, df.columns.get_loc('volume')] = volume
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
