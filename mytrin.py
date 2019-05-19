# Amanda Shen 
# import library 
import pandas as pd
import quandl
import matplotlib.pyplot as plt
import math
#--------------------------------------------------------------------------------------------------------------
# get data 
sp500 = quandl.get("CHRIS/CME_SP1", authtoken = "ktxq1e9qz5uVEyn1Zgem" , start_date = "2018-01-1")

num_advancing = quandl.get("URC/NYSE_ADV", authtoken = "ktxq1e9qz5uVEyn1Zgem" , start_date = "2018-01-1")

num_declining = quandl.get("URC/NYSE_DEC", authtoken = "ktxq1e9qz5uVEyn1Zgem" , start_date = "2018-01-1")

vol_advancing = quandl.get("URC/NYSE_ADV_VOL", authtoken = "ktxq1e9qz5uVEyn1Zgem" , start_date = "2018-01-1")

vol_declining = quandl.get("URC/NYSE_DEC_VOL", authtoken = "ktxq1e9qz5uVEyn1Zgem" , start_date = "2018-01-1")

# create a new dataframe to sum up all the info I want: 
master = pd.DataFrame()

master['num_advancing'] = num_advancing['Numbers of Stocks']

master['num_declining'] = num_declining['Numbers of Stocks']

master['vol_advancing'] = vol_advancing['Numbers of Stocks']

master['vol_declining'] = vol_declining['Numbers of Stocks']

join_data = master.join(sp500)
join_data = join_data.fillna(method = 'ffill')
master = join_data

#--------------------------------------------------------------------------------------------------------------
# calculate trin value : (advances / declines) / (advancing volume / declining volume)
top = (master['num_advancing'])/(master['num_declining'])
botton = master['vol_advancing']/(master['vol_declining']) 
TRIN = top/botton  
master['TRIN'] = TRIN
#master['TRIN'] = master['TRIN'].apply(lambda x: math.log(x))
master['Close'] = master['Last']
#--------------------------------------------------------------------------------------------------------------
# Constructing the band 
# Short term: 10 day moving average, bands at 1.5 standard deviations. (1.5 times the standard dev. +/- the SMA)
# Medium term: 20 day moving average, bands at 2 standard deviations.
# Long term: 50 day moving average, bands at 2.5 standard deviations.
# ask user for use for types of term: 
print("Enter 1 for short term")
print("Enter 2 for medium term")
print("Enter 3 for long term")
term_indicator=input("Enter your desire term period: ")
if(term_indicator==1):
  ma_len=10
  mv_sd_constant=1.5
  bl_sd_constant=2
elif(term_indicator==2):
  ma_len=20
  mv_sd_constant=2
  bl_sd_constant=2.5
elif(term_indicator==3):
  ma_len=50
  mv_sd_constant=2.5
  bl_sd_constant=3
else:
  ma_len=10
  mv_sd_constant=1.5
  bl_sd_constant=2

master['moving_average'] = master['TRIN'].rolling(ma_len).mean() # Calculating the moving average of the TRIN
master['previous_TRIN'] = master['TRIN'].shift(1)
# caluclate standard deviation:
temp = master['TRIN']-master['moving_average'] # Difference a-b
temp2 = temp.apply(lambda x:x**2)  #(a-b)^2
temp3 = temp2.rolling(ma_len - 1).mean() # Summation (a-b)^2 / (ma_len - 1)
sd = temp3.apply(lambda x: math.sqrt(x)) # Calculating the standard deviation
mv_sd_constant_sigma = mv_sd_constant * sd
bl_sd_constant_sigma = bl_sd_constant * sd
master['Upper Bollinger Band'] = master['moving_average']+mv_sd_constant_sigma 
master['lower Bollinger Band'] = master['moving_average']-mv_sd_constant_sigma 
master['Upper Stoploss Band'] = master['Upper Bollinger Band']+bl_sd_constant_sigma
master['Lower Stoploss Band'] = master['lower Bollinger Band']-bl_sd_constant_sigma 
master['position'] = pd.Series() # list which contains the orders: BUY / SELL / Do Nothing
size = master['TRIN'].size  # Total Number of data point
#--------------------------------------------------------------------------------------------------------------
#print(master['Upper Bollinger Band'])
Profit_tracker = 0  # Profit Variable
is_first_transaction = 1 # Flag is there for begin first transaction -- transaction should start with LBB/UBB crossing only
buy_flag = False
sell_flag = False
transaction_start_price = 0
abs_SL = 25  # Absolute Stoploss Variable
trading_status = list()
order_details = list()
order = list()  #list which contains the orders: BUY / SELL / Do Nothing
profit = list()
buy_sell = list()
stoploss = list()
trade_cause = list()

