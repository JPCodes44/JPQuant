"""
Backtesting a Flag Pattern Breakout strategy, 
which identifies a flag pattern with a strong price movement 
followed by a consolidation period. The strategy trades in the 
direction of the breakout. Key parameters include lookback period, 
flag pattern duration, entry/exit rules, and risk management 
(stop loss/take profit). The backtest evaluates performance 
over historical data, providing metrics like total return, 
win rate, and maximum drawdown.
"""

# get data on the 15m timeframe

from backtesting import Backtest
from datetime import datetime
import warnings
import pandas as pd
from strats_26 import *
from dataset import get_candles_since_date


def run_backtest(stratName, symbol, timeframe, start_time, plot=True, save_data=True):

    # data = pd.read_csv('feb23/BTC-USD-15m_filled.csv', index_col='datetime', parse_dates=True)
    data = get_candles_since_date(symbol)
