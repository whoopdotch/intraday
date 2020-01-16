import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, date, timedelta, timezone

# there's a limit from yfinance to only get intraday data for the last 30 days
START_DATE = date.today() - timedelta(days=30)

def to_utc(d):
    return d.tz_convert(timezone.utc)

def df_to_utc(df):
    df.index = df.index.map(to_utc)
    
def get_tickerfile(ticker, ticker_type = None):
    dirname = os.path.dirname(__file__)
    if ticker_type != None:
        if os.path.isdir(dirname + '/data/' + ticker_type) == False:
            try:
                os.mkdir(dirname + '/data/' + ticker_type)
            except OSError:
                print ("Creation of the directory %s failed" % dirname + '/data/' + ticker_type)
                exit()
            else:
                print ("Successfully created the directory %s " % dirname + '/data/' + ticker_type)
        return dirname + '/data/' + ticker_type + '/' + ticker + '.csv'
    else:
        return dirname + '/data/' + ticker + '.csv'  

def get_cache(ticker, ticker_type = None):
    filename = get_tickerfile(ticker, ticker_type)
    try:
        return pd.read_csv(filename, parse_dates=True, index_col='Datetime')
    except FileNotFoundError:
        print("Ticker cache file '{}' not found.\nCreating...".format(filename))
        # return empty data frame on error
        return pd.DataFrame()

def get_lastday(df):
    if len(df) == 0:
        return START_DATE
    df['temp'] = pd.to_datetime(df.index)
    max = df['temp'].max()
    df.drop(columns='temp', inplace=True)
    return max.date()
    
def get_ticker(ticker, ticker_type = None):
    old_df = get_cache(ticker, ticker_type)
    start_date = get_lastday(old_df) + timedelta(days=1)  
    end_date = start_date + timedelta(days=7)  
    print("getting ticker {} from {} to {}".format(ticker, start_date, end_date))
    # get new data
    t = yf.Ticker(ticker)
    df = t.history(start=start_date, end=end_date, interval="1m")
    if df.empty:
        print("returned data for ticker is empty - do not update cache")
    else: 
        # append new data
        old_df = old_df.append(df, sort=False)
        # serialize to CSV
        old_df.to_csv(get_tickerfile(ticker, ticker_type))
    # return latest data as UTC
    df_to_utc(old_df)
    return old_df

def get_ticker_all(ticker_type):
    # get dict from file
    dirname = os.path.dirname(__file__)
    xl_file = pd.ExcelFile(dirname + '/sources/Yahoo Ticker Symbols - September 2017.xlsx')
    dfs = {sheet_name: xl_file.parse(sheet_name, skiprows=3) for sheet_name in xl_file.sheet_names}
    # check if ticker type exists in file
    if ticker_type in dfs:
        for ticker in dfs[ticker_type]['Ticker']:
            get_ticker(ticker, ticker_type = ticker_type)
    else:
        print('Invalid input.\n' + ticker_type + ' does not exist')

