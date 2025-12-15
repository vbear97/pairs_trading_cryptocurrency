import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt 

class BollingerBandTradeStrategy:
    def __init__(self, entry_threshold, exit_threshold):
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

    def get_positions(self, z_score: pd.Series, beta: pd.Series) -> pd.Series: 
        '''Main function: convert z_score pricing signals into atual positions'''
        actions = self._generate_trading_actions(z_score)
        positions = self._calculate_desired_positions(beta = beta, actions = actions)
        return positions 
    
    def _generate_trading_actions(self, z_score: pd.Series):
        """
        WHEN you trade 
        
        Returns: trades DataFrame
                 ['enter_long', 'enter_short', 'exit']
        """

        trades = pd.DataFrame(0, index=z_score.index, columns=['enter_long', 'enter_short', 'exit'])        
        position = 0 # 1 for long, -1 for short, 0 for neutral

        for i in range(len(z_score)):
            if pd.isna(z_score.iloc[i]):
                continue  # Skip this iteration, maintain current position

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
    
    def _calculate_desired_positions(self, beta: pd.Series, actions: pd.DataFrame) -> pd.DataFrame: 
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
            elif actions.loc[idx, 'exit']==1: 
                current_direction = 0 

            if current_direction!=0: 
                beta_t = beta.loc[idx]
                #Long spread; + 1, -betaX
                positions.loc[idx, 'position_y'] = current_direction*1
                positions.loc[idx, 'position_x'] = current_direction*(-beta_t)
                #TODO - implement rounding/integer for the hedge ratio 
        return positions 
    
    def plot_positions(self, beta: pd.Series, z_score: pd.Series, actions: pd.DataFrame = None, positions: pd.DataFrame = None):
        """
        Plot positions over time with z_score and actions for debugging
        
        Args:
            beta: Series of hedge ratios
            z_score: optional pd.Series of z-scores
            actions: optional pd.DataFrame with trades
            positions: optional pd.DataFrame with positions (if None, will calculate)
        """
        
        # Generate actions if needed
        if actions is None:
            actions = self._generate_trading_actions(z_score)
        
        # Generate positions if needed
        if positions is None:
            positions = self._calculate_desired_positions(beta, actions)
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        
        # Plot 1: Z-score with trade signals
        axes[0].plot(z_score, label='Z-Score', color='blue', linewidth=2)
        axes[0].axhline(self.entry_threshold, color='r', linestyle='--', alpha=0.3)
        axes[0].axhline(-self.entry_threshold, color='r', linestyle='--', alpha=0.3)
        axes[0].axhline(self.exit_threshold, color='g', linestyle='--', alpha=0.3)
        axes[0].axhline(-self.exit_threshold, color='g', linestyle='--', alpha=0.3)

        axes[0].axhline(0, color='black', linestyle='-', alpha=0.2)
        
        # Mark trades
        enter_long = actions[actions['enter_long'] == 1].index
        enter_short = actions[actions['enter_short'] == 1].index
        exits = actions[actions['exit'] == 1].index
        
        axes[0].scatter(enter_long, z_score[enter_long], 
                    color='green', s=100, marker='^', label='Enter Long', zorder=5)
        axes[0].scatter(enter_short, z_score[enter_short], 
                    color='red', s=100, marker='v', label='Enter Short', zorder=5)
        axes[0].scatter(exits, z_score[exits], 
                    color='black', s=100, marker='X', label='Exit', zorder=5)
    
        axes[0].set_ylabel('Z-Score')
        axes[0].set_title('Z-Score and Trade Signals')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Position in Y
        axes[1].plot(positions['position_y'], label='Position Y', color='purple', linewidth=2)
        axes[1].axhline(0, color='black', linestyle='-', alpha=0.3)
        axes[1].fill_between(positions.index, 0, positions['position_y'], 
                            where=(positions['position_y'] > 0), alpha=0.3, color='green', label='Long Y')
        axes[1].fill_between(positions.index, 0, positions['position_y'], 
                            where=(positions['position_y'] < 0), alpha=0.3, color='red', label='Short Y')
        axes[1].set_ylabel('Position Y')
        axes[1].set_title('Position in Asset Y')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Position in X
        axes[2].plot(positions['position_x'], label='Position X', color='orange', linewidth=2)
        axes[2].axhline(0, color='black', linestyle='-', alpha=0.3)
        axes[2].fill_between(positions.index, 0, positions['position_x'], 
                            where=(positions['position_x'] > 0), alpha=0.3, color='green', label='Long X')
        axes[2].fill_between(positions.index, 0, positions['position_x'], 
                            where=(positions['position_x'] < 0), alpha=0.3, color='red', label='Short X')
        axes[2].set_ylabel('Position X')
        axes[2].set_xlabel('Time')
        axes[2].set_title('Position in Asset X (Hedge)')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        fig.tight_layout()

def generate_synthetic_zscore(n_periods=100, seed=42):
    '''Generate synthetic z score data that oscillates in a predictable pattern'''
    np.random.seed(seed)
    dates = pd.date_range('2024-01-01', periods=n_periods, freq='H')
    z_score = np.sin(np.linspace(0, 4*np.pi, n_periods)) * 2.5
    z_score += np.random.randn(n_periods) * 0.3
    return pd.Series(z_score, index=dates)