# https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/master/Filtered-Stream/filtered_stream.py

import time
import requests
import json
import config
import exchange
import itertools
import telegrambot
from dogevision import fromImageUrlToProbability

consumer_key = config.authenticate._twitter_key
secret_key = config.authenticate._twitter_secret


def get_bearer_token():
    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        auth=(consumer_key, secret_key),
        data={"grant_type": "client_credentials"})

    if response.status_code != 200:
        print("cannot get a bearer token (HTTP {}) : {}".format(response.status_code, response.text))

    body = response.json()
    return body['access_token']


def create_rule():
    payload = {
        "add": [
            {"value": "from:" + str(config.twitter_id)},
        ]
    }
    response = requests.post("https://api.twitter.com/2/tweets/search/stream/rules",
                             headers={"Authorization": "Bearer {}".format(
                                 get_bearer_token())}, json=payload)

    if response.status_code == 201:
        print("Response: {}".format(response.text))
    else:
        print("Cannot create rules (HTTP {}): {}".format(response.status_code, response.text))


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers={"Authorization": "Bearer {}".format(
            get_bearer_token())})

    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers={"Authorization": "Bearer {}".format(
            get_bearer_token())}, json=payload)

    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def buy_doge_on_binance():
    exchange.set_market_order('DOGE')
    exchange.set_trailing_stop_loss('DOGE')
    print('Doge found, order sent')


def checker(string_text, list_perms, prob_doge):
    plain_text = string_text.replace(' ', '').lower()
    if (any(word in plain_text for word in list_perms)) or prob_doge > 0.9:  # checking for doge
        buy_doge_on_binance()


def create_url():
    expansions = "expansions=attachments.media_keys"
    media_fields = "media.fields=url"
    url = "https://api.twitter.com/2/tweets/search/stream?{}&{}".format(
        expansions,
        media_fields
    )
    return url


def stream_connect(token, list_perms):
    search_url = create_url()
    search_headers = {
        "Authorization": "Bearer {}".format(token),
    }

    with requests.get(search_url,
                      headers=search_headers,
                      stream=True) as response:
        print(response.status_code)
        telegrambot.send_msg('Status Code: ' + str(response))
        if response.status_code != 200:
            raise Exception(
                "Cannot get stream (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )

        for response_line in response.iter_lines():
            if response_line:
                tweet = json.loads(response_line)
                print(tweet)
                tweet_txt = tweet['data']['text']
                if 'includes' in tweet.keys():
                    tweet_image_url = tweet['includes']['media'][0]['url']
                    probability_doge_related = fromImageUrlToProbability(tweet_image_url)[1]
                    telegrambot.send_msg('##### DOGE MEME DETECTED #####'
                                         'Probability Meme Doge Related: '
                                         + str(probability_doge_related) + '%')
                if probability_doge_related:
                    checker(tweet_txt, list_perms, probability_doge_related)
                else:
                    probability_doge_related = 0
                    checker(tweet_txt, list_perms, probability_doge_related)
                telegrambot.send_msg('Tweet trigger: ' + tweet_txt)


def main():
    telegrambot.send_msg('Running main.py')
    d = {'d': ['d', 'ð', 'Ð', 'Þ', '6'],
         'o': ['0', 'o', 'ô', 'ö', 'ò', 'ø', 'ó', 'º', '®', '©', 'õ'],
         'g': ['g', '9', 'ç'],
         'e': ['e', 'é', 'ê', 'ë', 'è', 'æ', '3']}
    list_perms = [''.join(v) for v in itertools.product(*d.values())]
    token = get_bearer_token()
    rules = get_rules()
    delete_all_rules(rules)
    create_rule()
    timeout = 0

    print('Opened Twitter Stream')
    while True:
        stream_connect(token, list_perms)
        time.sleep(25)
        # time.sleep(2 ** timeout)
        # timeout += 1


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Caught exception, re-running main')
        telegrambot.send_msg('Exception: ' + str(e))
        time.sleep(30)
        main()
    finally:
        telegrambot.send_msg('SKUMLEON DEAD: please /skumleon !!!')
