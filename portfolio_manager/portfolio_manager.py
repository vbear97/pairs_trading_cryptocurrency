from typing import Dict, Tuple
import numpy as np 
import pandas as pd

from pairs_trading_cryptocurrency.portfolio_manager.constraints import ConstraintChecker, DummyConstraintChecker 
from pairs_trading_cryptocurrency.portfolio_manager.metrics import MetricsCalculator
from pairs_trading_cryptocurrency.portfolio_manager.pnl import PnLCalculator
from pairs_trading_cryptocurrency.portfolio_manager.transaction_costs import CostCalculator, DummyCostCalculator 

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
                 idealised: bool = False,
                 initial_capital: float = 10_000,
                 max_leverage: float = 3.0,
                 transaction_cost: float = 0.0025,
                 margin_threshold: float = 0.5):
        
        self.initial_capital = initial_capital
        self.position_history = []
        
        # Create helper objects
        if idealised:
            self.constraints = DummyConstraintChecker()
            self.costs = DummyCostCalculator()
            
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

        return self._calc_results()
    
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