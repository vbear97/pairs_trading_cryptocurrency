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
        self.position_history = {'position_y': [], 'position_x': []}
        
        # Create helper objects
        if idealised:
            self.constraints = DummyConstraintChecker()
            self.costs = DummyCostCalculator()
        
        else: 
            self.constraints = ConstraintChecker(max_position_value=initial_capital * max_leverage, margin_threshold=margin_threshold)
            self.costs = CostCalculator(transaction_cost_rate=transaction_cost)
        
        self.pnl_calculator = PnLCalculator(
            initial_capital=initial_capital
        )
        self.metrics_calc = MetricsCalculator(periods_per_year = trading_periods_per_year)   
        self.is_liquidated = False
        self._reset()

    def _reset(self):
        """Reset state between backtests"""
        self.position_history = {'position_y': [], 'position_x': []}
        self.index = None
        self.pnl_calculator = PnLCalculator(self.initial_capital)
        self.is_liquidated = False

    def _rebalance_portfolio(self, price: pd.Series, existing_position: float, new_position: float):
        '''Rebalance position of one asset using current bid/ask prices.'''
        change = new_position - existing_position
        if change == 0:
            return 0.0
        if change > 0:  # Going more LONG, therefore buy MORE at the ask price 
            gross_cash_flow = -change * price['ask']
        else:  # Going more short: 
            gross_cash_flow = -change * price['bid']
        return gross_cash_flow
    
    def _mark_to_market_position(self, price: pd.Series, new_position: float) -> float: 
        '''Calculate mark to market position of one asset using current bid/ask prices'''
        if new_position < 0: 
            #short position value = close by BUYING at the ask price 
            return new_position*price['ask']
        elif new_position > 0: 
            #long position value = close by SELLING at the bid price 
            return new_position*price['bid']
        else: 
            return 0.0
    
    def backtest(self, 
                    close_position: pd.DataFrame, 
                    prices_y: pd.DataFrame, 
                    prices_x: pd.DataFrame,
                    instant_execution: bool = False
                    ) -> Dict:
        '''
        - Assumptions: 
            - Close_position represents desired position at END of every timestep t, prices are prices at END of every timestep t 
            - Assume we can execute x and y at the same time 
        
        - Args: 
            -instant_execution: bool = True 
                - Whether or not to assume instantantaneous execution, i.e. observe trading signal at end of period t, and then adjust position based on prices at end of period t 
            - prices_y, prices_x: : 2 col dataframe with col 'bid' and 'ask' 
        '''
        self._reset()
        self.index = close_position.index

        # Initialize positions and prices
        existing_position_y = 0.0 
        existing_position_x = 0.0

        if not instant_execution: 
            #1 period lag: at end of period t-1 we have desired position that we can only execute based on period t prices 
            close_position = close_position.shift(1, fill_value = 0.0)
        
        # If our portfolio has been liquidated, we can no longer trade 
        for idx in tqdm(close_position.index):
            if self.is_liquidated: 
                break

            #TODO - deal with special case of the first signal 
            # Current prices 
            price_y, price_x = prices_y.loc[idx], prices_x.loc[idx]

            #1. Rebalance portfolio and calculate cash flows 
            ##Rebalance portfolio 
            desired_y, desired_x = close_position.loc[idx, ['position_y', 'position_x']]
            #TODO - Redo this once we enact capital limits - no problem for now 
            _, new_position_y, new_position_x = self.constraints.check_capital_limit(
                desired_y, desired_x, price_y, price_x
            )
            self.position_history['position_y'].append(new_position_y)
            self.position_history['position_x'].append(new_position_x)

            ##Cash flows 
            cash_flow_y = self._rebalance_portfolio(price_y, existing_position_y, new_position_y)
            cash_flow_x= self._rebalance_portfolio(price_x, existing_position_x, new_position_x)
            cash_flow = cash_flow_y + cash_flow_x

            # Cost 
            #TODO - change once we incorporate transaction costs
            transaction_costs = self.costs.calculate_total_cost()

            #2. Calculate mark to market position value of new position 
            position_value_y = self._mark_to_market_position(price_y, new_position_y)
            position_value_x = self._mark_to_market_position(price_x, new_position_x)
            position_value = position_value_y + position_value_x
            
            #3. Update position 
            existing_position_y = new_position_y
            existing_position_x = new_position_x

            #4. Update PnL 
            self.pnl_calculator.update(cash_flow, position_value, transaction_costs)
        
        self.pnl_calculator.summarise()
        return self._calc_results()

    def _calc_results(self) -> Dict: 

        # Truncate index if liquidated early
        n = len(self.pnl_calculator.equity_curve)
        idx = self.index[:n]

        #Risk adjusted 
        equity = pd.Series(self.pnl_calculator.equity_curve, index=idx)
        pnl = equity.diff()
        risk_adjusted = self.metrics_calc.risk_adjusted.get_all(pnl, self.initial_capital)

        return {
            'position_history': pd.DataFrame(self.position_history, index=idx), 
            'cost': pd.Series(self.pnl_calculator.cost_series, index=idx),
            'cash_flow': pd.Series(self.pnl_calculator.cash_flow_series, index = idx),
            'cash_holdings': pd.Series(self.pnl_calculator.cash_holdings, index = idx),
            'position_value':  pd.Series(self.pnl_calculator.position_value_series, index = idx),
            'equity_curve': equity, 
            'pnl': pnl,

            #summary metrics 
            'final_equity': self.pnl_calculator.equity, 
            'is_liquidated': self.is_liquidated, 

            #risk adjusted metrics 
            **risk_adjusted
        }