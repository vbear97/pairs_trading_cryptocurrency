from typing import Literal
def summary_streaks_seconds(series, seconds_per_row = 10, stat: Literal['longest_location', 'describe'] = 'describe'):
    # Create groups of consecutive NaNs
    isnan = series.isna()
    flipped = ~isnan
    streak_counts = flipped.cumsum() #if we are detecting strings of consecutive trues, then flipping it and then doing a cum sum means that the now consecutive falses generate streak of all the same number 
    streak_groups = streak_counts[isnan]
    streak_counts = streak_groups.value_counts() #in terms of number of rows 
    if stat == 'describe': 
        summary = streak_counts.describe(percentiles=[0.25, 0.75, .90, .95, 0.99])
        return summary*seconds_per_row
    elif stat == 'longest_location':
        # Find the longest streak
        longest_streak_id = streak_counts.idxmax()
        # Find where this streak starts (first occurrence of this streak_id)
        longest_streak_indices = streak_groups[streak_groups == longest_streak_id].index
        return longest_streak_indices[0], longest_streak_indices[-1]