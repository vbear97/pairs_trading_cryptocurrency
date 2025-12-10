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
        intercept = []

        for i in range(self.hedge_window, len(x)):
            # Get window of data
            x_window = x.iloc[i - self.hedge_window : i]
            y_window = y.iloc[i - self.hedge_window : i]
            
            # Add constant for intercept
            X = sm.add_constant(x_window)
            
            # Run OLS: y = alpha + beta * x
            model = sm.OLS(y_window, X).fit()
            params = list(model.params)
            intercept.append(params[0])
            betas.append(params[1])
            #TODO - what is the intercept for in pairs trading? 
        
        # Create series with proper index
        beta_series = pd.Series(
            betas, 
            index=x.index[self.hedge_window:]
        )
        intercept_series = pd.Series(
            intercept, 
            index=x.index[self.hedge_window:]
        )
        
        # Reindex to match original data (fill early values with NaN)
        beta_series = beta_series.reindex(x.index)
        intercept_series = intercept_series.reindex(x.index)
        
        return intercept_series, beta_series
    
    def _calculate_spread(self, x, y, intercept, beta): 
        '''Calculate spread based off dynamic hedge ratio'''
        spread = y - intercept - (beta * x)
        return spread
    
    def _calculate_zscore(self, spread): 
        mean = spread.rolling(self.spread_window).mean()
        std = spread.rolling(self.spread_window).std()
        return (spread - mean) / std
    
    def _generate(self, x, y):
        """
        Full pipeline: prices → signal
        """
        intercept, beta = self._calculate_hedge_ratio(x, y)
        spread = self._calculate_spread(x, y, intercept, beta)
        z_score = self._calculate_zscore(spread)
        
        return pd.DataFrame({
            'z_score': z_score,       # signal 
            'spread': spread,         # For analysis
            'beta': beta              # For position sizing
        })
    
def generate_pricing_signal_test_data(n_periods=200, 
                                      freq='H', 
                                      start_date='2024-01-01',
                                      n_regimes=4,
                                      regime_betas=None,
                                      noise_std=2.0,
                                      x_start=50,
                                      seed=42):
    np.random.seed(seed)
    
    # Generate dates
    dates = pd.date_range(start_date, periods=n_periods, freq=freq)
    
    # Base X series (random walk)
    x = pd.Series(np.cumsum(np.random.randn(n_periods)) + x_start, index=dates)
    
    # Y with changing slopes
    periods_per_regime = n_periods // n_regimes
    y_values = []
    
    for regime_idx, beta in enumerate(regime_betas):
        start = regime_idx * periods_per_regime
        end = start + periods_per_regime if regime_idx < n_regimes - 1 else n_periods
        
        # y = beta * x + noise for this regime
        regime_y = beta * x.iloc[start:end] + np.random.randn(end - start) * noise_std
        y_values.extend(regime_y.values)
    
    y = pd.Series(y_values, index=dates)
    
    # Regime boundaries
    regime_boundaries = [i * periods_per_regime for i in range(1, n_regimes)]
    
    return {
        'x': x,
        'y': y,
        'true_betas': regime_betas,
        'regime_boundaries': regime_boundaries,
        'dates': dates
    }