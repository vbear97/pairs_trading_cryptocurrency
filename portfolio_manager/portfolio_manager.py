from typing import Dict, Tuple
import numpy as np 
import pandas as pd
from tqdm import tqdm 

from .constraints import ConstraintChecker, DummyConstraintChecker 
from .metrics import MetricsCalculator
from .pnl import PnLCalculator
from .transaction_costs import CostCalculator, DummyCostCalculator 

#TODO - fix up implementation of portfolio manager backtest 
#Should not separate out positions from prices 

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
                 trading_periods_per_year: int,
                 idealised: bool = False,
                 initial_capital: float = 10_000,
                 max_leverage: float = 3.0,
                 transaction_cost: float = 0.0025,
                 margin_threshold: float = 0.5, 
                 ):
        
        self.initial_capital = initial_capital
        self.position_history = []
        
        # Create helper objects
        if idealised:
            self.constraints = DummyConstraintChecker()
            self.costs = DummyCostCalculator()
        
        else: 
            self.constraints = ConstraintChecker(max_position_value=initial_capital * max_leverage, margin_threshold=margin_threshold)
            self.costs = CostCalculator(transaction_cost_rate=transaction_cost)
        
        self.pnl = PnLCalculator(
            initial_capital=initial_capital
        )
        self.metrics_calc = MetricsCalculator(periods_per_year = trading_periods_per_year)   
        self.is_liquidated = False
        self._reset()

    def _reset(self):
        """Reset state between backtests"""
        self.position_history = []
        self.index = None
        self.pnl = PnLCalculator(self.initial_capital)
        self.is_liquidated = False
    
    def backtest(self, 
                    desired_positions: pd.DataFrame, 
                    prices_y: pd.DataFrame, 
                    prices_x: pd.DataFrame) -> Dict:

        self._reset()
        self.index = desired_positions.index

        # Initialize positions and prices
        existing_position_y = 0.0 
        existing_position_x = 0.0
        prev_price_y = None
        prev_price_x = None
        
        # If our portfolio has been liquidated, we can no longer trade 
        for idx in tqdm(desired_positions.index):
            if self.is_liquidated:
                break

            # Current prices
            price_y, price_x = prices_y.loc[idx], prices_x.loc[idx]

            # 1. Calculate P&L from price changes on existing position
            if prev_price_y is not None:
                price_change_y = price_y - prev_price_y
                price_change_x = price_x - prev_price_x
                
                pnl = self.pnl.calculate_pnl(
                    existing_position_y, existing_position_x,
                    price_change_y, price_change_x
                )
            else:
                pnl = 0.0

            # 2. Rebalance portfolio, incur transaction costs
            desired_y, desired_x = desired_positions.loc[idx, ['position_y', 'position_x']]
            
            _, actual_y, actual_x = self.constraints.check_capital_limit(
                desired_y, desired_x, price_y, price_x
            )
            
            change_y = actual_y - existing_position_y
            change_x = actual_x - existing_position_x
            
            transaction_costs = self.costs.calculate_total_cost(
                change_y, change_x, price_y, price_x
            )

            # 3. Update P&L with profit and costs
            self.pnl.update(pnl, transaction_costs)
        
            # 4. Update positions and prices for next iteration
            existing_position_y = actual_y
            existing_position_x = actual_x
            prev_price_y = price_y
            prev_price_x = price_x

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
        risk_adjusted = self.metrics_calc.risk_adjusted.get_all(net_pnl_series, self.initial_capital)

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