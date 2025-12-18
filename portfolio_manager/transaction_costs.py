import pandas as pd 

class CostCalculator:
    """Handles cost calculations per trade"""
    
    def __init__(self, transaction_cost_rate: float):
        self.transaction_cost_rate = transaction_cost_rate
    
    def calculate_trade_cost(self, 
                            position_change: float, 
                            current_price: float) -> float:
        """Calculate cost for one leg"""
        #TODO - Can make more complex one we incorporate other costs 
        current_price = current_price['ask'] if position_change > 0 else current_price['bid']
        trade_value = abs(position_change * current_price)
        return trade_value * self.transaction_cost_rate
    
    def calculate_total_cost(self,
                            position_change_y: float, 
                            position_change_x: float,
                            current_price_y: pd.Series, 
                            current_price_x: pd.Series) -> float:
        """Calculate cost for both legs"""
        if position_change_y == 0 and position_change_x == 0:
            return 0.0
        cost_y = self.calculate_trade_cost(position_change_y, current_price_y)
        cost_x = self.calculate_trade_cost(position_change_x, current_price_x)
        return cost_y + cost_x

class DummyCostCalculator:
    """Zero-cost calculator for idealized backtesting"""
    def __init__(self, *args, **kwargs):
        pass
    
    def calculate_trade_cost(self):
        return 0.0
    
    def calculate_total_cost(self):
        return 0.0