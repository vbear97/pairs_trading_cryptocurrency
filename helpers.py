
SECONDS_TO_MINUTES = 60

import pandas as pd
import numpy as np
import statsmodels.api as sm 
from itertools import combinations

def fit_spread(y: pd.Series, x: pd.Series) -> pd.Series: 
    x_with_constant = sm.add_constant(x)
    results = sm.OLS(y, x_with_constant, missing='drop').fit()  # ← Add this
    b0, b1 = results.params 
    spread = (y - (b0 + b1*x))
    return spread

def rel_positions(spread: pd.Series) -> pd.Series:
    mu = spread.mean()
    conditions = [(spread > mu), (spread == mu), (spread < mu)]
    values = ['Above', 'Equal', 'Below']
    position_values = np.select(conditions, values)
    return pd.Series(position_values, index = spread.index)    

def zero_crossings(spread: pd.Series) -> pd.Series:
    '''Return vector of times between zero crossings from global mu'''
    mu = spread.mean()
    demeaned_spread = spread - mu 
    signs = pd.Series(np.sign(demeaned_spread), index = spread.index)
    #Filter to cases where we are either strictly ABOVE or strictly BELOW the mean 
    above_below = signs[signs!=0]
    crossings = above_below.diff().loc[lambda x: x!=0].dropna()
    interarrival_times = crossings.index.to_series().diff().dt.total_seconds() / SECONDS_TO_MINUTES
    #hanging - time from last crossing 
    last_crossing_time = crossings.index[-1]
    time_since_last_crossing = (spread.index[-1] - last_crossing_time).total_seconds()/SECONDS_TO_MINUTES
    return crossings, interarrival_times.dropna(), time_since_last_crossing

def quantile_crossing_time(spread: pd.Series, q = 0.5) -> pd.Series: 
    _, interarrival_times = zero_crossings(spread)
    if interarrival_times: 
        return np.quantile(interarrival_times, q = q)
    else: 
        return np.inf 
    

def ssd_distance(prices_df): 
    """
    Pre-screen pairs using Sum of Squared Differences on cumulative returns
    
    Parameters:
    -----------
    prices_df : DataFrame
        Price data with coins as columns, timestamps as index    
    Returns:
    --------
    DataFrame with pairs ranked by SSD distance
    """
    cumulative_returns = prices_df / prices_df.iloc[0]    
    results = []

    coins = list(prices_df.columns)
    pairs_list = list(combinations(coins, 2))
    
    for coin1, coin2 in pairs_list:
        # Get cumulative return series for both coins
        p_i = cumulative_returns[coin1]  # p_it starts at 1.0
        p_j = cumulative_returns[coin2]  # p_jt starts at 1.0
        
        # Calculate the spread: p_it - p_jt at each time point
        spread = p_i - p_j
        
        # Sum of Squared Differences
        ssd = (spread ** 2).sum()
        
        # Normalized by number of time periods (more interpretable)
        ssd_normalized = ssd / len(cumulative_returns)
        
        results.append({
            'coin1': coin1,
            'coin2': coin2,
            'distance': ssd_normalized,  # This is what we rank by
        })
    
    # Sort by distance (lower = more similar = better candidates)
    results_df = pd.DataFrame(results).sort_values('distance')
    results_df['rank_ssd'] = range(1, len(results_df) + 1)

    return results_df