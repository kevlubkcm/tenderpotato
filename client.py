from typing import Tuple
import base64

import requests

from core import encode, TossPotato, decode, Status, Message


URL = 'http://localhost:46657'


class Client:
    def __init__(self):
        self.sequence = 0

    def send_message(self, msg) -> dict:
        msg = Message(msg, self.sequence)
        r = requests.get('%s/broadcast_tx_sync?tx=0x%s' % (URL, encode(msg).hex()))
        self.sequence += 1
        return r.json()

    def toss_potato(self, sender, secret, receiver):
        return self.send_message(TossPotato(sender, secret, receiver))


def query() -> Tuple[int, Status]:
    r = requests.get('%s/abci_query' % URL)
    res = r.json()['result']['response']
    return int(res['height']), decode(base64.b64decode(res['value'])).data
