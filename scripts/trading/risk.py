class RiskManager:
    def __init__(self, initial_capital: float, daily_loss_limit_pct: float):
        self.daily_start_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_loss_limit_pct = daily_loss_limit_pct

    def update_capital(self, capital: float):
        self.current_capital = capital

    def is_daily_limit_hit(self) -> bool:
        if self.daily_start_capital <= 0:
            return False
        loss_pct = (self.current_capital / self.daily_start_capital - 1) * 100
        return loss_pct <= -self.daily_loss_limit_pct

    def reset_daily(self, new_capital: float):
        self.daily_start_capital = new_capital
        self.current_capital = new_capital
