import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries

api_key = "5C0UONZ0TJ3FKCHZ"


class PriceData:
    #needs, Ticker symbol, Date/Time Range(startdatetime and enddatetime), and resolution (time interval for price (1min, 5min etc))
    #gets price of ticker in pandas dataframe over specificed time frame
    def __init__(self, api_key, ticker, startdatetime, enddatetime, resolution):
        self.api_key = api_key
        self.ticker = ticker
        self.startdatetime = startdatetime
        self.enddatetime = enddatetime
        self.resolution = resolution

    def get_intraday_data(self):
        ts = TimeSeries(key=api_key, output_format='pandas')  # getting time series data

        data, metadata = ts.get_intraday(symbol=ticker, interval=resolution, outputsize="full")  #stores open,high,low,close and volume of ticker at for chosen resolution
        df = data[::-1] #for some reason the timeseries dataframe is given in reverse, this gets it in the proper format
        self.price_df = df[startdatetime:enddatetime]

        return self.price_df


class MACrossStrat(PriceData):

    def __init__(self, api_key, ticker, startdatetime, enddatetime, resolution, longSMA, shortSMA, EMA):
        self.longSMA = longSMA #choose longterm moving average period
        self.shortSMA= shortSMA #choose shortterm moving average period
        self.EMA = EMA #choose EMA period
        PriceData.__init__(self, api_key, ticker, startdatetime, enddatetime, resolution)

    def get_MAs(self):
        ti = TechIndicators(key=api_key, output_format='pandas')  # getting technical indicator and setting output to pandas dataframe

        #will be using 200SMA, 50SMA, and 10EMA for buy and sell signals
        #gets moving averages in pandas dataframe

        longSMAdata, longSMAmetadata = ti.get_sma(symbol=ticker, interval=resolution, time_period=self.longSMA)
        longSMAdatasubset = longSMAdata[startdatetime:enddatetime]

        shortSMAdata, longSMAmetadata = ti.get_sma(symbol=ticker, interval=resolution, time_period=self.shortSMA)
        shortSMAdatasubset = shortSMAdata[startdatetime:enddatetime]

        EMAdata, EMAmetadata = ti.get_ema(symbol=ticker, interval=resolution,time_period=self.EMA)
        EMAdatasubset = EMAdata[startdatetime:enddatetime]

        self.moving_average_df = pd.concat([longSMAdatasubset, shortSMAdatasubset, EMAdatasubset], axis=1)
        self.moving_average_df.columns = ["longSMA", "shortSMA", "EMA"]

        return self.moving_average_df

    def get_signals(self):
        self.signals = pd.DataFrame(index=self.moving_average_df.index)  # initializing signals dataframe

        #create buy and sell signals based off of moving average crossover.
        #generates BUY signal when 10 EMA crosses 50SMA while above 200 SMA, SELL when crossing back below 50SMA
        #Also generates BUY signal when 10 EMA crosses above 200 SMA, signifying the stock currently has strong momentum, SELL if 10EMA crosss below 200SMA or 50SMA

        self.signals["signals"] = np.where((self.moving_average_df['EMA'][::] > self.moving_average_df['shortSMA']) & (self.moving_average_df['longSMA'][::] < self.moving_average_df['EMA'][::]), 1.0,0.0)

        ##BUY and SELL signal dataframe column (1=BUY, -1=SELL, 0=Do nothing)

        self.signals['positions'] = self.signals['signals'].diff().fillna(0.0)

        return self.signals


class PortfolioValue:

    def __init__(self,shares,initial_capital, price_df, signals):
        self.price_df = price_df
        self.signals = signals
        self.shares = shares #choose how many shares you want to buy and sell at each signal
        self.initial_capital = initial_capital #choose starting capital for portfolio

    def positions(self):
        #generates dataframe of shares currently being held in portfolio

        self.positions = pd.DataFrame(index=self.price_df.index).fillna(0.0)

        self.positions[ticker] = self.shares * self.signals['signals'].fillna(0.0)

        self.pos_diff = self.positions.diff().fillna(0.0)

        return self.positions, self.pos_diff

    def portfolio(self):
        #initializing portfolio dataframe
        self.portfolio = self.positions.multiply(self.price_df['4. close'], axis=0)

        # Value of currently held position
        self.portfolio['holdings'] = (self.positions.multiply(self.price_df['4. close'], axis=0)).sum(axis=1)

        # Current cash available for trading
        self.portfolio['cash'] = self.initial_capital - (self.pos_diff.multiply(self.price_df['4. close'], axis=0)).sum(
            axis=1).cumsum()

        # total value of liquid assets held in portfolio
        self.portfolio['net_liquid'] = self.portfolio['cash'] + self.portfolio['holdings']

        # rolling percent change of total portfolio value
        self.portfolio['percent_change'] = self.portfolio['net_liquid'].pct_change()

        return self.portfolio


