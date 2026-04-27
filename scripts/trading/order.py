import os
from dataclasses import dataclass, field
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
    initial_capital: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)

    def __post_init__(self):
        if self.initial_capital == 0.0:
            self.initial_capital = self.capital

    def can_open_position(self, max_positions: int) -> bool:
        return len(self.positions) < max_positions

    def open_position(self, symbol: str, price: float, size_pct: float):
        amount = self.initial_capital * size_pct
        if amount > self.capital:
            amount = self.capital
        quantity = amount / price
        self.positions[symbol] = Position(symbol=symbol, avg_price=price, quantity=quantity)
        self.capital -= amount

    def add_to_position(self, symbol: str, price: float, size_pct: float):
        pos = self.positions[symbol]
        add_amount = self.initial_capital * size_pct
        if add_amount > self.capital:
            add_amount = self.capital
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

    def _kis_order(self, symbol: str, qty: int, side: str) -> bool:
        import requests as req
        from scripts.trading.collector import get_kis_token, _kis_base_url
        virtual = os.getenv('KIS_VIRTUAL', 'true').lower() == 'true'
        tr_id = {'buy': 'VTTC0802U', 'sell': 'VTTC0801U'} if virtual else {'buy': 'TTTC0802U', 'sell': 'TTTC0801U'}
        token = get_kis_token()
        url = f"{_kis_base_url()}/uapi/domestic-stock/v1/trading/order-cash"
        headers = {
            'authorization': f'Bearer {token}',
            'appkey': os.getenv('KIS_APP_KEY'),
            'appsecret': os.getenv('KIS_APP_SECRET'),
            'tr_id': tr_id[side],
        }
        body = {
            'CANO': os.getenv('KIS_ACCOUNT_NO', '').replace('-', '')[:8],
            'ACNT_PRDT_CD': os.getenv('KIS_ACCOUNT_NO', '').split('-')[-1] if '-' in os.getenv('KIS_ACCOUNT_NO', '') else '01',
            'PDNO': symbol,
            'ORD_DVSN': '01',  # 시장가
            'ORD_QTY': str(qty),
            'ORD_UNPR': '0',
        }
        resp = req.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
        return resp.json().get('rt_cd') == '0'

    def buy_krx(self, symbol: str, amount: float) -> bool:
        from scripts.trading.collector import get_kis_token, fetch_kis_price
        try:
            token = get_kis_token()
            price, _ = fetch_kis_price(symbol, token)
            qty = int(amount / price)
            if qty < 1:
                return False
            return self._kis_order(symbol, qty, 'buy')
        except Exception as e:
            print(f"[OrderManager] KRX 매수 실패 {symbol}: {e}")
            return False

    def sell_krx(self, symbol: str, quantity: float) -> bool:
        try:
            return self._kis_order(symbol, int(quantity), 'sell')
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
