from binance.client import Client, BinanceAPIException

# 44196397 = @elonmusk en
# 1364153410774323201 = @GortBerend
# https://tweeterid.com/

pick_twitter_account = 'Staging'

if pick_twitter_account == 'Staging':
    twitter_id = 1389249951910268935
    callbackRate = 1
    leverage = 20
    position_ratio = 0.01
if pick_twitter_account == 'Production':
    twitter_id = 1364153410774323201
    callbackRate = 1
    leverage = 20
    position_ratio = 0.01
if pick_twitter_account == 'Elon':
    twitter_id = 44196397
    callbackRate = 1
    leverage = 20
    position_ratio = 0.5

DEFAULT_FNAME = "auth_staging.txt"


class CredentialHandler(object):
    """Contains all credentials
    """

    def __init__(self, auth_fname=DEFAULT_FNAME):
        """Constructor method
        """
        self.load_credentials(auth_fname)

    def load_credentials(self, auth_fname=DEFAULT_FNAME):
        """Load credentials from auth.txt file. A typical file looks
        as follows:
        twitter key
        twitter secret
        binance key
        binance secret
        coinmarketcap_key
        :param auth_fname: path + filename to auth.txt file
        """

        try:
            print("trying")
            with open(auth_fname, 'r') as f:
                content = [x.replace('\n', '').replace(' ', '')
                           for x in f.readlines()]

            self._twitter_key = content[0]
            self._twitter_secret = content[1]
            self._binance_key = content[2]
            self._binance_secret = content[3]
            self._coinmarketcap_key = content[4]
            self._telegram_key = content[5]
            self._have_credentials = True

        except:
            print("ERROR. Fill the file '{}'".format(auth_fname))
            print("An empty one has been created for you")
            print("Content: (5 lines)")
            print("<twitter key>")
            print("<twitter secret>")
            print("<binance key>")
            print("<binance secret>")
            print("<coinmarketcap_key>")

            with open(auth_fname, 'w') as f:
                f.write('')

            # TODO: rewrite as a proper FnF exception
            self.__have_credentials = False
            # raise Exception("File not found")


authenticate = CredentialHandler()
