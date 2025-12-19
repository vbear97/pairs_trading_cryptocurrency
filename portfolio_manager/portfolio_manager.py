from typing import Dict, Tuple
import numpy as np 
import pandas as pd
from tqdm import tqdm 

from .constraints import ConstraintChecker, DummyConstraintChecker 
from .metrics import MetricsCalculator
from .pnl import PnLCalculator
from .transaction_costs import CostCalculator 

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
                 transaction_cost: float = 0.0,
                 hourly_interest_rate_by_coin: dict = {},
                 margin_threshold: float = 0.5, 
                 ):
        
        self.initial_capital = initial_capital
        
        # Create helper objects
        if idealised:
            self.constraints = DummyConstraintChecker()
        
        else: 
            self.constraints = ConstraintChecker(max_position_value=initial_capital * max_leverage, margin_threshold=margin_threshold)
        
        self.costs =  CostCalculator(transaction_cost_rate=transaction_cost, hourly_interest_rate_by_coin = hourly_interest_rate_by_coin)
        self.metrics_calc = MetricsCalculator(periods_per_year = trading_periods_per_year)   
        self.is_liquidated = False

    def _calc_cash_flow_by_coin(self, position_change_by_coin: Dict[str, float], current_price: pd.Series) -> pd.Series: 
        '''Rebalance position of one asset using current bid/ask prices.'''
        #buy into long at the ask price, get proceeds of short sale at bid price
        return pd.Series({
        coin: -delta * current_price[coin]['ask' if delta > 0 else 'bid']
        for coin, delta in position_change_by_coin.items()
        })

    def _calc_m2m_by_coin(self, position: pd.Series, price: pd.Series,) -> pd.Series: 
        '''Calculate mark to market position of one asset using current bid/ask prices'''
        m2m_by_coin = {
            #to close a short/long position, we buy/sell at the ask/bid price 
            coin: position*price[coin]['ask' if position < 0 else 'bid'] for (coin, position) in position.items() }
        return pd.Series(m2m_by_coin)
    
    def _calc_results(self, pnl_calculator: PnLCalculator, position_df: pd.DataFrame) -> Dict: 
        pnl = pnl_calculator.cum_df['equity_curve'].diff()
        risk_adjusted = self.metrics_calc.risk_adjusted.get_all(pnl, self.initial_capital)
        
        return {
            'summary_df': pd.concat([
                position_df,
                pnl_calculator.summary_df,
            ], axis=1, keys = ['Position', 'PnL']
            ),  
            **risk_adjusted
        }

    def backtest(self, 
                    close_position_df: pd.DataFrame, 
                    prices_df: pd.DataFrame, 
                    instant_execution: bool = False
                    ) -> Dict:
        '''
        - Assumptions: 
            - close_position_df represents desired position at END of every timestep t, prices are prices at END of every timestep t 
            - Assume we can execute x and y at the same time 
        
        - Args: 
            -instant_execution: bool = True 
                - Whether or not to assume instantantaneous execution, i.e. observe trading signal at end of period t, and then adjust position based on prices at end of period t 
        '''
        #Initialise 
        coins = close_position_df.columns.get_level_values(0).unique().to_list()
        position_df = pd.DataFrame({col: pd.Series(0.0, index = close_position_df.index) for col in coins})
        pnl_calculator = PnLCalculator(self.initial_capital, close_position_df.index)

        if not instant_execution: 
            #1 period lag: at end of period t-1 we have desired position that we can only execute based on period t prices 
            close_position_df = close_position_df.shift(1, fill_value = 0.0)
        
        # If our portfolio has been liquidated, we can no longer trade 
        for idx, t in enumerate(tqdm(close_position_df.index)):
            if self.is_liquidated: 
                break

            ##Rebalance portfolio 
            current_price_df, current_position_df = prices_df.loc[t], close_position_df.loc[t]
            current_position_df = self.constraints.check_capital_limit(current_position_df)
            position_df.loc[t] = current_position_df
            
            ##Cash flows 
            position_change_by_coin = (position_df.iloc[idx] - position_df.iloc[idx-1]) if idx > 0 else pd.Series(0.0, index = coins)
            cash_flow_by_coin = self._calc_cash_flow_by_coin(position_change_by_coin, current_price_df)

            # Costs 
            if (t.minute ==0 & t.second ==0):
                start_hour = t - pd.Timedelta(hours=1)
                #Calculat interest fees that occured in the previous hour 
                recent_position_df = position_df.loc[start_hour:t].iloc[:-1]
                recent_prices_df = prices_df.loc[start_hour:t].iloc[:-1]
                transaction_costs_by_type_coin = self.costs.calc_total_cost(position_change_by_coin, current_price_df, recent_position_df, recent_prices_df)
            else: 
                  transaction_costs_by_type_coin = self.costs.calc_total_cost(position_change_by_coin, current_price_df)
            #m2m
            m2m_by_coin= self._calc_m2m_by_coin(current_position_df, current_price_df)

            #4. Update PnL 
            pnl_calculator.update(t, cash_flow_by_coin, m2m_by_coin, transaction_costs_by_type_coin)
        
        pnl_calculator.summarise()

        return self._calc_results(pnl_calculator, position_df)