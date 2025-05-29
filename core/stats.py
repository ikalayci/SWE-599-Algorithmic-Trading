# core/stats.py
class TradingStats:
    def __init__(self):
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit_usdt = 0
        self.total_profit_percentage = 0
        self.max_drawdown = 0
        self.best_trade = 0
        self.worst_trade = 0
        self.average_profit_per_trade = 0
        self.win_rate = 0
        self.active_trades = {}
        self.trade_history = []

    def add_trade_history(self, trade_data: dict):
        """İşlem geçmişine yeni işlem ekle"""
        self.trade_history.append(trade_data)
        
        # Satış işlemiyse istatistikleri güncelle
        if trade_data['type'] == 'sell':
            profit = trade_data.get('profit', 0)
            if profit > self.best_trade:
                self.best_trade = profit
            if profit < self.worst_trade:
                self.worst_trade = profit
            
            if self.total_trades > 0:
                self.average_profit_per_trade = self.total_profit_usdt / self.total_trades
                self.win_rate = (self.winning_trades / self.total_trades) * 100