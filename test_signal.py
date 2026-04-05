import pandas as pd 
import numpy as np 
import statsmodels.api as sm

def estimate_half_lives(pairs: list, prices_df: pd.DataFrame) -> pd.DataFrame:
    '''Take in prices and fit spread via OLS, then estimate half-life.
    Bar duration is inferred automatically from the index frequency.
    '''
    # infer bar duration in minutes from index
    bar_duration_mins = prices_df.index.to_series().diff().dropna().mode()[0].total_seconds() / 60
    
    results = []
    
    for (x, y) in pairs:
        spread = fit_spread(x=prices_df[x], y=prices_df[y])
        
        lag  = spread.shift(1).dropna()
        diff = spread.diff().dropna()
        lag  = lag.iloc[-len(diff):]
        diff = diff.iloc[-len(lag):]
        
        result = sm.OLS(diff, sm.add_constant(lag)).fit()
        
        beta   = result.params.iloc[1]
        pvalue = result.pvalues.iloc[1]
        phi1   = 1 + beta
        
        if beta < 0:
            half_life_bars = -np.log(2) / np.log(abs(phi1))
            half_life_mins = half_life_bars * bar_duration_mins
        else:
            half_life_bars = np.nan
            half_life_mins = np.nan
        
        results.append({
            'pair':            f"{x}/{y}",
            'beta':            round(beta, 6),
            'phi1':            round(phi1, 6),
            'p_value':         round(pvalue, 4),
            'mean_reverting':  beta < 0,
            'half_life_bars':  round(half_life_bars, 1) if not np.isnan(half_life_bars) else np.nan,
            'half_life_mins':  round(half_life_mins, 1) if not np.isnan(half_life_mins) else np.nan,
        })
    
    return pd.DataFrame(results).sort_values('half_life_mins')

def fit_spread(y: pd.Series, x: pd.Series) -> pd.Series: 
    '''Fit spread via OLS '''
    x_with_constant = sm.add_constant(x)
    results = sm.OLS(y, x_with_constant, missing='drop').fit()
    b0, b1 = results.params 
    spread = (y - (b0 + b1*x))
    return spread

def get_half_life(spread: pd.Series) -> float:
    """
    Estimate half-life of mean reversion via AR(1) approximation.
    
    Fits: Δspread_t = β * spread_{t-1} + ε_t
    Half-life = -log(2) / β
    """
    spread = spread.dropna()
    lag    = spread.shift(1).dropna()
    diff   = spread.diff().dropna()
    
    # align
    lag  = lag.iloc[-len(diff):]
    diff = diff.iloc[-len(lag):]
    
    lag_with_const = sm.add_constant(lag)
    result = sm.OLS(diff, lag_with_const).fit()
    
    beta     = result.params.iloc[1]
    half_life = -np.log(2) / beta
    
    return half_life
