import base64
from enum import Enum

import requests

from core import encode_for_wire, TossPotato, decode, State, RawMessage, create_key_pair, sign_message, NewPlayer


URL = 'http://localhost:46657'


class BroadcastMode(Enum):
    async = 'broadcast_tx_async'
    sync = 'broadcast_tx_sync',
    commit = 'broadcast_tx_commit'


class Client:
    def __init__(self, server=URL):
        self.sequence = 0
        self.private_key, self.public_key = create_key_pair()
        self.server = server

    def send_message(self, msg, mode: BroadcastMode) -> dict:
        raw_msg = RawMessage(self.public_key, msg, self.sequence)
        msg = sign_message(raw_msg, self.private_key)
        r = requests.get('%s/%s?tx=0x%s' % (self.server, mode.value, encode_for_wire(msg).hex()))
        self.sequence += 1
        return r.json()

    def toss_potato(self, receiver, mode=BroadcastMode.async):
        return self.send_message(TossPotato(receiver), mode)

    def enter_game(self):
        return self.send_message(NewPlayer(), BroadcastMode.commit)


def query() -> State:
    r = requests.get('%s/abci_query' % URL)
    res = r.json()['result']['response']
    return decode(base64.b64decode(res['value'])).data
