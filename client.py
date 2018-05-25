import base64

import requests

from core import encode, TossPotato, decode, Status


URL = 'http://localhost:46657'


def send_message(msg: TossPotato) -> dict:
    r = requests.get('%s/broadcast_tx_commit?tx=0x%s' % (URL, encode(msg).hex()))
    return r.json()


def toss_potato(sender, secret, receiver):
    return send_message(TossPotato(sender, secret, receiver))


def query() -> Status:
    r = requests.get('%s/abci_query' % URL)
    return decode(base64.b64decode(r.json()['result']['response']['value']))
