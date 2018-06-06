from typing import Tuple
import pickle
from collections import namedtuple


import nacl.encoding
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
import nacl.hash


RawMessage = namedtuple('RawMessage', ['sender', 'data', 'sequence'])
Message = namedtuple('Message', ['sender', 'data', 'sequence', 'signature'])
NewPlayer = namedtuple('NewPlayer', [])
TossPotato = namedtuple('TossPotato', ['receiver'])
State = namedtuple('State', ['players', 'losses', 'potato_holder', 'blow_up_height', 'last_block_height'])
ENCODING = nacl.encoding.Base64Encoder


class SignatureError(Exception):
    pass


# TODO: pickles are not a safe serialization method
def encode_for_wire(msg: Message) -> bytes:
    return pickle.dumps(msg)


def encode_for_signature(msg: RawMessage) -> bytes:
    return pickle.dumps(msg)


def state_hash(state: State) -> bytes:
    msg = pickle.dumps(state)
    return nacl.hash.sha256(msg, encoder=ENCODING)


def decode(raw: bytes) -> Message:
    res = pickle.loads(raw)
    if not validate_signature(res):
        raise SignatureError
    return res


def sign_message(raw_message: RawMessage, private_key: SigningKey) -> Message:
    to_sign = encode_for_signature(raw_message)
    signature = private_key.sign(to_sign).signature
    return Message(raw_message.sender, raw_message.data, raw_message.sequence, signature)


def validate_signature(value: Message) -> bool:
    verify_key = nacl.signing.VerifyKey(value.sender, ENCODING)
    try:
        raw_message = RawMessage(value.sender, value.data, value.sequence)
        raw_message = encode_for_signature(raw_message)
        verify_key.verify(raw_message, value.signature)
    except BadSignatureError:
        return False

    return True


def create_key_pair() -> Tuple[SigningKey, VerifyKey]:
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    return signing_key, verify_key.encode(ENCODING)
