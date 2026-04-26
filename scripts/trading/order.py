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
