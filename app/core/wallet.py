from solana.keypair import Keypair
import base58

class Wallet:
    def __init__(self, secret):
        self.keypair = Keypair.from_secret_key(base58.b58decode(secret))

    def sign(self, tx):
        tx.sign(self.keypair)
        return tx