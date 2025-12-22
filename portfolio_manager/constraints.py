from collections import defaultdict
from typing import Tuple
import numpy as np 
import pandas as pd

class ConstraintChecker: 
    """Handle constraint enforcement"""
    def __init__(self, 
                    max_leverage: float, 
                    margin_threshold: float, 
                    min_order_value_usdt_by_coin, 
                    min_position_tick_size_by_coin):
        self.max_leverage = max_leverage
        self.margin_threshold = margin_threshold
        self.min_order_value_usdt_by_coin = min_order_value_usdt_by_coin
        self.tick_size_by_coin = min_position_tick_size_by_coin

    def _round_and_filter_position_changes(self, position_change: pd.Series, prices_df: pd.Series) -> pd.Series:
        """Round to tick sizes and zero out positions below minimum"""
        #Step 1: Round to tick sizes, then zero out positions below minimum
        rounded_position_change = pd.Series({
            coin: (pos/self.tick_size_by_coin[coin]).round()*self.tick_size_by_coin[coin] for coin, pos in desired_position.items()
        })
        #Step 2: Calculate position value in USDT 
        #TODO - take away this midprice logic that was added in for brevity 
        mid_prices = prices_df[['bid', 'ask']].mean(axis=1)
        position_values = rounded_position_change.abs()*mid_prices

        # Step 3: Zero out positions below minimum
        min_values = pd.Series(self.min_order_value_usdt_by_coin).loc[position.index]
        rounded_position_change = rounded_position_change.where(position_values >= min_values, 0)

        return rounded_position_change

    def _check_leverage(self, desired_position_by_coin: pd.Series, prices_df: pd.DataFrame, current_equity: float) -> pd.Series: 
        '''Scale down position size depending on leverage'''
        # Calculate mid prices
        # TODO - take away midprices, added in for brevity 
        mid_prices = prices_df[['bid', 'ask']].mean(axis=1)
        # Calculate total position value
        total_position_value = (desired_position_by_coin.abs() * mid_prices).sum()
        
        max_allowed = current_equity * self.max_leverage
        if total_position_value > max_allowed:
            scale = max_allowed / total_position_value
            desired_position_by_coin = desired_position_by_coin * scale
        
        return desired_position_by_coin      
        
    def check_capital_limit(self, 
                            prev_position_by_coin: pd.Series, 
                            desired_position_by_coin: pd.Series, 
                            prices_df: pd.DataFrame, 
                            current_equity: float) -> pd.Series:
        '''
        Apply all position constraints: 
        1. Round to tick sizes 
        2. Enforce minimum sizes 
        3. Enforce leverage limits 
        '''
        #1. Check leverage on desired position 
        adjusted_position = self._check_leverage(desired_position_by_coin, prices_df, current_equity)
        #2. Calculate change 
        position_change = adjusted_position - prev_position 
        #3. Round and filter change 
        rounded_position_change = self._round_and_filter_position_changes(position_change, prices_df)
        return rounded_position_change
        
    def check_margin_call(self, equity: float, initial_capital: float) -> bool: 
        '''
        Rule: Liquidate all positions when equity/initial_capital drops below threshold.
        '''
        liquidation_level = initial_capital * self.margin_threshold
        return equity < liquidation_level 

class DummyConstraintChecker:
    """Pass-through constraint checker for idealized backtesting"""
    def __init__(self, *args, **kwargs):
        pass

    def check_capital_limit(self, positions: pd.Series):
        """Return desired positions unchanged"""
        return positions

    def check_margin_call(self, equity, initial_capital):
        """Never trigger margin calls"""
        return False