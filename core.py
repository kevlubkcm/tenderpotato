import pickle
from collections import namedtuple

TossPotato = namedtuple('TossPotato', ['sender', 'secret', 'receiver'])
Status = namedtuple('Status', ['players', 'losses', 'potato_holder'])


def encode(msg) -> bytes:
    return pickle.dumps(msg)


def decode(raw: bytes):
    return pickle.loads(raw)
