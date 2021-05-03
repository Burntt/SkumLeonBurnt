import time
import requests
import json
import config
import exchange
import itertools
import telegrambot
import coinmarketcap as cmc

consumer_key = config.authenticate._twitter_key
secret_key = config.authenticate._twitter_secret
# names_dict, slug_dict = cmc.ticker_aggregator()

stream_url = "https://api.twitter.com/2/tweets/search/stream"
rules_url = "https://api.twitter.com/2/tweets/search/stream/rules"


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
    response = requests.post(rules_url,
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


def checker(string_text, list_perms, name_ticker_pair, slug_ticker_pair):
    plain_text = string_text.replace(' ', '').lower()
    if any(word in plain_text for word in list_perms):  # checking for doge
        exchange.set_market_order('DOGE')
        exchange.set_trailing_stop_loss('DOGE')
        print('Doge found, order sent')


def stream_connect(token, list_perms, name_ticker_pair, slug_ticker_pair, retry_count=0):
    MAX_RETRIES = 10
    try:
        response = requests.get(stream_url,
                                headers={"Authorization": "Bearer {}".format(
                                    token)}, stream=True)
        for response_line in response.iter_lines():
            if response_line:
                tweet = json.loads(response_line)
                try:
                    checker(tweet['data']['text'], list_perms, name_ticker_pair, slug_ticker_pair)
                    tweet_txt = tweet['data']['text']
                    print(tweet_txt)
                    telegrambot.send_msg('Tweet trigger: ' + tweet_txt)
                except KeyError:
                    print('waiting for connection..')
                    time.sleep(5)
    except ConnectionResetError as c_reset_error:
        if retry_count == MAX_RETRIES:
            raise c_reset_error
        telegrambot.send_msg('ConnectionResetError' + str(c_reset_error))
        time.sleep(60)
        telegrambot.send_msg('Connection attempt: ' + str(retry_count))
        stream_connect(token, list_perms, name_ticker_pair, slug_ticker_pair, retry_count + 1)
    except requests.exceptions.ChunkedEncodingError as chunked_enc_error:
        telegrambot.send_msg('Chunked Encoding Error' + str(chunked_enc_error))
    except requests.RequestException as rand_stream_connect_error:
        telegrambot.send_msg('Random Exception' + str(rand_stream_connect_error))
    finally:
        telegrambot.send_msg('Unidentified Exception: struggling to stream connect to Twitter')


def main():
    telegrambot.send_msg('Running main.py')
    d = {'d': ['d', 'ð', 'Ð', 'Þ', '6'],
         'o': ['0', 'o', 'ô', 'ö', 'ò', 'ø', 'ó', 'º', '®', '©', 'õ'],
         'g': ['g', '9', 'ç'],
         'e': ['e', 'é', 'ê', 'ë', 'è', 'æ', '3']}
    list_perms = [''.join(v) for v in itertools.product(*d.values())]
    name_ticker_pair, slug_ticker_pair = cmc.ticker_aggregator()
    token = get_bearer_token()
    rules = get_rules()
    delete_all_rules(rules)
    create_rule()
    timeout = 0

    print('Opened Twitter Stream')
    while True:
        stream_connect(token, list_perms, name_ticker_pair, slug_ticker_pair)
        time.sleep(2 ** timeout)
        timeout += 1


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Caught exception, re-running main')
        telegrambot.send_msg('Exception:' + str(e))
        main()
    except:
        telegrambot.send_msg('SKUMLEON DEAD: please /reboot !!!')
