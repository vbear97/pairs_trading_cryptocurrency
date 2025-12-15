import pandas as pd 
class BuyHoldStrategy:
    def __init__(self):
        pass 
    def _calculate_desired_positions(self, num_units: int, index = None): 
        '''Buy num_units and hold'''
        if index is not None:
            return pd.Series(num_units, index = index)
        else: 
            return pd.Series(num_units)
        
        