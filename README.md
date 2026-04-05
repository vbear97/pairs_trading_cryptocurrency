# Pairs Trading - Statistical Arbitrage Strategies (Top Level Cryptocurrency Order Book Data)

This repo investigates whether pairs trading/statistical arbitrage strategies exist for cryptocurrency assets at a high (10s) and mid (1 minute) frequency. We focus on: 

1. Applying and interpreting different statistical methods for selecting candidate pairs 
2. Backtesting a dynamic OLS strategy with real world constraints, in particular short-selling fees. 

## Key Results (WiP) - Summary
- Historical price series display statistically significant findings of cointegration, but empirical methods of estimating degree of mean reversion (e.g. Half Life, Hurst Exponent) suggests that pairs trading cryptocurrencies will not be profitibable 
  - Moreover, there is no evidence that historicaly cointegrated price series might **persist** into the future 
    - External Evidence: Lack of economic reasoning as to why price series co-move 
    - In data evidence: Comovements are inconsistent across time frequencies, suggesting no fundamental relationship 
      - This is in contrast to BTC/W-BTC 
- Backtesting a rolling hedging strategy (rolling OLS, Kalman filters) for a crypto-pair shows that even if the signal is not totally noise-fit, the short-selling fees nukes our profit 
  - See WiP folder 
