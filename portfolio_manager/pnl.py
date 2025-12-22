from typing import Dict
import pandas as pd
import numpy as np 

class PnLCalculator:
    """Handles P&L calculations and tracking"""
    def __init__(self, initial_capital: float, index: pd.Index = None): 
        self.initial_capital = initial_capital
        self.index = index
        self.current_equity = None

        #Instantaneous/snapshot 
        self.state_df = pd.DataFrame({
            'cash_flow': pd.Series(0.0, index = self.index), 
            'position_value': pd.Series(0.0, index = self.index), 
            'cost_spot': pd.Series(0.0, index = self.index), 
            'cost_interest': pd.Series(0.0, index = self.index), 
            'cost': pd.Series(0.0, index = self.index), 
            'equity': pd.Series(0.0, index = self.index)
        })

        #cumulative
        self.cum_df= pd.DataFrame({
            'running_cash': pd.Series(0.0, index = self.index), 
        })

        self.summary_df = None

    def update(self, t: pd.Timestamp, cash_flow_by_coin: pd.Series, position_value_by_coin: pd.Series, cost_by_type_coin: Dict[str, pd.Series]): 
        self.state_df.loc[t, ['cash_flow', 'position_value', 'cost_spot', 'cost_interest']] = [
            cash_flow_by_coin.sum(), 
            position_value_by_coin.sum(), 
            cost_by_type_coin['spot'].sum(), 
            cost_by_type_coin['interest'].sum()
        ]
        #We need to update costs at every step to keep track of margins
        self.state_df.loc[t, 'cost'] = self.state_df.loc[t, ['cost_spot', 'cost_interest']].sum()

            # Calculate equity incrementally (ADD THIS)
        running_cost = self.state_df.loc[:t, 'cost'].sum()
        running_cash = self.state_df.loc[:t, 'cash_flow'].sum()
        current_equity = self.initial_capital + running_cash - running_cost + position_value_by_coin.sum()
        self.state_df.loc[t, 'equity'] = current_equity

    def summarise(self):
        self.cum_df['running_cost'] = self.state_df['cost'].cumsum()
        self.cum_df['running_cash_gross'] = self.state_df['cash_flow'].cumsum()
        self.cum_df['running_cash'] = self.cum_df['running_cash_gross'] - self.cum_df['running_cost']
        self.cum_df['equity_curve'] = self.state_df['equity']  
        self.summary_df = pd.concat([self.state_df, self.cum_df], axis=1)