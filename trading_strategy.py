import pandas as pd 
import numpy as pd 

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