for i in range(size):

    Profit_tracker = 0
    future_cost = master['Close'][i]
    TRIN = master['TRIN'][i]
    TRIN_prev = master['previous_TRIN'][i]
    LBB = master['lower Bollinger Band'][i]
    UBB = master['Upper Bollinger Band'][i]
    mAvg = master['moving_average'][i]
    USL = master['Upper Stoploss Band'][i]
    LSL = master['Lower Stoploss Band'][i]

  # for each day's moving avaergae, determine its position: 
    # if today's trin ge above UBB and yesterday's below: raise
    UBB_cross = (TRIN > UBB) and (TRIN_prev < UBB)  # Check if TRIN crosses Upper Bollinger Band
    #how much avaerage is moving: compare to ourselves
    mAvg_cross_up = (TRIN > mAvg) and (TRIN_prev < mAvg)  # Check if TRIN crosses moving average from low to high
    # if today's trin ge below LBB and yesterday's above: drop
    LBB_cross = (TRIN < LBB) and (TRIN_prev > LBB)  # Check if TRIN crosses Lower Bollinger Band
    mAvg_cross_down = (TRIN < mAvg) and (TRIN_prev > mAvg)  # Check if TRIN crosses moving average from high to low
    # stoploss for high price: to sell: when to sell
    USL_cross = (TRIN > USL) and (TRIN_prev < USL) # Check if TRIN Crosses upper stoploss band
    # stoploss for high price: to buy or long, when to buy:
    LSL_cross = (TRIN < LSL) and (TRIN_prev > LSL) # Check if TRIN Crosses lower stoploss band

    # Strategy
    # if ubb corss, high trin: Overbought describes a period of time where there has been a significant and consistent upward move in price over a period of time without much pullback, so we want to buy immediately and sell highter in the future: 
    if(UBB_cross and (not buy_flag) and is_first_transaction == 1):# not in buying position already
        is_first_transaction = 0
        buy_flag = True # buy 
        sell_flag = False
        transaction_start_price = future_cost
        order_details = [1, "Buy", "UBB Crossed", "UBB Crosse", "Position taken"]
    # same reason as above but the opposite: 
    elif(LBB_cross and (not sell_flag) and is_first_transaction == 1):# not in short position already
        is_first_transaction = 0
        sell_flag = True
        buy_flag = False
        transaction_start_price = future_cost
        order_details = [-1, "Sell", "LBB Crossed", "LBB Crossed", "Position taken"]
#-----------------------------------------------------------------------------------------------------------------
    elif(mAvg_cross_up and (not buy_flag) and is_first_transaction == 0):  # Places "BUY" order if TRIN crosses mAvg from low to high to close a trade
        is_first_transaction = 1
        buy_flag = True
        sell_flag = False
        Profit_tracker = future_cost - transaction_start_price
        order_details = [1, "Buy", "mAvg Crossed", "mAvg Crossed", "Position Closed"]

    elif(LSL_cross and (not buy_flag) and is_first_transaction == 0):  # Places "BUY" order if TRIN crosses lower stoploss band to close a trade
        is_first_transaction = 1
        buy_flag = True
        sell_flag = False
        Profit_tracker = future_cost - transaction_start_price
        order_details = [1, "Buy", "LSB Crossed", "Stoploss Executed", "Position Closed"]
  # set 25 limit for stop risk management: abs_SL=25
    elif((future_cost - transaction_start_price) > abs_SL and (not buy_flag) and is_first_transaction == 0):  # Places "BUY" order if TRIN crosses lower stoploss absolute value
        is_first_transaction = 0
        buy_flag = True
        sell_flag = False
        Profit_tracker = future_cost - transaction_start_price
        order_details = [1, "Buy", "LSB Crossed", "Stoploss Executed", "Position Closed"]
#------------------------------------------------------------------------------------------------------------------
    elif(mAvg_cross_down and (not sell_flag) and is_first_transaction == 0):  # Places "Sell" order if TRIN crosses mAvg from high to low to close a trade
        is_first_transaction = 1
        buy_flag = False
        sell_flag = True
        Profit_tracker = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "mAvg Crossed (H to L)", "0", "Position Closed"]

    elif(USL_cross and (not sell_flag) and is_first_transaction == 0):  # Places "Sell" order if TRIN crosses Upper stoploss band to close a trade
        is_first_transaction = 1
        buy_flag = False
        sell_flag = True
        Profit_tracker = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "USB Crossed", "Stoploss Executed", "Position Closed"]

    elif( (- future_cost - transaction_start_price) > abs_SL and (not sell_flag) and is_first_transaction == 0):  # Places "SELL" order if TRIN crosses Upper stoploss absolute value
        is_first_transaction = 1
        buy_flag = False
        sell_flag = True
        Profit_tracker = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "USB Crossed", "Abs Stoploss Executed", "Position Closed"]
    #no trade happened: in the range
    else:
        if(buy_flag == False and sell_flag == False):
            tempo = "0"
        else:
            if(buy_flag == 1 and sell_flag == 0):
                tempo = (master['Close'][i] - transaction_start_price) * 500
            if(buy_flag == 0 and sell_flag == 1):
                tempo = (- master['Close'][i] + transaction_start_price) * 500
        order_details = [0, "No Trade", "No Trade", "0", tempo]
    
    #upload information each day: 
    #print(Profit_tracker)
    Profit_tracker=0.99*Profit_tracker # transcation cost 1%
    profit.append(round(Profit_tracker,4) * 500)

master['profit'] = pd.Series(profit,index=master.index)
mean_return=master.profit.mean()
print(master.columns)
print("Mean return: ",round(mean_return,4))
#print(master['profit'],master['daily_return'])