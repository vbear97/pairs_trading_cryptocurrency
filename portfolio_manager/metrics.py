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
            
        #TODO - Note that sharpe ratio is the same regardless of initial capital, since it cancels out 
        def absolute_sharpe_ratio(self, net_pnl_series): 
            '''Absolute sharpe ratio on pnl series only'''
            return np.sqrt(self.periods_per_year) * net_pnl_series.mean() / net_pnl_series.std()

        def sharpe_ratio(self, net_pnl_series, initial_capital): 
            returns = net_pnl_series / initial_capital
            return np.sqrt(self.periods_per_year) * returns.mean() / returns.std()
        
        def absolute_sortino_ratio(self, net_pnl_series): 
            '''Absolute sortino based on pnl series only'''
            returns = net_pnl_series 
            downside_returns = returns[returns<0]
            return np.sqrt(self.periods_per_year) * downside_returns.mean() / downside_returns.std()
        
        def sortino_ratio(self, net_pnl_series, initial_capital):
            returns = net_pnl_series / initial_capital
            downside = returns[returns < 0]
            return np.sqrt(self.periods_per_year) * returns.mean() / downside.std()
        
        def _max_drawdown(self, returns): 
            cum_returns = 1+returns.cumsum()
            # rolling_max = cum_returns.cummax()
            # #TODO - why calculate as percentage? 
            # percentage_drawdown = (rolling_max - cum_returns)/cum_returns #measure decline from rolling peak 
            # max_drawdown = percentage_drawdown.max()
            # return max_drawdown
        
        def _max_drawdown_duration(self, returns): 
            pass 
        
        def absolute_calmar_ratio(self, net_pnl_series):
            '''Absolute calmar ratio based on pnl series only'''
            # returns = net_pnl_series
            # max_drawdown = self._absolute_max_drawdown(returns)
            # return np.sqrt(self.periods_per_year) * returns.mean() / max_drawdown

        def get_all(self, net_pnl_series, initial_capital):
            return {
                'absolute_sharpe': self.absolute_sharpe_ratio(net_pnl_series),
                'sharpe': self.sharpe_ratio(net_pnl_series, initial_capital),
                'absolute_sortino': self.absolute_sortino_ratio(net_pnl_series),
            }