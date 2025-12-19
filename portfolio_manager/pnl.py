from typing import Dict
import pandas as pd
import numpy as np 

class PnLCalculator:
    """Handles P&L calculations and tracking"""
    def __init__(self, initial_capital: float, index: pd.Index = None): 
        self.initial_capital = initial_capital
        self.index = index

        #Instantaneous/snapshot 
        self.state_df = pd.DataFrame({
            'cash_flow': pd.Series(0.0, index = self.index), 
            'position_value': pd.Series(0.0, index = self.index), 
            'cost_spot': pd.Series(0.0, index = self.index), 
            'cost_interest': pd.Series(0.0, index = self.index), 
            'cost': pd.Series(0.0, index = self.index), 
        })

        #cumulative
        self.cum_df= pd.DataFrame({
            'running_cash': pd.Series(0.0, index = self.index), 
            'equity_curve': pd.Series(0.0, index = self.index),
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

    def summarise(self):
        #Update 
        self.cum_df['running_cost'] = self.state_df['cost'].cumsum()
        self.cum_df['running_cash_gross'] =  self.state_df['cash_flow'].cumsum()
        self.cum_df['running_cash'] = self.cum_df['running_cash_gross'] - self.cum_df['running_cost']
        self.cum_df['equity_curve'] = self.initial_capital + self.cum_df['running_cash'] + self.state_df['position_value']   
        self.summary_df = pd.concat([self.state_df, self.cum_df], axis = 1)