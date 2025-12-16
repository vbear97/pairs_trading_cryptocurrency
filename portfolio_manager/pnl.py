import pandas as pd
import numpy as np 

class PnLCalculator:
    """Handles P&L calculations and tracking"""
    def __init__(self, initial_capital: float): 
        self.initial_capital = initial_capital
        self.equity = initial_capital #Current net worth in the account = Initial Capital 

        #Instantaneous/snapshot 
        self.cash_flow_series = []
        self.position_value_series = []
        self.cost_series = []

        #state 
        self.cash_holdings = None
        self.portfolio_value = None
        self.pnl_series = None 


    def update(self, cash_flow_t: float, position_value_t: float, cost_t: float): 
        # Record time series 
        self.position_value_series.append(position_value_t)
        self.cash_flow_series.append(cash_flow_t)
        self.cost_series.append(cost_t) 

    def summarise(self):
        cash_flows = np.array(self.cash_flow_series)
        costs = np.array(self.cost_series)
        position_values = np.array(self.position_value_series)
    
        cumulative_cash = np.cumsum(cash_flows) - np.cumsum(costs)
        equity_curve = self.initial_capital + cumulative_cash + position_values
    
        self.equity_curve = np.concatenate([[self.initial_capital], equity_curve])
        self.pnl_series = np.diff(self.equity_curve)
        self.equity = self.equity_curve[-1]