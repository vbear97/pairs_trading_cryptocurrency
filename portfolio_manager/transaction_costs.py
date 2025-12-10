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