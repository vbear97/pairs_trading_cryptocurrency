import pandas as pd
import numpy as np 

class PnLCalculator:
    """Handles P&L calculations and tracking"""
    def __init__(self, initial_capital: float): 
        self.initial_capital = initial_capital
        self.equity = initial_capital  #Current net worth in the account = Initial Capital 

        #Instantaneous/snapshot 
        self.cash_flow_series = []
        self.position_value_series = []
        self.cost_series = []

        #state 
        self.cash_holdings = None
        self.equity_curve = None 

    def update(self, cash_flow_t: float, position_value_t: float, cost_t: float): 
        # Record time series 
        self.position_value_series.append(position_value_t)
        self.cash_flow_series.append(cash_flow_t)
        self.cost_series.append(cost_t) 

    def summarise(self):
        #reformat 
        self.cash_flow_series = np.array(self.cash_flow_series)
        self.position_value_series = np.array(self.position_value_series)
        self.costs = np.array(self.cost_series)

        #calculate other 
        self.cash_holdings = np.cumsum(self.cash_flow_series) - np.cumsum(self.cost_series)
        self.equity_curve = self.initial_capital + self.cash_holdings + self.position_value_series
        self.equity = self.equity_curve[-1]