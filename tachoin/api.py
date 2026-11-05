"""Lightweight REST API backend for mobile (Android & iOS) AetherCoin clients.

Built using Python's standard library (zero third-party dependencies).
Provides endpoints for wallet management, balances, staking, transfers, and
mobile participation mining (check-in rewards).
"""

from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from tachoin.client import TachoinClient
from tachoin.wallet import TachoinWallet, is_valid_address
from tachoin.transaction import TachoinTx
from tachoin.node import format_tach, parse_tach

# Global singleton client for the node instance
_client: TachoinClient | None = None

def get_client() -> TachoinClient:
    global _client
    if _client is None:
        _client = TachoinClient(num_validators=4)
    return _client


class AetherAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for AetherCoin mobile API."""

    def _send_json(self, status: int, data: dict | list) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        client = get_client()

        try:
            if path == "/status":
                self._send_json(200, client.status())
            elif path == "/supply":
                self._send_json(200, client.supply())
            elif path == "/balance":
                addr = query.get("address", [None])[0]
                if not addr:
                    self._send_json(400, {"error": "missing 'address' parameter"})
                    return
                self._send_json(200, client.balance(addr))
            elif path == "/stake":
                addr = query.get("address", [None])[0]
                if not addr:
                    self._send_json(400, {"error": "missing 'address' parameter"})
                    return
                self._send_json(200, client.stake_info(addr))
            elif path == "/validators":
                self._send_json(200, {"validators": client.validator_addresses()})
            else:
                self._send_json(404, {"error": "endpoint not found"})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        client = get_client()

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        try:
            if path == "/wallet/create":
                wallet = client.create_wallet()
                passphrase = data.get("passphrase")
                response_data = {
                    "address": wallet.address,
                    "public_key": wallet.public_key_hex,
                }
                if passphrase:
                    # Save temporarily or return encrypted data structure
                    response_data["sealed"] = True
                else:
                    response_data["seed_hex"] = wallet.seed_hex
                    response_data["sealed"] = False
                self._send_json(200, response_data)

            elif path == "/tx/transfer":
                # Expects sender seed_hex (or wallet), recipient, amount
                seed_hex = data.get("seed_hex")
                to = data.get("to")
                amount = data.get("amount")
                if not seed_hex or not to or not amount:
                    self._send_json(400, {"error": "missing 'seed_hex', 'to', or 'amount'"})
                    return
                wallet = TachoinWallet.from_seed_hex(seed_hex)
                res = client.transfer(wallet, to, str(amount))
                client.node.produce_blocks(1)
                self._send_json(200, res)

            elif path == "/tx/checkin":
                # Mobile participation mining check-in
                seed_hex = data.get("seed_hex")
                if not seed_hex:
                    self._send_json(400, {"error": "missing 'seed_hex'"})
                    return
                wallet = TachoinWallet.from_seed_hex(seed_hex)
                node = client.node
                nonce = node.get_nonce(wallet.address)
                slot = node.get_current_slot() + 1
                tx = TachoinTx.build_checkin(wallet, nonce, slot)
                result = node.submit_transaction(tx)
                if result.success:
                    node.produce_blocks(1)
                self._send_json(200, {
                    "success": result.success,
                    "tx_hash": result.tx_hash,
                    "error": result.error,
                    "new_balance": format_tach(node.get_balance(wallet.address))
                })

            elif path == "/tx/stake":
                seed_hex = data.get("seed_hex")
                amount = data.get("amount")
                validator = data.get("validator", "")
                if not seed_hex or not amount:
                    self._send_json(400, {"error": "missing 'seed_hex' or 'amount'"})
                    return
                wallet = TachoinWallet.from_seed_hex(seed_hex)
                res = client.stake(wallet, str(amount), validator)
                client.node.produce_blocks(1)
                self._send_json(200, res)

            elif path == "/tx/unstake":
                seed_hex = data.get("seed_hex")
                amount = data.get("amount")
                validator = data.get("validator", "")
                if not seed_hex or not amount:
                    self._send_json(400, {"error": "missing 'seed_hex' or 'amount'"})
                    return
                wallet = TachoinWallet.from_seed_hex(seed_hex)
                res = client.unstake(wallet, str(amount), validator)
                client.node.produce_blocks(1)
                self._send_json(200, res)

            else:
                self._send_json(404, {"error": "endpoint not found"})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = HTTPServer((host, port), AetherAPIHandler)
    print(f"Aether Mobile API Server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print("Server stopped.")


if __name__ == "__main__":
    run_server()
