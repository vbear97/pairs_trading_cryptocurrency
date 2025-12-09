from typing import Dict, Tuple
import numpy as np 
import pandas as pd 

TRADING_DAYS_PER_YEAR = 365 #crypto-assets trade 24/7 

class PortfolioManager: 
    '''
    Main portfolio manager that translates position sizes into trading activity. 

    Uses: 
    - ConstraintChecker 
    - CostCalculator 
    - PnL Calculator 
    - Metrics Calculator 
        -Post trading evaluation 
    '''
    #TODO - put in terms of UNITS of bitcoin 
    def __init__(self,
                 initial_capital: float = 10_000,
                 max_leverage: float = 3.0,
                 transaction_cost: float = 0.0025,
                 margin_threshold: float = 0.5):
        
        self.initial_capital = initial_capital
        
        # Create helper objects
        self.position_history = []
        self.constraints = ConstraintChecker(
            max_position_value=initial_capital * max_leverage,
            margin_threshold=margin_threshold
        )
        self.costs = CostCalculator(
            transaction_cost_rate=transaction_cost
        )
        self.pnl = PnLCalculator(
            initial_capital=initial_capital
        )    
        self.is_liquidated = False
        self._reset()

    def _reset(self):
        """Reset state between backtests"""
        self.position_history = []
        self.index = None
        self.pnl = PnLCalculator(self.initial_capital)
        self.is_liquidated = False
    
    def _calc_results(self) -> Dict: 

        # Truncate index if liquidated early
        n = len(self.pnl.equity_curve)
        idx = self.index[:n]

        # Convert to Series with index
        equity_curve = pd.Series(self.pnl.equity_curve, index=idx)
        net_pnl_series = pd.Series(self.pnl.net_pnl_series, index=idx)
        gross_pnl_series = pd.Series(self.pnl.gross_pnl_series, index=idx)
        cost_series = pd.Series(self.pnl.cost_series, index=idx)
        position_history = pd.DataFrame(self.position_history, index=idx)

        #Basic metrics 
        total_return = (self.pnl.equity - self.initial_capital) / self.initial_capital
        total_costs = cost_series.sum()

        #Risk adjusted 
        risk_adjusted = MetricsCalculator.RiskAdjusted.get_all(net_pnl_series, self.initial_capital)

        return {
            'position_history': position_history,  
            'equity_curve': equity_curve, 
            'net_pnl_series': net_pnl_series, 
            'gross_pnl_series': gross_pnl_series,
            'cost_series': cost_series, 

            #summary metrics 
            'final_equity': self.pnl.equity, 
            'total_return': total_return, 
            'total_costs': total_costs, 
            'is_liquidated': self.is_liquidated, 

            #risk adjusted metrics 
            **risk_adjusted
        }
    
    #TODO - Make this code more tidier, just an absolute mess of stuff here 
    def backtest(self, 
                 desired_positions: pd.DataFrame, 
                 prices_y: pd.DataFrame, 
                 prices_x: pd.DataFrame) -> Dict:

        self._reset()
        self.index = desired_positions.index

        #Initialise 
        prev_position_y = 0.0   
        prev_position_x = 0.0
        
        #If our portfolio has been liquidated, we can no longer trade 
        for t, idx in enumerate(desired_positions.index):
            if self.is_liquidated:
                break
        
            #Snapshot: want to move to this position
            desired_y = desired_positions.loc[idx, 'position_y']
            desired_x = desired_positions.loc[idx, 'position_x']
            price_y = prices_y.loc[idx]
            price_x = prices_x.loc[idx]

            # 1. CONSTRAINTS: Check capital limit
            within_limit, actual_y, actual_x = self.constraints.check_capital_limit(
                desired_y, desired_x, price_y, price_x
            )
            
            # Calculate position changes
            change_y = actual_y - prev_position_y
            change_x = actual_x - prev_position_x
            
            # 2. COSTS: Apply transaction costs
            total_cost = self.costs.calculate_total_cost(
                change_y, change_x, price_y, price_x
            )

            # 3. P&L: Calculate from price changes
            if t > 0:
                prev_idx = desired_positions.index[t-1]
                price_change_y = price_y - prices_y.loc[prev_idx]
                price_change_x = price_x - prices_x.loc[prev_idx]
                
                pnl = self.pnl.calculate_pnl(
                    prev_position_y, prev_position_x,
                    price_change_y, price_change_x
                )
                self.pnl.update(pnl, total_cost)
            else:
                self.pnl.update(0.0, 0.0)
        
            #4. Update position 
            prev_position_y = actual_y
            prev_position_x = actual_x

            # 5. Update for next iteration
            prev_position_y = actual_y
            prev_position_x = actual_x

        return self._calculate_metrics()

class ConstraintChecker: 
    """Handle constraint enforcement"""
    def __init__(self, max_position_value: float, margin_threshold: float):
        self.max_position_value = max_position_value
        self.margin_threshold = margin_threshold

    def check_capital_limit(self, 
                            desired_y_units: int, 
                            desired_x_units: int, 
                            price_y: float, 
                            price_x: float
                            ) -> Tuple[bool, int, int]: 
        '''
        Constraint Rule
        -------------- 
        Total gross position exposure <= Initial Capital * Leverage 
        Returns: 
            (within_limit, actual_y_units, actual_x_units)
        '''
        #Sum up - absolute value of long/short legs 
        value_y = abs(desired_y_units * price_y)
        value_x = abs(desired_x_units * price_x)
        total_value = value_y + value_x

        if total_value > self.max_position_value: 
            #Scale down
            scale = self.max_position_value/total_value 
            actual_y_units = np.floor(desired_y_units*scale)
            actual_x_units = np.floor(desired_x_units*scale)
            return False, actual_y_units, actual_x_units
        else: 
            return True, desired_y_units, desired_x_units
        
    def check_margin_call(self, equity: float, initial_capital: float) -> bool: 
        '''
        Rule: Liquidate all positions when equity/initial_capital drops below threshold.
        '''
        liquidation_level = initial_capital * self.margin_threshold
        return equity < liquidation_level 


class CostCalculator:
    """Handles cost calculations per trade"""
    
    def __init__(self, transaction_cost_rate: float):
        self.transaction_cost_rate = transaction_cost_rate
    
    def calculate_trade_cost(self, 
                            position_change: float, 
                            current_price: float) -> float:
        """Calculate cost for one leg"""
        #TODO - Can make more complex one we incorporate other costs 
        trade_value = abs(position_change * current_price)
        return trade_value * self.transaction_cost_rate
    
    def calculate_total_cost(self,
                            position_change_y: float, 
                            position_change_: float,
                            current_price_y: float, 
                            current_price_x: float) -> float:
        """Calculate cost for both legs"""
        if position_change_y == 0 and position_change_ == 0:
            return 0.0
        
        cost_y = self.calculate_trade_cost(position_change_y, current_price_y)
        cost_x = self.calculate_trade_cost(position_change_, current_price_x)
        return cost_y + cost_x


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
        self.equity_curve(self.equity)
    
    def deduct_cost(self, total_cost): 
         self.pnl -= total_cost

    def get_equity(self) -> float:
        return self.equity
    

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
