import numpy as np
import pandas as pd
import statsmodels.api as sm

class PricingSignal: 
    def __init__(self, hedge_lookback, spread_lookback):
        self.hedge_window = hedge_lookback 
        self.spread_window = spread_lookback 
    
    def _calculate_hedge_ratio(self, x, y): 
        #TODO - handle NaN's 
        '''Calculate dynamic hedge ratio'''
        betas = []

        for i in range(self.hedge_window, len(x)):
            # Get window of data
            x_window = x.iloc[i - self.hedge_window : i]
            y_window = y.iloc[i - self.hedge_window : i]
            
            # Add constant for intercept
            X = sm.add_constant(x_window)
            
            # Run OLS: y = alpha + beta * x
            model = sm.OLS(y_window, X).fit()
            beta = model.params[1]  # Get slope (not intercept)
            #TODO - what is the intercept for in pairs trading? 
            
            betas.append(beta)
        
        # Create series with proper index
        beta_series = pd.Series(
            betas, 
            index=x.index[self.hedge_window:]
        )
        
        # Reindex to match original data (fill early values with NaN)
        beta_series = beta_series.reindex(x.index)
        
        return beta_series
    
    def calculate_spread(self, x, y, beta): 
        '''Calculate spread based off dynamic hedge ratio'''
        spread = y - beta * x
        return spread
    
    def _calculate_zscore(self, spread): 
        mean = spread.rolling(self.spread_window).mean()
        std = spread.rolling(self.spread_window).std()
        return (spread - mean) / std
    
    def _generate(self, x, y):
        """
        Full pipeline: prices → signal
        """
        beta = self.calculate_hedge_ratio(x, y)
        spread = self.calculate_spread(x, y, beta)
        z_score = self.calculate_zscore(spread)
        
        return pd.DatFrame({
            'z_score': z_score,       # signal 
            'spread': spread,         # For analysis
            'beta': beta              # For position sizing
        })