from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import config


coinmarketcap_key = config.authenticate._coinmarketcap_key

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': coinmarketcap_key,
}

session = Session()
session.headers.update(headers)


def ticker_aggregator():
    url = ' https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'
    try:
        with open("coinmarketcapdata.json", "r") as read_file:
            cmc_data = json.load(read_file)
            print('data loaded from directory')
    except(FileNotFoundError):
        try:
            response = session.get(url)
            cmc_data = json.loads(response.text)
            with open('coinmarketcapdata.json', 'w') as json_file:
                json.dump(cmc_data, json_file)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
    slug_ticker_pair = {ticker['slug'].replace(' ', '').lower() : ticker['symbol'] for ticker in cmc_data['data']}
    name_ticker_pair = {ticker['name'].replace(' ', '').lower() : ticker['symbol'] for ticker in cmc_data['data']}
    return name_ticker_pair,slug_ticker_pair



