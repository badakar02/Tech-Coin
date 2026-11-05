"""Show addresses and balances of the 5 demo wallets."""

from tachoin.client import TachoinClient
from tachoin.wallet import TachoinWallet

def check_wallets():
    client = TachoinClient(num_validators=4)
    
    print("5 Demo Wallets:")
    for i in range(1, 6):
        path = f"wallet{i}.json"
        passphrase = f"passphrase{i}"
        try:
            wallet = TachoinWallet.load(path, passphrase)
            bal = client.balance(wallet.address)
            print(f"  Wallet {i}:")
            print(f"    Path    : {path}")
            print(f"    Address : {wallet.address}")
            print(f"    Balance : {bal['balance']}")
        except Exception as e:
            print(f"  Wallet {i} ({path}): Error loading - {e}")

if __name__ == "__main__":
    check_wallets()
