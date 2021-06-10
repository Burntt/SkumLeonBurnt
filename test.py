
## Get image url from whatever tweet

tweet = {'data': {'attachments': {'media_keys': ['3_1402965463064326149']}, 'id': '1402965476301545479', 'text': 'https://t.co/13TpL4VObh'}, 'includes': {'media': [{'media_key': '3_1402965463064326149', 'type': 'photo', 'url': 'https://pbs.twimg.com/media/E3hVp8oXMAUOd5S.jpg'}]}, 'matching_rules': [{'id': 1402965446450626566, 'tag': None}]}

#tweet = {'data': {'id': '1402967862499811328', 'text': 'asdfasdfasdfasdf'}, 'matching_rules': [{'id': 1402967839196303363, 'tag': None}]}

tweet_txt = tweet['data']['text']
print(tweet_txt)

if 'includes' in tweet.keys():
    tweet_image_url = tweet['includes']['media'][0]['url']
    print(tweet_image_url)