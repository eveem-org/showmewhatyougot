from web3 import Web3
from web3 import HTTPProvider


def read_address(smart_contract_address, index):
    web3 = Web3(HTTPProvider("https://mainnet.infura.io/"))
    return '0x'+web3.eth.getStorageAt( Web3.toChecksumAddress(smart_contract_address),index).hex()[26:66]
