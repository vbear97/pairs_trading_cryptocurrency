from typing import Tuple
import numpy as np 
import pandas as pd

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