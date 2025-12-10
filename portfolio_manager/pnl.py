class PnLCalculator:
    """Handles P&L calculations and tracking"""
    
    def __init__(self, initial_capital: float): 
        self.initial_capital = initial_capital
        self.equity = initial_capital #Equity = current net worth in the account = Initial Capital + Cumulative P&L - Cumulative Costs
        self.equity_curve = []
        self.gross_pnl_series = []
        self.net_pnl_series = []
        self.cost_series = []
    
    def calculate_pnl(self,
                     current_position_y: float,
                     current_position_x: float,
                     price_change_y: float,
                     price_change_x: float) -> float:
        """Calculate mark-to-market P&L"""
        return current_position_y * price_change_y + current_position_x * price_change_x
    
    def update(self, pnl: float, cost: float):
        """Update equity with PnL and costs together"""
        net_pnl = pnl - cost 
        self.equity += net_pnl 
        self.gross_pnl_series.append(pnl) #before costs
        self.net_pnl_series.append(net_pnl) #after costs
        self.cost_series.append(cost)
        self.equity_curve.append(self.equity)
    
    def deduct_cost(self, total_cost): 
         self.pnl -= total_cost

    def get_equity(self) -> float:
        return self.equity