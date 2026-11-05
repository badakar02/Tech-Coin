"""Script to mint coins and have the 5 demo wallets compete with transactions."""

import random
from tachoin.client import TachoinClient
from tachoin.wallet import TachoinWallet
from tachoin.node import format_tach

def main():
    print("Initializing TachoinClient with 4 validators...")
    client = TachoinClient(num_validators=4)
    validator = client.validator_wallets()[0]
    
    print(f"Validator address: {validator.address}")
    print(f"Initial supply: {client.supply()}")
    
    # Load the 5 demo wallets
    wallets = []
    for i in range(1, 6):
        w = TachoinWallet.load(f"wallet{i}.json", f"passphrase{i}")
        wallets.append(w)
        print(f"Loaded Wallet {i}: {w.address}")
        
    # Mint 1,000,000 TACH from reserve to validator
    print("\nMinting 1,000,000 TACH to validator from uncirculated reserve...")
    mint_res = client.mint(validator, "1000000")
    print(f"  Mint result: {mint_res['success']} - New balance: {mint_res['new_balance']}")
    client.node.produce_blocks(1)
    
    # Seed the 5 wallets with 100,000 TACH each from validator
    print("\nSeeding the 5 wallets with 100,000 TACH each...")
    for idx, w in enumerate(wallets):
        res = client.transfer(validator, w.address, "100000")
        print(f"  Seeded Wallet {idx+1}: Success = {res['success']}, Balance = {res['new_balance']}")
    
    client.node.produce_blocks(1)
    
    # Let wallets compete with random transactions over 5 rounds
    print("\nStarting competition rounds between the 5 wallets...")
    for round_num in range(1, 6):
        print(f"\n--- Round {round_num} ---")
        # Each wallet makes 2 random transactions to other wallets
        for idx, sender in enumerate(wallets):
            # Pick a different recipient
            recipient = random.choice([w for w in wallets if w.address != sender.address])
            amount = str(random.randint(100, 5000))
            
            res = client.transfer(sender, recipient.address, amount)
            if res['success']:
                print(f"  Wallet {idx+1} sent {amount} TACH -> Balance: {res['new_balance']}")
            else:
                print(f"  Wallet {idx+1} transfer failed: {res['error']}")
                
        # Produce a block for the round
        block = client.node.produce_blocks(1)[0]
        print(f"  Block #{block.header.slot} produced.")
        
    # Final balances and invariants check
    print("\n========================================")
    print("Final Competition Standings & Balances:")
    print("========================================")
    for idx, w in enumerate(wallets):
        bal = client.balance(w.address)
        stk = client.stake_info(w.address)
        print(f"  Wallet {idx+1} ({w.address[:10]}...):")
        print(f"    Balance : {bal['balance']}")
        print(f"    Staked  : {stk['staked']}")
        
    print("\nVerifying Invariants:")
    supply_ok = client.node.check_supply_invariant()
    balance_ok = client.node.check_balance_invariant()
    print(f"  Supply invariant OK : {supply_ok}")
    print(f"  Balance invariant OK: {balance_ok}")
    print(f"  Final Supply Status : {client.supply()}")

if __name__ == "__main__":
    main()
