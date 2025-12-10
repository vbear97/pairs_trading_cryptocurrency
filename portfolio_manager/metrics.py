TRADING_DAYS_PER_YEAR = 365 #crypto-assets trade 24/7 
import numpy as np 
class MetricsCalculator:
    """Helper: Calculate performance metrics (organized by category)"""
    class RiskAdjusted:
        """Risk-adjusted performance metrics"""
        
        @staticmethod
        def sharpe_ratio(net_pnl_series, initial_capital):
            returns = net_pnl_series / initial_capital
            return np.sqrt(TRADING_DAYS_PER_YEAR) * returns.mean() / returns.std()
        
        @staticmethod
        def sortino_ratio(net_pnl_series, initial_capital):
            returns = net_pnl_series / initial_capital
            downside = returns[returns < 0]
            return np.sqrt(TRADING_DAYS_PER_YEAR) * returns.mean() / downside.std()
        
        # @staticmethod
        # def calmar_ratio(total_return, max_dd):
        #     return total_return / abs(max_dd) if max_dd != 0 else 0
    
        @staticmethod
        def get_all(net_pnl_series, initial_capital):
            return {
                'sharpe': MetricsCalculator.RiskAdjusted.sharpe_ratio(net_pnl_series, initial_capital),
                'sortino': MetricsCalculator.RiskAdjusted.sortino_ratio(net_pnl_series, initial_capital),
                #'calmar': MetricsCalculator.RiskAdjusted.calmar_ratio(total_return, max_dd)
            }
        
    #TODO - Fix maximum drawdown 
    # class Drawdown:
    #     """Drawdown risk metrics"""
    #     @staticmethod
    #     def max_drawdown(equity_curve):
    #         #cumulative maximum
    #         running_max = np.maximum.accumulate(equity_curve)
    #         drawdowns = (equity_curve - running_max) / running_max
    #         return drawdowns.max()

    #     @staticmethod
    #     def get_all(equity_curve):
    #         """Get all drawdown metrics at once"""
    #         return {
    #             'max_drawdown': MetricsCalculator.Drawdown.max_drawdown(equity_curve)
    #         }