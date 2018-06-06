import abc
from typing import Tuple, Dict, List
from pickle import UnpicklingError

from abci import (
    ABCIServer,
    BaseApplication,
    ResponseInfo,
    ResponseCheckTx, ResponseDeliverTx,
    ResponseQuery,
    ResponseCommit,
    ResponseEndBlock,
    CodeTypeOk,
)

from core import (
    decode, State, encode_for_wire, TossPotato, Message, SignatureError, NewPlayer, RawMessage, sign_message,
    create_key_pair, state_hash
)


class EndBlockHandler(abc.ABC):
    @abc.abstractmethod
    def end_block(self, state: State, req) -> Tuple[State, ResponseEndBlock]:
        pass


class FixedBlowUp(EndBlockHandler):
    def __init__(self, blow_up_inc: int):
        self.blow_up_inc = blow_up_inc

    def end_block(self, state: State, req) -> Tuple[State, ResponseEndBlock]:
        if req.height == state.blow_up_height:
            losses = list(state.losses)
            losses[state.potato_holder] += 1
            losses = tuple(losses)
            blowup = state.blow_up_height + self.blow_up_inc
        elif state.blow_up_height is not None and state.blow_up_height < 0:  # New game
            losses = state.losses
            blowup = state.last_block_height + self.blow_up_inc
        else:
            losses = state.losses
            blowup = state.blow_up_height

        return State(state.players, losses, state.potato_holder, blowup, req.height), ResponseEndBlock()


class MessageHandler(abc.ABC):
    def __init__(self, message_type: type):
        self.message_type = message_type

    @abc.abstractmethod
    def deliver_tx(self, state: State, message: Message) -> Tuple[State, ResponseDeliverTx]:
        pass


class TossPotatoHandler(MessageHandler):
    def __init__(self):
        super().__init__(TossPotato)

    def deliver_tx(self, state: State, message: Message) -> Tuple[State, ResponseDeliverTx]:
        assert type(message.data) is TossPotato

        if message.sender != state.players[state.potato_holder]:
            return state, ResponseDeliverTx(code=1, info='Not holding the potato')

        if message.data.receiver not in state.players:
            return state, ResponseDeliverTx(code=1, info='Target player does not exist')

        idx = state.players.index(message.data.receiver)
        return State(
            state.players,
            state.losses,
            idx,
            state.blow_up_height,
            state.last_block_height
        ), ResponseDeliverTx(code=0)


class NewPlayerHandler(MessageHandler):
    def __init__(self):
        super().__init__(NewPlayer)

    def deliver_tx(self, state: State, message: Message) -> Tuple[State, ResponseDeliverTx]:
        if message.sender in state.players:
            return state, ResponseDeliverTx(code=1, info='Already playing')

        if len(state.players) == 1:  # We have enough players to start
            blowup = -1
            holder = 1
        else:
            blowup = state.blow_up_height
            holder = state.potato_holder

        return State(
            state.players + (message.sender, ),
            state.losses + (0, ),
            holder,
            blowup,
            state.last_block_height,
        ), ResponseDeliverTx(code=0)


class TenderPotato(BaseApplication):
    def __init__(self, handlers: List[MessageHandler], end_block: EndBlockHandler):
        self.sequence = 0
        self.private_key, self.public_key = create_key_pair()

        self.state = State(tuple(), tuple(), None, None, 0)

        self.handlers: Dict[type, MessageHandler] = {h.message_type: h for h in handlers}
        self.end_block_handler = end_block

    def info(self, req) -> ResponseInfo:
        r = ResponseInfo()
        r.version = "1.0"
        r.last_block_height = 0
        r.last_block_app_hash = b''
        return r

    def check_tx(self, tx: bytes) -> ResponseCheckTx:
        try:
            message = decode(tx)
        except (SignatureError, TypeError, UnpicklingError) as e:
            return ResponseCheckTx(code=1, info='%s' % type(e))

        message_type = type(message.data)
        handler = self.handlers.get(message_type)
        if handler is None:
            return ResponseCheckTx(code=1, info='Unrecognized Type: %s' % message_type)

        return ResponseCheckTx(code=0)

    def deliver_tx(self, tx: bytes) -> ResponseDeliverTx:
        message = decode(tx)
        self.state, resp = self.handlers[type(message.data)].deliver_tx(self.state, message)
        return resp

    def query(self, req) -> ResponseQuery:
        message = sign_message(RawMessage(self.public_key, self.state, self.sequence), self.private_key)
        res = encode_for_wire(message)
        self.sequence += 1
        return ResponseQuery(code=CodeTypeOk, value=res, height=self.state.last_block_height)

    def end_block(self, req) -> ResponseEndBlock:
        self.state, resp = self.end_block_handler.end_block(self.state, req)
        return resp

    def commit(self) -> ResponseCommit:
        return ResponseCommit(data=state_hash(self.state))


if __name__ == '__main__':
    tp = TenderPotato(
        [
            NewPlayerHandler(),
            TossPotatoHandler(),
        ],
        FixedBlowUp(100),
    )
    app = ABCIServer(app=tp)
    app.run()
