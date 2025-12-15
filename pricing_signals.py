import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS

class PricingSignal: 
    def __init__(self, hedge_lookback, spread_lookback):
        self.hedge_window = hedge_lookback 
        self.spread_window = spread_lookback 
    
    def _calculate_hedge_ratio(self, x, y, fit_intercept=True): 
        if fit_intercept:
            X = sm.add_constant(x)
            exog_idx = 1  # Beta is second column
            const_idx = 0
        else:
            X = x.to_frame() if isinstance(x, pd.Series) else x
            exog_idx = 0
            const_idx = None
    
        # Fit rolling OLS
        model = RollingOLS(y, X, window=self.hedge_window)
        rolling_res = model.fit()
    
        # Extract parameters
        betas = rolling_res.params.iloc[:, exog_idx]
    
        if fit_intercept:
            intercepts = rolling_res.params.iloc[:, const_idx]
        else:
            intercepts = pd.Series(0.0, index=betas.index)
    
        return intercepts, betas
    
    def _calculate_spread(self, x, y, intercept, beta): 
        '''Calculate spread based off dynamic hedge ratio'''
        spread = y - intercept - (beta * x)
        return spread
    
    def _calculate_zscore(self, spread): 
        mean = spread.rolling(self.spread_window).mean()
        std = spread.rolling(self.spread_window).std()
        return (spread - mean) / std
    #TODO - remove _
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
                                      intercept: float = 1.0, 
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
        
        # y = intercept + beta * x + noise for this regime
        regime_y = intercept + (beta * x.iloc[start:end]) + np.random.randn(end - start) * noise_std
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