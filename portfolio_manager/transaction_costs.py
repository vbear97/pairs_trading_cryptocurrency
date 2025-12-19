import pandas as pd 
from typing import Dict, Optional
from .constants import DEFAULT_HOURLY_INTEREST_RATE

class CostCalculator:
    """Handles cost calculations per trade"""
    
    def __init__(self, transaction_cost_rate: float, hourly_interest_rate_by_coin: Dict[str, float]):
        self.transaction_cost_rate = transaction_cost_rate
        self.hourly_interest_rate_by_coin = hourly_interest_rate_by_coin

    def _calc_interest(self, position_history_df: Optional[pd.DataFrame], 
                      prices_df: Optional[pd.DataFrame]) -> Dict[str, float]: 
        '''Calculate upper bound interest rate'''
        if len(position_history_df) and len(prices_df):
            return {
                    coin: position_history_df[coin][position_history_df[coin] < 0].abs().max() * 
                        prices_df[coin].values.max() * #Get maximum of bid, ask price  for that coin for the hour
                        self.hourly_interest_rate_by_coin.get(coin, DEFAULT_HOURLY_INTEREST_RATE)
                    for coin in position_history_df.columns
            }
        else: 
            return {}

    def _calc_spot_fees(self, position_change: pd.Series, 
                       current_price: pd.DataFrame) -> Dict[str, float]:
        return {
            #buy long = ask 
            coin: abs(delta * current_price[coin]['ask' if delta > 0 else 'bid']) 
                  * self.transaction_cost_rate
            for coin, delta in position_change.items()
        }
    
    def calc_total_cost(self, position_change: pd.Series, current_price: pd.Series, 
                       position_history_df = pd.DataFrame(), 
                       price_history_df = pd.DataFrame()) -> Dict[str, pd.Series]: 
        return {
            'spot': pd.Series(self._calc_spot_fees(position_change, current_price)),
            'interest': pd.Series(self._calc_interest(position_history_df, price_history_df))
        }