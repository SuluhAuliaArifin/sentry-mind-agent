"""Solana devnet proof-of-report stub.

Strategy: store SHA256(report) as a memo on devnet using the MEMO program.
We keep this as a STUB so the MVP runs without solana-py installed. When you
enable it, install `solana` + `solders` and implement send_memo() below.

Public interface stays stable: anchor_hash(hash_hex) -> (ok, signature_or_msg).
"""
from __future__ import annotations
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def anchor_hash(hash_hex: str) -> tuple[bool, str]:
    if not settings.solana_enabled:
        return False, "solana disabled in config"
    # TODO(prod): implement with solders + solana memo program
    # from solders.keypair import Keypair
    # from solana.rpc.api import Client
    # client = Client(settings.solana_rpc_url)
    # ... build memo tx with hash_hex, sign, send, return signature
    logger.info("solana anchor stub for hash=%s", hash_hex[:16])
    return False, "stub: implement send_memo() to enable"