"""Initialize data here"""
ticker = 'MSFT' #change ticker symbol here
resolution = '5min' #allowable intervals include 1min, 5minute, 15min, 30min, and 60min.
startdatetime = "2021-03-29 09:30:00" ## choose timeframe within last 2 months
enddatetime = "2021-04-04 16:00:00"


#creating new MACrossStrat Object
pricedata=MACrossStrat(api_key, ticker, startdatetime, enddatetime, resolution, longSMA = 200, shortSMA = 50, EMA = 10)

pricedata.get_intraday_data()
pricedata.get_MAs()
pricedata.get_signals()

#Creating new PortfolioValue object
portfoliodata = PortfolioValue(100, 100000.0, pricedata.price_df, pricedata.signals)

portfoliodata.positions()
portfoliodata.portfolio()

#creating Price and Moving Average plot with buy/sell signals
fig = plt.figure(1)
fig.patch.set_facecolor('white')
ax1 = fig.add_subplot(111, ylabel = 'Price in $', title=ticker)
pricedata.price_df['4. close'].plot(ax=ax1, color='k', lw=0.6, label='Price')
pricedata.moving_average_df['longSMA'].plot(ax=ax1, color='g', lw=0.4, label="longSMA")
pricedata.moving_average_df['shortSMA'].plot(ax=ax1, color='m', lw=0.4, label='shortSMA')
pricedata.moving_average_df['EMA'].plot(ax=ax1, color='c', lw=0.4, label='EMA')
#overlay buy/sell signals on price plot
ax1.legend()
ax1.plot(pricedata.signals.loc[pricedata.signals['positions'] == 1.0].index, pricedata.price_df["4. close"][pricedata.signals['positions'] == 1.0], '^', markersize=5, color='g')
ax1.plot(pricedata.signals.loc[pricedata.signals['positions'] == -1.0].index, pricedata.price_df["4. close"][pricedata.signals['positions'] == -1.0], 'v', markersize=5, color='r')


#creating total portfolio value plot with buy/sell signals notated
fig2=plt.figure(2)
ax2 = fig2.add_subplot(111, ylabel = "Net Liquid", title ="Total Portfolio Value")
portfoliodata.portfolio['net_liquid'].plot(ax=ax2, lw=0.6)
#overlay buy/sell signals on equity curve
ax2.plot(portfoliodata.portfolio.loc[pricedata.signals.positions == 1.0].index, portfoliodata.portfolio.net_liquid[pricedata.signals.positions == 1.0], '^', markersize=5, color='g')
ax2.plot(portfoliodata.portfolio.loc[pricedata.signals.positions == -1.0].index, portfoliodata.portfolio.net_liquid[pricedata.signals.positions == -1.0], 'v', markersize=5, color='r')

plt.show()


###basic anaylsis on portfolio returns over the test time frame

returns = portfoliodata.portfolio['percent_change']

# annualized Sharpe ratio, 252 trading days in a year
sharpe_ratio = np.sqrt(252) * (returns.mean() / returns.std())
print(sharpe_ratio)


# Calculate the max drawdown over test timeframe
window = len(pricedata.price_df.index)
rolling_max = pricedata.price_df['4. close'].rolling(window, min_periods=1).max()
rolling_drawdown = pricedata.price_df['4. close']/rolling_max - 1.0

# Calculate the maximum drawdown over test time frame
max_drawdown = rolling_drawdown.rolling(window, min_periods=1).min()


rolling_drawdown.plot(label="Rolling Drawdown")
max_drawdown.plot(label="Max Drawdown")
plt.legend()
plt.show()
