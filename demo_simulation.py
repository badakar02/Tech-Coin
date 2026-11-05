"""Demo script verifying Tachoin-Coin functionality:
- Multiple demo wallets
- Minting from reserve (validator action)
- Random transfers between wallets
- Block production & invariant checking
"""

from tachoin.client import TachoinClient
from tachoin.node import format_tach

def run_demo():
    print("Initializing TachoinClient with 4 validators...")
    client = TachoinClient(num_validators=4)
    
    print("\nInitial node status:")
    print(client.status())
    
    print("\nInitial supply:")
    print(client.supply())
    
    # Get validator wallets
    validator_wallets = client.validator_wallets()
    validator1 = validator_wallets[0]
    
    print(f"\nValidator 1 address: {validator1.address}")
    print(f"Validator 1 initial balance: {client.balance(validator1.address)['balance']}")
    
    # Create multiple demo wallets
    print("\nCreating 3 demo user wallets...")
    user1 = client.create_wallet()
    user2 = client.create_wallet()
    user3 = client.create_wallet()
    
    print(f"  User 1: {user1.address}")
    print(f"  User 2: {user2.address}")
    print(f"  User 3: {user3.address}")
    
    # Mint coins from uncirculated reserve to Validator 1 (validators only)
    print("\nMinting 50,000 TACH to Validator 1 from reserve...")
    mint_res = client.mint(validator1, "50000")
    print(f"  Mint result: {mint_res}")
    print(f"  Validator 1 balance after mint: {client.balance(validator1.address)['balance']}")
    
    # Produce a block to process transactions
    print("\nProducing block...")
    blocks = client.node.produce_blocks(1)
    print(f"  Produced block slot: {blocks[0].header.slot}")
    
    # Perform random transfers between wallets
    transfers = [
        (validator1, user1.address, "10000"),
        (validator1, user2.address, "5000"),
        (user1, user3.address, "2500"),
        (user2, user1.address, "1000"),
        (user3, user2.address, "500"),
    ]
    
    print("\nExecuting random transfers between wallets...")
    for sender, recipient_addr, amount in transfers:
        res = client.transfer(sender, recipient_addr, amount)
        print(f"  Transfer {amount} TACH from {sender.address[:10]}... to {recipient_addr[:10]}... -> Success: {res['success']}, New Balance: {res['new_balance']}")
    
    # Produce another block
    print("\nProducing block for transfers...")
    client.node.produce_blocks(1)
    
    # Check final balances
    print("\nFinal Balances:")
    print(f"  Validator 1: {client.balance(validator1.address)['balance']}")
    print(f"  User 1     : {client.balance(user1.address)['balance']}")
    print(f"  User 2     : {client.balance(user2.address)['balance']}")
    print(f"  User 3     : {client.balance(user3.address)['balance']}")
    
    # Verify invariants
    print("\nVerifying conservation invariants...")
    supply_ok = client.node.check_supply_invariant()
    balance_ok = client.node.check_balance_invariant()
    print(f"  Supply invariant OK : {supply_ok}")
    print(f"  Balance invariant OK: {balance_ok}")
    
    print("\nFinal Supply Status:")
    print(client.supply())
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    run_demo()
