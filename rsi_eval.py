"""
The purpose of this algorithm is to evalutate RSI data for the given products.
Trade based on the length of time spent above the high RSI level or low RSI level.

"""
import talib
import numpy as np

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open())

    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())

    context.stock = sid(41968)

    # Define the products
    context.stocks = [context.stock]

    # Variable to hold prices for each Natural Gas tool
    context.prices = {context.stock: 0}

    # Dictionary holding rsi signal levels
    context.RSI_levels = [{ 'high': 60},
                          { 'low': 40}]

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

    # Variables to hold weights of each product
    context.weights = {context.stock: 0}

    # Will execute trades after defined number of average signal periods
    context.enough_data = 1

def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    update_data(context, data)
    pass

def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    for stock in context.stocks:
        enough_data = (len(context.signal_periods[stock]) > context.enough_data)
        signal_period = context.signal_period[stock]
        signal_period_average = context.signal_period_averages[stock]
        signal_period_type = context.signal_period_type[stock]
        # Signal period is above average and there is enough sample data
        if((signal_period > signal_period_average) & enough_data):
            difference = (abs(signal_period - signal_period_average))
            total_average = ((signal_period + signal_period_average)/2)
            percentage_difference = ((difference/total_average))
            # Assign portfolio weight based on percentage difference
            if((signal_period_type == -1)):
                if(context.weights[stock] > 1):
                    context.weights[stock] = 1
                else:
                    context.weights[stock] = percentage_difference
            elif(signal_period_type == 1):
                neg_diff = 1 - (context.weights[stock] - percentage_difference)
                if((percentage_difference > 1) | (difference < 0)):
                    context.weights[stock] = 0
                else:
                    print ('sell difference: ' + str(neg_diff))
                    context.weights[stock] = neg_diff
    pass

def my_rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    for stock in context.stocks:
        if((data.can_trade(stock)) &
           (context.account.buying_power > 0) &
           (context.weights[stock] < 1) &
           (context.weights[stock] > 0)):
                order_target_percent(stock, context.weights[stock])
    pass

def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    # Record variables
    for stock in context.stocks:
        if (context.rsis[stock]):
            record(
                rsi = context.rsis[stock],
                signal_type = (context.signal_period_type[stock]),
                signal_period = context.signal_period[stock],
                current_weight = (context.account.total_positions_value/context.portfolio.portfolio_value)
            )
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
    get_prices(context, data)
    get_rsis(context, data)
    get_rsis_signal_type(context)
    update_signal_period_length(context)
    update_signal_period_average(context)
    my_assign_weights(context, data)
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
    pass


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
    pass

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

# Prints product information
def print_product_information(context):
    for stock in context.stocks:
        log.info('STOCK INFO')
        print ('Current period: ' + str(context.signal_period[stock]) + '\n')
        print ('Current Average: ' + str(context.signal_period_averages[stock]) + '\n')
        print ('Current Type: ' + str(context.signal_period_type[stock]) + '\n')
    pass