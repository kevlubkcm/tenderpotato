import pickle
from collections import namedtuple

Message = namedtuple('Message', ['data', 'sequence'])
TossPotato = namedtuple('TossPotato', ['sender', 'secret', 'receiver'])
Status = namedtuple('Status', ['players', 'losses', 'potato_holder'])


def encode(msg: Message) -> bytes:
    return pickle.dumps(msg)


def decode(raw: bytes) -> Message:
    return pickle.loads(raw)
