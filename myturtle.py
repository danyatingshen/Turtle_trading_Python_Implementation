# Amanda Shen Turtle trading strategy imp
#Import the libraries to get the closing prices data
from pandas_datareader import data as pandanreader
import fix_yahoo_finance as yf
yf.pdr_override()
#data Manipulation
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
data_length=0
def turtle(future_id):
  # get data from yahoo with spesified parameter: 
    future = pandanreader.get_data_yahoo(future_id, start = "2018-1-01", end = "2019-1-01")
    data_length=future.size
    # System 1
    # 20 days high
    future['high20'] = future.Close.shift(1).rolling(window = 20).max()
    # 20 days low
    future['low20'] = future.Close.shift(1).rolling(window = 20).min() 
    # 20 days mean
    future['avg20'] = future.Close.shift(1).rolling(window = 20).mean()
    #print(future['high20'])
    future['PDC20'] = future.Close.shift(1)
    # print(future.index)
    # System 2
    # 55 days high
    future['high55'] = future.Close.shift(1).rolling(window = 55).max()
    # 50 days low
    future['low55'] = future.Close.shift(1).rolling(window = 55).min() 
    # 50 days mean
    future['avg55'] = future.Close.shift(1).rolling(window = 55).mean()
    #print(future['high20'])
    future['PDC55'] = future.Close.shift(1)
    # print(future.index)
   
    #print(future['Close'])
    # print(future['PDC20'])
  #Position Sizing
    # find N for 20 days True Range = Maximum(H - L,H - PDC, PDC - L)
    true_value = []
    N=[]
    unit=[]
    prv_is_losing=-1
    index=0
    for row in future.itertuples():
      true_value.append(max(row[7]-row[8],row[7]-row[10],row[10]-row[7]))
    #N = (19 × PDN + TR ) /20
    for row in future.itertuples():
      N.append((19*row[10]+true_value[index])/20)
      index=index+1
      #Unit = (1% of Account/(N × Dollars per Point )
      #assume our account has 1,000,000
    counter=0
    for date in range(len(N)):
      if N[counter]==0:
        unit.append(0)
        counter=counter+1
      else:
        unit.append((0.01*1000000)/(N[counter]*5000))
        counter=counter+1
    future['N'] = pd.Series(N, index=future.index)
    future['true_value'] = pd.Series(true_value, index=future.index)
    future['unit'] = pd.Series(unit, index=future.index)
    future['Next'] = future.Close.shift(-1)
    
      #System 1 Entry - Turtles entered positions when the price exceeded by a single tick the high     or low of the preceding 20 days.
      #If the price exceeded the 20-day high, then the Turtles would buy one Unit to initiate a long position in the corresponding commodity. 
    
      #If the price dropped one tick below the low of the last 20-days, the Turtles would sell one Unit to initiate a short position. 

      # This breakout would be considered a losing breakout if the price subsequent to the date of the breakout moved 2N against the position before a profitable 10-day exit occurred.
    future['long_20_position'] = future.Close > future.high20
    future['long_cost']=future['long_20_position']*future.Close*future['unit']

    future['short_20_position'] = future.Close < future.low20
    future['short_cost']=future['short_20_position']*(-future.Close*future['unit'])

    

    future['long_55_position'] = future.Close > future.high55
    future['long_55_cost']=future['long_55_position']*future.Close*future['unit']

    future['short_55_position'] = future.Close < future.low55
    future['short_55_cost']=future['short_55_position']*(-future.Close*future['unit'])

    future['cost20']=future['long_cost']+future['short_cost']
    future['cost55']=future['long_55_cost']+future['short_55_cost']
    
    # print(future['short_cost'])
    # print(future['cost'])
    # print(future.Close)
    #print(future['unit'])
    # DETERMIN LOSING TRADE: 
    #create another column with previous day's closing price to compare: 
    future['Next'] = future.Close.shift(-1)
#Preset a tracker variable to -1 for whether last trde is losing trade or winning trade:
    future['prv_is_losing']=-1
    #Check if last trade is in long position:
    for day in range(future['prv_is_losing'].size):
      if (future['long_20_position'] =='True').any():
        if (future.Next<future.low20-(2*future.N)):
          future['prv_is_losing']=1
        else:
           future['prv_is_losing']=-1
      if (future['short_20_position'] =='True').any():
        if future.Next>future.low20-(2*future.N):
          future['prv_is_losing']=0
        else:
           future['prv_is_losing']=-1
    #print(future['prv_is_losing'])

    
    if(prv_is_losing==-1):
      future['final_cost']=future['cost20']
    else:
      future['final_cost']=future['cost50']
    


  #If price go up more than 2N for long position, stop loss
    future['long_stop_loss'] = future.Close+2*future['N']
  #If price go down more than 2N for short position, stop loss
    future['short_stop_loss'] = future.Close-2*future['N']

# System 1
    # 10 days high
    future['high10'] = future.Close.shift(1).rolling(window = 10).max()
    # 10 days low
    future['low10'] = future.Close.shift(1).rolling(window = 10).min() 
  #System 1 exsit
    future['long_exit']= 0
    future['short_exit'] = 0
    if prv_is_losing==1 or prv_is_losing==0 :
      future['long_exit']= 1
      future['short_exit'] = 1
    #System 2 exsit
   
      # 10 day low for long position: 
    future['long_exit1']= future.Close < future.low10
      # 10 day high for short position: 
    future['short_exit1'] = future.Close > future.high10
      # 20 day low for long position: 
    future['long_exit2']= future.Close < future.low20
      # 20 day low for long position:
    future['short_exit2'] = future.Close > future.high20

    future['profit']=0
    #for day in range(future['prv_is_losing'].size):
    if(future['long_exit']==1).any():
      future['profit']=-(future['cost20']+future['cost55'])
    if(future['short_exit']==1).any():
      future['profit']=-(future['cost20']+future['cost55'])

    if(future['long_exit1']==1).any():
      future['profit']=-(future['cost20'])
    if(future['short_exit1']==1).any():
      future['profit']=-(future['cost20'])
    if(future['long_exit2']==1).any():
      future['profit']=-(future['cost55'])
    if(future['short_exit2']==1).any():
      future['profit']=-(future['cost55'])
    future['profit']=future['profit']*0.99
    print(future.columns)
    print(future['profit'])
    return future['profit'].sum();
    
# Consider the case of heating oil
print("Usage: ")
print("Enter future ticket on Yahoo Finance, default is APPL")
print("Notice: ")
print("We will ignore data that is null or nan for daily return")
future_id = input("Enter your future ticket: ")

if future_id:
  portfolio = [future_id]
else:
  portfolio = ['SM=F']

sum=0;
length=data_length
cum_daily_return = pd.DataFrame()
for stock in portfolio:
    cum_daily_return = turtle(stock)
print ("daily returns")
sum = cum_daily_return
print("Average return for this period: ",sum,"%")
print("Since we ignore transition cost for this estimate return, we deduct 3~5% off for more realistic number: ", sum-(sum*0.03),"~",sum-(sum*0.05))
