#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 12:11:45 2021

@author: jurjenvangenugten
"""
import sys; sys.path.append("../")
import requests
import json
import config
from config import CredentialHandler
import pandas as pd
from datetime import timedelta, datetime 
from binance.client import Client, BinanceAPIException
import pandas as pd
import calendar
import mplfinance as fplt
import numpy as np
import operator
from scipy.stats import linregress
import csv

delta_before = 10                       #collect historic data before tweets
delta_after = 10                        #collect historic data after tweets
max_tweets = 40                         #max tweets per category
max_tweet_age = timedelta(weeks = 26)   #max age of tweets
minimum_tweet_delta = 2                 #Ignore tweets that are less than x minutes together

auth = CredentialHandler("../auth.txt")
stream_url = "https://api.twitter.com/2/tweets/search/stream"
rules_url = "https://api.twitter.com/2/tweets/search/stream/rules"

#get targets from text
targets = []
with open('targets.txt', newline='') as csvfile:
    contents = csv.reader(csvfile, delimiter=',')
    for target in contents:
        targets.append(target[0])
    
#get coins from text
with open('coin_dict.txt','r') as inf:
    coin_list = eval(inf.read())

def get_bearer_token():
    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        auth=(auth._twitter_key, auth._twitter_secret),
        data={"grant_type": "client_credentials"})
    if response.status_code != 200:
        print("cannot get a bearer token (HTTP {}) : {}".format(response.status_code, response.text))
        pass
    body = response.json()
    return body['access_token']

#normalize values starting value = 0 and increase/decrease measured in percentages (%)
def normalize(klines,exact_price): 
    for kline in klines:
        kline[1] = (float(kline[1])-exact_price)/exact_price
        kline[2] = (float(kline[2])-exact_price)/exact_price
        kline[3] = (float(kline[3])-exact_price)/exact_price
        kline[4] = (float(kline[4])-exact_price)/exact_price
    return(klines)

#limit tweets from target about specific coin to 40
def limit_tweets(tweet_list):
    #sort list to facilitate counting
    tweet_list.sort(key=operator.itemgetter('symbol'))
    tweet_list.sort(key=operator.itemgetter('target'))
    counter = 0
    target = ""
    symbol = ""
    tweet_list_capped = []
    for tweet in tweet_list:
        if counter < max_tweets:
            tweet_list_capped.append(tweet)
        if target == tweet['target'] and symbol == tweet['symbol']:
                counter += 1
        else:
            counter = 0
        target = tweet['target']
        symbol = tweet['symbol']  
    return(tweet_list_capped)
        
#get tweets from target id. Select tweets that mention a coin
def get_tweets(token,targets):
    tweet_list = []
    for target in targets:        
        #get username
        url = "https://api.twitter.com/1.1/users/show.json?user_id={}".format(target)
        for response_line in requests.get(url, headers={"Authorization": "Bearer {}".format(  token)}, stream=True).iter_lines():
            name = json.loads(response_line)['name']
        
        #get tweet
        next_token = ''
        for i in range(6): #check latest 600 tweets, if target doesn't have that many, error is thrown and code continues
            url = "https://api.twitter.com/2/users/{}/tweets?tweet.fields=id,created_at&exclude=replies,retweets&max_results=100{}".format(target,next_token)
            response = requests.get(url, headers={"Authorization": "Bearer {}".format(token)}, stream=True)
            for response_line in response.iter_lines():
                try:
                    if json.loads(response_line)['meta']['next_token']:
                        
                        #create pagination token for scrolling through pages
                        next_token = '&pagination_token={}'.format(json.loads(response_line)['meta']['next_token'])
                        for tweet in json.loads(response_line)['data']:
                            plain_text = tweet['text'].replace(' ', '').lower()
                            for symbol, coin in coin_list.items():
                                
                                #check tweet for coin
                                if any(word in plain_text for word in coin):
                                    timestamp = datetime.strptime(tweet['created_at'].replace('T',' ').replace('.000Z',''), '%Y-%m-%d %H:%M:%S')
                                    
                                    #limit age of tweet
                                    if (datetime.today() - max_tweet_age < timestamp):
                                        tweet_list.append({'target':target,
                                                           'timestamp':timestamp,#+ timedelta(hours=1),   #add 1 hour to compensate for timezone
                                                           'symbol':symbol.upper(),
                                                           'text':tweet['text'],
                                                           'username':name})
                                        
                                        #remove tweets that are too close together
                                        if len(tweet_list) > 1 and (tweet_list[-2]['timestamp'] - tweet_list[-1]['timestamp']) < timedelta(minutes=minimum_tweet_delta) and tweet_list[-1]['target'] == tweet_list[-2]['target'] and tweet_list[-1]['symbol'] == tweet_list[-2]['symbol']:
                                            tweet_list.pop()
                    else:
                        continue
                except KeyError:
                    continue     
    #remove excess tweets
    tweet_list = limit_tweets(tweet_list)
    return(tweet_list)

#get historic price data from binance
def fetch_history(tweet_list):
    before_minutes = timedelta(minutes=delta_before)
    after_minutes = timedelta(minutes=delta_after)
    binance_client = Client(api_key=auth._binance_key,api_secret=auth._binance_secret)
    kline_size = '1m'

    index = 0
    for tweet in tweet_list[:]:
        current_point = tweet['timestamp']   
        oldest_point = (current_point - before_minutes).strftime("%d %b %Y %H:%M:%S")
        newest_point = (current_point + after_minutes).strftime("%d %b %Y %H:%M:%S")
        current_unix = int(calendar.timegm(current_point.timetuple()))*1000
        symbol = '{}USDT'.format(tweet['symbol'])
        try:
            
            #get candles from binance
            klines = binance_client.get_historical_klines(symbol, kline_size, oldest_point, newest_point)
            
            #get price of coin on the exact moment of the tweet
            fetch_price = binance_client.get_aggregate_trades(symbol=symbol,
                                                                    startTime=current_unix,
                                                                    endTime=current_unix+30000,
                                                                    limit=1)
            #check if exact_price contains a value else use opening price
            if klines and len(fetch_price) > 0:
                exact_price = fetch_price[0]['p']
            else:
                exact_price = klines[delta_before][1]
            
            #normalize historic price data and append to tweet_list
            klines_normal = normalize(klines,float(exact_price))
            data = pd.DataFrame(klines_normal, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
            data = data.drop(columns=['volume', 'close_time', 'quote_av','tb_base_av', 'tb_quote_av', 'ignore' ])
            tweet['historic_data'] = data
        except BinanceAPIException as e:
            print("Error: {} for {}".format(e,symbol))
        except IndexError:
             tweet_list.remove(tweet)
        index +=1
        if index % int((len(tweet_list) / 10))  == 0:
            print('{}% complete'.format(round(float((index/len(tweet_list))*100),0)))
    return(tweet_list)

#generate mean from all historic data per target per coin
def generate_mean(tweet_list):
    tp_list_mean = []
    for target in targets:                 
        for symbol in coin_list.keys():     
            temp_list = []
            for tweet in tweet_list:           #
                if tweet['target'] == target and tweet['symbol'] == symbol:       
                       temp_list.append(tweet['historic_data'])
                       name = tweet['username']
            if temp_list:
                df_concat = pd.concat(temp_list)
                by_row_index = df_concat.groupby(df_concat.index).mean()
                tp_list_mean.append({'username':name,'target':target,'symbol':symbol,'mean_data':by_row_index})
    return(tp_list_mean)            

#Summarize findings in dataframe
def create_summary(tp_list,tp_list_mean):
    mean_column = 'mean ({} minutes)'.format(delta_after)
    max_column = 'max ({} minutes)'.format(delta_after)
    columns=['username','target_id','coin_symbol','tweet_count',mean_column,'mean_std','mean_coef',max_column,'max_std','max_coef','time_max','min','time_min','revenue (.05)','revenue optimized']
    target_summary = pd.DataFrame(columns=columns)
    
    #summarizing measures based on tp_list_mean
    index = 0
    for data_item in tp_list_mean:
        #set username
        target_summary.loc[index,'username'] = data_item['username']
        #set target_id
        target_summary.loc[index,'target_id'] = data_item['target']
        #set coin_symbol
        target_summary.loc[index,'coin_symbol'] = data_item['symbol']
        #set tweet_count
        target_summary.loc[index,'tweet_count'] = 0
        #add mean increase in value, x minutes after posting tweet
        target_summary.loc[index,mean_column] = np.mean((data_item['mean_data'].iloc[delta_before:,1]+data_item['mean_data'].iloc[delta_before:,2])/2)
        #add max increase in value, x minutes after posting tweet
        target_summary.loc[index,max_column] = max(data_item['mean_data'].iloc[delta_before:,1])
        #add minutes until peak is reached
        target_summary.loc[index,'time_max'] = data_item['mean_data'].iloc[delta_before:,1].idxmax() -10
        #add max decrease in value, x minutes after posting tweet
        target_summary.loc[index,'min'] = min(data_item['mean_data'].iloc[delta_before:,2])
        #add minutes until minimum is reached
        target_summary.loc[index,'time_min'] = data_item['mean_data'].iloc[delta_before:,2].idxmin() -10
        index+=1
        
    #summarizing measures based on tp_list (un-averaged)
    for index,df_item in target_summary.iterrows():
        mean_list = []
        max_list = []
        for list_item in tp_list:
            if df_item["target_id"] == list_item['target'] and df_item['coin_symbol'] == list_item['symbol']:
                #add number of tweets on which calculations are based
                df_item['tweet_count'] += 1
                mean = np.mean((list_item['historic_data'].loc[delta_before:,'high']+list_item['historic_data'].loc[delta_before:,'low'])/2)
                mean_list.append(np.mean(mean))
                max_list.append(max(list_item['historic_data'].loc[delta_before:,'high']))
        #add std dev of the mean value
        df_item['mean_std'] = np.std(mean_list)
        #add std dev of the max value
        df_item['max_std'] = np.std(max_list)
        #add slope coefficient: is mean impact of tweets rising or falling
        slope, intercept, r_value, p_value, std_err = linregress([i for i in range(len(mean_list))],mean_list)
        df_item['mean_coef'] = slope
        #add slope coefficient: is max impact of tweets rising or falling
        slope, intercept, r_value, p_value, std_err = linregress([i for i in range(len(max_list))],mean_list)
        df_item['max_coef'] = slope
    return(target_summary)
'''    
    #generate plots of mean data
    index = 0
    for data_item in tp_list_mean:
        data_item['mean_data'].index = pd.to_datetime(data_item['mean_data'].index)
        fplt.plot(data_item['mean_data'],
                  type='candle',
                  title='{}{}, {} tweets'.format(data_item['username'],data_item['symbol'],target_summary.loc[index,'tweet_count']),
                  ylabel='Price ($)')
        index+=1
'''

def main():
    token = get_bearer_token()
    print("token collected..")
    
    print("collecting tweets..")
    tweet_list = get_tweets(token,targets) 
    print("{} tweets collected".format(len(tweet_list)))
    
    print("fetching historic price data..")
    tp_list = fetch_history(tweet_list)
    print("historic data collected")
    
    print("generating mean..")
    tp_list_mean = generate_mean(tp_list)
    print("mean_generated")

    print("summarizing results..")
    target_summary = create_summary(tp_list,tp_list_mean)
    print("Analysis complete")
    
    #return summary
    return(target_summary)

if __name__ == "__main__":
    data = main()
    
