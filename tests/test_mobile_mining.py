"""Tests for mobile participation check-in mining and AetherCoin backend."""

import unittest
from tachoin.client import TachoinClient
from tachoin.transaction import TachoinTx
from tachoin.config import MOBILE_MINING_REWARD, CHECKIN_COOLDOWN_SLOTS
from tachoin.node import format_tach

class MobileMiningTests(unittest.TestCase):
    def setUp(self):
        self.client = TachoinClient(num_validators=4)
        self.wallet = self.client.create_wallet()

    def test_mobile_checkin_rewards_user(self):
        """Verify that a mobile check-in transaction rewards the user with mobile mining coins."""
        node = self.client.node
        initial_balance = node.get_balance(self.wallet.address)
        self.assertEqual(initial_balance, 0)

        # Build and submit check-in transaction
        nonce = node.get_nonce(self.wallet.address)
        slot = node.get_current_slot() + 1
        tx = TachoinTx.build_checkin(self.wallet, nonce, slot)
        result = node.submit_transaction(tx)
        
        self.assertTrue(result.success, result.error)
        node.produce_blocks(1)

        # Verify balance increased by mobile mining reward
        new_balance = node.get_balance(self.wallet.address)
        self.assertEqual(new_balance, MOBILE_MINING_REWARD)

    def test_mobile_checkin_cooldown_enforced(self):
        """Verify that consecutive check-ins within the cooldown period are rejected."""
        node = self.client.node
        nonce = node.get_nonce(self.wallet.address)
        slot = node.get_current_slot() + 1

        # First check-in succeeds
        tx1 = TachoinTx.build_checkin(self.wallet, nonce, slot)
        res1 = node.submit_transaction(tx1)
        self.assertTrue(res1.success)
        node.produce_blocks(1)

        # Second immediate check-in should fail due to cooldown
        nonce2 = node.get_nonce(self.wallet.address)
        slot2 = node.get_current_slot() + 1
        tx2 = TachoinTx.build_checkin(self.wallet, nonce2, slot2)
        res2 = node.submit_transaction(tx2)
        self.assertFalse(res2.success)
        self.assertIn("cooldown active", res2.error)

if __name__ == "__main__":
    unittest.main()
