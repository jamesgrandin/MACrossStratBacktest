# MACrossStratBacktest
This program back tests a moving average cross over strategy

Assumption: A cross over of a short term moving average above a longer term moving average indicates an change in momentum to the upside. 
This cross over can provide an early warning sign that the trend direction has shifted from downward to upward. If this is true, a profitable trading
signal can be generated when this the corssover event occurs.

This algorithm is applied to the 5-minute time frame (OHLC bars) and signals a BUY condition when the 10 expoential moving average (EMA) crosses over the 50 
simple moving average (SMA) and a SELL condition when it crosses back below. This only occurs if the 10 EMA is currently trading above to 200 SMA, to try to 
filter out trade signals when the market is showing signs of weakness. The system also triggers a BUY when the 10 EMA crosses above the 200 SMA, signifying a 
change in momentum to the upside, and generates a SELL signal when the 10EMA crosses back below either the 50 SMA or the 200 SMA, whichever comes first.

Price Data Class: This pulls that pricing data over a specified date time range with a specified resolution for a specified ticker and converts it to a 
pandas dataframe for manipulation. This data can be used in multiple strategies.

MACrossStrat Class: This class inherents the attributes of the price data class. It produces trade signals based on moving average cross over conditions.

PortfolioValue Class: This class enters postions based on price signals and simulates the portfolio value over the life of the position.
