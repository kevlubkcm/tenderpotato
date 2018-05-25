from typing import Optional

from abci import (
    ABCIServer,
    BaseApplication,
    ResponseInfo,
    ResponseInitChain,
    ResponseCheckTx, ResponseDeliverTx,
    ResponseQuery,
    ResponseCommit,
    ResponseEndBlock,
    CodeTypeOk,
)

from core import decode, Status, encode, TossPotato


BLOW_UP_INC = 100


class SimpleCounter(BaseApplication):
    def __init__(self):
        self.players = tuple()
        self.secrets = tuple()
        self.potato_holder = None
        self.blow_up_height = None
        self.losses = tuple()
        self.last_block_height = 0

    def __index_of(self, player):
        if player in self.players:
            return self.players.index(player)

    def status(self):
        return Status(self.players, self.losses, self.players[self.potato_holder])

    def info(self, req) -> ResponseInfo:
        r = ResponseInfo()
        r.version = "1.0"
        r.last_block_height = 0
        r.last_block_app_hash = b''
        return r

    def init_chain(self, req) -> ResponseInitChain:
        """Set initial state on first run"""
        self.players = ('a', 'b', 'c')
        self.secrets = ('aa', 'bb', 'cc')
        assert len(self.players) == len(self.secrets)

        self.losses = (0, ) * len(self.players)
        self.potato_holder = 0
        self.blow_up_height = BLOW_UP_INC
        self.last_block_height = 0
        return ResponseInitChain()

    def check_toss(self, value: TossPotato) -> Optional[str]:
        if value.sender == value.receiver:
            return 'Cannot send to self'

        sender_index = self.__index_of(value.sender)
        if sender_index is None:
            return 'Sender does not exist'

        if sender_index != self.potato_holder:
            return 'Sender does not hold the potato'

        if self.__index_of(value.receiver) is None:
            return 'Receiver does not exist'

        if value.secret != self.secrets[self.potato_holder]:
            return 'Invalid signature'

    def check_tx(self, tx) -> ResponseCheckTx:
        value = decode(tx)
        check = self.check_toss(value)
        if check is not None:
            return ResponseCheckTx(code=1, info=check)
        else:
            return ResponseCheckTx(code=CodeTypeOk)

    def deliver_tx(self, tx) -> ResponseDeliverTx:
        value = decode(tx)
        check = self.check_toss(value)
        if check is not None:
            return ResponseDeliverTx(code=1, info=check)

        self.potato_holder = self.__index_of(value.receiver)
        return ResponseDeliverTx(code=CodeTypeOk)

    def query(self, req) -> ResponseQuery:
        v = encode(self.status())
        return ResponseQuery(code=CodeTypeOk, value=v, height=self.last_block_height)

    def end_block(self, req) -> ResponseEndBlock:
        if req.height == self.blow_up_height:
            self.blow_up_height += BLOW_UP_INC
            losses = list(self.losses)
            losses[self.potato_holder] += 1
            self.losses = tuple(losses)

        self.last_block_height = req.height
        return ResponseEndBlock()

    def commit(self) -> ResponseCommit:
        return ResponseCommit(data=encode(self.status()))


if __name__ == '__main__':
    # Create the app
    app = ABCIServer(app=SimpleCounter())
    # Run it
    app.run()
