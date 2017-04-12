"""
The purpose of this algorithm is to evalutate RSI data for the given products.

Ideas:
1. Track areas above and below a specified RSI range. Track the average time
in these signal areas correlated with the probability of trend change?

2. Develop an RSI average
"""

from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters.morningstar import Q1500US

import talib
import numpy as np

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(minutes=15))

    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())

    # Update context data
    schedule_function(update_data, date_rules.every_day(), time_rules.market_open())

    # Define the products
    context.stocks = [sid(42477)]

    # Dummy product
    context.stock = sid(42477)

    # Variable to hold prices for each Natural Gas tool
    context.prices = {context.stock: 0}

    # Dictionary holding rsi signal levels
    context.RSI_levels = [{ 'high': 70},
                          { 'low': 30}]

    # Variable to count the average number of days in signal areas
    context.signal_period = {context.stock: 0}

    # Variable to hold signal type: 0-nuetral 1-bear 2-bull
    context.signal_period_type = {context.stock: 0}

    # Variables to hold RSI levels for Natural Gas Products
    context.rsis = {context.stock: 0}

    # Track lengths of all signal periods
    context.signal_periods = {context.stock: []}

    # Variable to hold RSI signal period averages
    context.signal_period_averages = {context.stock: 0}

def before_trading_start(context, data):
    """
    Called every day before market open.
    """

def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    pass

def my_rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    pass

def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """

    # Record variables
    for stock in context.stocks:
        if (context.rsis[stock]):
            record(rsi = context.rsis[stock],
                  signal_type = (context.signal_period_type[stock] * 100))
    pass

def handle_data(context, data):
    """
    Called every minute.
    """
    pass

"""
Custom Cycle Functions
"""

def update_data(context, data):
    #log.info('Updating data: ')
    get_prices(context, data)
    get_rsis(context, data)
    get_rsis_signal_type(context)
    update_signal_period_length(context)
    update_signal_period_average(context)


    for stock in context.stocks:
        log.info('STOCK INFO')
        print ('Current period: ' + str(context.signal_period[stock]) + '\n')
        print ('Current Average: ' + str(context.signal_period_averages[stock]) + '\n')
        print ('Current Type: ' + str(context.signal_period_type[stock]) + '\n')

    pass

"""
Custom Functions
"""

# Resets the day count for time in signal areas.
def reset_signal_count(context, stock):
    context.signal_period[stock] = 0
    pass

# Adds a day to the signal period
def increment_signal_period(context, stock):
    context.signal_period[stock] = context.signal_period[stock] + 1
    pass

# Gets prices and returns to context
def get_prices(context, data):
    for stock in context.stocks:
        prices = data.history(stock, 'close', 20, '1d')
        context.prices[stock] = prices
    pass

# Calculates RSIs and returns to context.
def get_rsis(context, data):
    for stock in context.stocks:
        prices = context.prices[stock]
        context.rsis[stock] = talib.RSI(prices, timeperiod=15)[-1]
    pass

# Check the RSI level and determine signal period needs to reset or begin
# Tracks all periods
def get_rsis_signal_type(context):
    for stock in context.stocks:
        rsi = context.rsis[stock]
        high = context.RSI_levels[0].get('high')
        low = context.RSI_levels[1].get('low')

        # RSI for stock is greater than the RSI_high
        # Change signal type and change signal period
        if (rsi >= high):
            context.signal_period_type[stock] = 1
        elif ((rsi < high) & (context.rsis[stock] > low)):
            context.signal_period_type[stock] = 0
        elif (rsi <= low):
            context.signal_period_type[stock] = -1
        else:
            print 'Not in Range'

# Daily: updates a signal period length -> used for average signal period lengths
def update_signal_period_length(context):
    for stock in context.stocks:
        # Increment a rsi signal period if it is not nuetral
        rtype = context.signal_period_type[stock]
        if(rtype != 0):
            increment_signal_period(context, stock)
        elif(context.signal_period[stock] > 0):
            period_length = context.signal_period[stock]
            # When period is over push it to the existing periods for average calculation
            add_signal_period(context, stock, period_length)
            reset_signal_count(context, stock)

# Add a period to a stocks list of periods
def add_signal_period(context, stock, period):
    context.signal_periods[stock].append(period)
    pass

# Get average given a list of numbers
def update_signal_period_average(context):
    for stock in context.stocks:
        if (len(context.signal_periods[stock]) > 0):
            context.signal_period_averages[stock] = np.average(context.signal_periods[stock])
        pass
