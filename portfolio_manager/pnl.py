import pandas as pd
class PnLCalculator:
    def __init__(self, initial_capital: float, index: pd.Index = None): 
        self.initial_capital = initial_capital
        self.index = index
        
        # Use LISTS instead of DataFrames
        self.cash_flow_list = []
        self.position_value_list = []
        self.cost_spot_list = []
        self.cost_interest_list = []
        self.equity_list = []
        
        self._running_cost = 0.0  
        self._running_cash = 0.0  

    def update(self, t, cash_flow_by_coin, position_value_by_coin, cost_by_type_coin): 
        cash_flow = cash_flow_by_coin.sum()
        position_value = position_value_by_coin.sum()
        cost_spot = cost_by_type_coin['spot'].sum()
        cost_interest = cost_by_type_coin['interest'].sum()
        
        # Append to lists (fast)
        self.cash_flow_list.append(cash_flow)
        self.position_value_list.append(position_value)
        self.cost_spot_list.append(cost_spot)
        self.cost_interest_list.append(cost_interest)
        
        # Update running totals
        cost_t = cost_spot + cost_interest
        self._running_cost += cost_t
        self._running_cash += cash_flow
        
        current_equity = self.initial_capital + self._running_cash - self._running_cost + position_value
        self.equity_list.append(current_equity)
        
        return current_equity  

    def summarise(self):
        # Convert lists to DataFrames once at end
        self.state_df = pd.DataFrame({
            'cash_flow': self.cash_flow_list,
            'position_value': self.position_value_list,
            'cost_spot': self.cost_spot_list,
            'cost_interest': self.cost_interest_list,
            'equity': self.equity_list
        }, index=self.index[:len(self.equity_list)])
        
        self.state_df['cost'] = self.state_df['cost_spot'] + self.state_df['cost_interest']
        
        self.cum_df = pd.DataFrame({
            'running_cost': self.state_df['cost'].cumsum(),
            'running_cash_gross': self.state_df['cash_flow'].cumsum(),
        }, index=self.state_df.index)
        
        self.cum_df['running_cash'] = self.cum_df['running_cash_gross'] - self.cum_df['running_cost']
        self.cum_df['equity_curve'] = self.state_df['equity']
        
        self.summary_df = pd.concat([self.state_df, self.cum_df], axis=1)