import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt 

class BollingerBandTradeStrategy:
    def __init__(self, entry_threshold, exit_threshold):
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
    
    def generate_trading_actions(self, z_score: pd.Series):
        """
        WHEN you trade 
        
        Returns: trades DataFrame
                 ['enter_long', 'enter_short', 'exit']
        """

        trades = pd.DataFrame(0, index=z_score.index, columns=['enter_long', 'enter_short', 'exit'])        
        position = 0 # 1 for long, -1 for short, 0 for neutral

        for i in range(len(z_score)):
            if position == 0:
                # Currently flat, look for entry/exit opportunities 
                if z_score.iloc[i] < -self.entry_threshold:
                    trades.at[trades.index[i], 'enter_long'] = 1
                    position = 1
                elif z_score.iloc[i] > self.entry_threshold:
                    trades.at[trades.index[i], 'enter_short'] = 1
                    position = -1

            elif position == 1 and z_score.iloc[i] > -self.exit_threshold:
                # Exit long position
                trades.at[trades.index[i], 'exit'] = 1
                position = 0

            elif position == -1 and z_score.iloc[i] < self.exit_threshold:
                # Exit short position
                trades.at[trades.index[i], 'exit'] = 1
                position = 0

        return trades
    
    def plot_trading_actions(self, z_score: pd.Series, trades: pd.DataFrame = None):
        """
        Plot z-score with trading actions overlaid
        
        Args:
            z_score: pd.Series of z-scores
            trades: optional pd.DataFrame with ['enter_long', 'enter_short', 'exit']
                    if None, will generate trades automatically
        """
    
        # Generate trades if not provided
        if trades is None:
            trades = self.generate_trading_actions(z_score)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Plot z-score line
        ax.plot(z_score, label='Z-Score', linewidth=2, color='blue', alpha=0.7)
        
        # Plot threshold lines
        ax.axhline(self.entry_threshold, color='red', linestyle='--', alpha=0.3, label='Entry threshold')
        ax.axhline(-self.entry_threshold, color='green', linestyle='--', alpha=0.3)
        ax.axhline(self.exit_threshold, color='orange', linestyle='--', alpha=0.3, label='Exit threshold')
        ax.axhline(-self.exit_threshold, color='orange', linestyle='--', alpha=0.3)
        ax.axhline(0, color='black', linestyle='-', alpha=0.2)
        
        # Plot trading actions
        enter_long_idx = trades[trades['enter_long'] == 1].index
        enter_short_idx = trades[trades['enter_short'] == 1].index
        exit_idx = trades[trades['exit'] == 1].index
        
        ax.scatter(enter_long_idx, z_score[enter_long_idx], 
                    color='green', s=150, marker='^', label='Enter Long', zorder=5, edgecolors='black')
        ax.scatter(enter_short_idx, z_score[enter_short_idx], 
                    color='red', s=150, marker='v', label='Enter Short', zorder=5, edgecolors='black')
        ax.scatter(exit_idx, z_score[exit_idx], 
                    color='black', s=150, marker='X', label='Exit', zorder=5)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Z-Score')
        ax.set_title('Trading Actions on Z-Score')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
    
    def calculate_desired_positions(self, actions: pd.DataFrame, beta: pd.Series) -> pd.DataFrame: 
        """
        How you trade: Convert trade actions into actual desired position sizes for each timestep 
        
        Long spread = Long Y (coef=1), Short X (coef=-beta)
        Short spread = Short Y (coef=-1), Long X (coef=+beta)
        
        Args:
            actions: DataFrame with ['enter_long', 'enter_short', 'exit']
            beta: Series of hedge ratios over time
            
        Returns: 
            DataFrame with ['position_y', 'position_x']
        """
        positions = pd.DataFrame(
            0.0, 
            index = actions.index, 
            columns = ['position_y', 'position_x']
        )
        
        #What is our CURRENT state? 
        current_direction = 0 #0=flat, 1= long-spread, -1 = short_sprad 

        for _, idx in enumerate(actions.index): 
            #Update position state at time t, based on actions
            if actions.loc[idx, 'enter_long']==1: 
                current_direction = 1
            if actions.loc[idx, 'enter_short']==1: 
                current_direction = -1
            elif actions.loc[idx, exit]==1: 
                current_direction = 0 

            if current_direction!=0: 
                beta_t = beta.loc[idx]
                #Long spread; + 1, -betaX
                positions.loc[idx, 'position_y'] = current_direction*1
                positions.loc[idx, 'position_x'] = current_direction*(-beta_t)
                #TODO - implement rounding/integer for the hedge ratio 
        return positions 
    
def generate_synthetic_zscore(n_periods=100, seed=42):
    '''Generate synthetic z score data that oscillates in a predictable pattern'''
    np.random.seed(seed)
    dates = pd.date_range('2024-01-01', periods=n_periods, freq='H')
    z_score = np.sin(np.linspace(0, 4*np.pi, n_periods)) * 2.5
    z_score += np.random.randn(n_periods) * 0.3
    return pd.Series(z_score, index=dates)

def plot_trading_actions(z_score, trades, entry_threshold=2.0, exit_threshold=0.5):
    """
    Plot z-score with trading actions overlaid
    
    Args:
        z_score: pd.Series of z-scores
        trades: pd.DataFrame with ['enter_long', 'enter_short', 'exit']
        entry_threshold: entry threshold level
        exit_threshold: exit threshold level
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot z-score line
    ax.plot(z_score, label='Z-Score', linewidth=2, color='blue', alpha=0.7)
    
    # Plot threshold lines
    ax.axhline(entry_threshold, color='red', linestyle='--', alpha=0.3, label='Entry threshold')
    ax.axhline(-entry_threshold, color='green', linestyle='--', alpha=0.3)
    ax.axhline(exit_threshold, color='orange', linestyle='--', alpha=0.3, label='Exit threshold')
    ax.axhline(-exit_threshold, color='orange', linestyle='--', alpha=0.3)
    ax.axhline(0, color='black', linestyle='-', alpha=0.2)
    
    # Plot trading actions
    enter_long_idx = trades[trades['enter_long'] == 1].index
    enter_short_idx = trades[trades['enter_short'] == 1].index
    exit_idx = trades[trades['exit'] == 1].index
    
    ax.scatter(enter_long_idx, z_score[enter_long_idx], 
               color='green', s=150, marker='^', label='Enter Long', zorder=5, edgecolors='black')
    ax.scatter(enter_short_idx, z_score[enter_short_idx], 
               color='red', s=150, marker='v', label='Enter Short', zorder=5, edgecolors='black')
    ax.scatter(exit_idx, z_score[exit_idx], 
               color='black', s=150, marker='X', label='Exit', zorder=5)
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Z-Score')
    ax.set_title('Trading Actions on Z-Score')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
