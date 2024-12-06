from bit.network import NetworkAPI

def broadcast_transaction(signed_tx_hex: str):
    NetworkAPI.broadcast_tx(signed_tx_hex)
