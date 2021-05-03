import tweepy
import pandas as pd
import numpy as np
import numba
from tqdm.notebook import tqdm


flat_currency_list = pd.read_hdf("data/flat_currency_list.h5")

def __attributes_from_tweet(tweet):

        id_ = tweet.id
        name = tweet.user.name

        posted_at = tweet.created_at
        text = tweet.full_text

        return [id_, name, posted_at, text]

def retrieve_user_timeline(credential_handler, userID, date_since=None, verbose=False):
    
    #pass twitter credentials to tweepy
    twit_auth = tweepy.OAuthHandler(credential_handler._twitter_key, 
                                    credential_handler._twitter_secret)
    twit_auth.set_access_token(credential_handler._twitter_access_key, 
                               credential_handler._twitter_access_secret)
    
    api = tweepy.API(twit_auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    # define query
    query = tweepy.Cursor(api.user_timeline, id=userID, count=1000,
                          tweet_mode='extended').items()
    
    iterator = lambda x: x if not verbose else tqdm(x)

    # retrieve tweets
    tweets = [__attributes_from_tweet(tweet) for tweet in iterator(query)]

    # create dataframe
    df = pd.DataFrame(tweets, columns = ['tweetid', 'username', 'posted_at', 'text'])
    
    
#     # Save dataframe
#     date_since = str(df['posted_at'].min().date())
#     username = df['username'].loc[0].replace(' ', '_')
#     df.to_hdf(f"data/{username}_{date_since}.h5", key='tweets')
    
    return df


numba.jit(nopyton=True)
def check_for_crypto_content(text):
    return np.unique([idx if x in text else 999 for idx, x in enumerate(flat_currency_list['ref'].values)])[0]
    
    
    