import numpy as np 
class MetricsCalculator:
    """Helper: Calculate performance metrics (organized by category)"""
    
    def __init__(self, periods_per_year: int):
        """
        Args:
            periods_per_year: Number of periods per year for annualization
        """
        self.periods_per_year = periods_per_year
        self.risk_adjusted = self.RiskAdjusted(self.periods_per_year)  # Create instance
    
    class RiskAdjusted:
        """Risk-adjusted performance metrics"""
        
        def __init__(self, periods_per_year):
            self.periods_per_year = periods_per_year
        
        def sharpe_ratio(self, net_pnl_series, initial_capital):
            returns = net_pnl_series / initial_capital
            return np.sqrt(self.periods_per_year) * returns.mean() / returns.std()
        
        def sortino_ratio(self, net_pnl_series, initial_capital):
            returns = net_pnl_series / initial_capital
            downside = returns[returns < 0]
            return np.sqrt(self.periods_per_year) * returns.mean() / downside.std()
    
        def get_all(self, net_pnl_series, initial_capital):
            return {
                'sharpe': self.sharpe_ratio(net_pnl_series, initial_capital),
                'sortino': self.sortino_ratio(net_pnl_series, initial_capital),
            }