from __future__ import annotations

import hashlib


def _compute_hash(*parts: str) -> str:
    """Compute SHA256 hash from concatenated parts."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_entry_hash(
    log_id: str,
    timestamp: str,
    actor_id: str,
    action: str,
    data_hash: str,
    previous_hash: str,
) -> str:
    """Compute the current hash for an audit log entry.

    Formula: SHA256(log_id|timestamp|actor_id|action|data_hash|previous_hash)
    """
    return _compute_hash(log_id, timestamp, actor_id, action, data_hash, previous_hash)


def verify_hash_chain(entries: list[dict]) -> tuple[bool, str]:
    """Verify the integrity of a hash chain.

    Iterates through entries (assumed sorted chronologically) and checks:
    1. Each current_hash matches SHA256(log_id|timestamp|actor_id|action|data_hash|previous_hash)
    2. Each entry's previous_hash matches the previous entry's current_hash

    Returns:
        (valid, message) tuple.
    """
    if not entries:
        return True, "No entries to verify"

    for i, entry in enumerate(entries):
        expected_hash = compute_entry_hash(
            log_id=str(entry.get("log_id", "")),
            timestamp=str(entry.get("timestamp", "")),
            actor_id=str(entry.get("actor_id", "")),
            action=str(entry.get("action_operation", "")),
            data_hash=str(entry.get("data_hash", "")),
            previous_hash=str(entry.get("previous_hash", "")),
        )

        current_hash = entry.get("current_hash", "")
        if current_hash != expected_hash:
            return False, (
                f"Hash mismatch at entry {i} (log_id={entry.get('log_id')}): "
                f"expected {expected_hash}, got {current_hash}"
            )

        # Check previous_hash linkage (skip first entry — genesis)
        if i > 0:
            prev_current_hash = entries[i - 1].get("current_hash", "")
            if entry.get("previous_hash", "") != prev_current_hash:
                return False, (
                    f"Chain broken at entry {i} (log_id={entry.get('log_id')}): "
                    f"previous_hash {entry.get('previous_hash')} does not match "
                    f"previous current_hash {prev_current_hash}"
                )

    return True, f"Hash chain verified: {len(entries)} entries intact"


def compute_merkle_root(entries: list[dict]) -> str:
    """Build a Merkle tree from the current_hashes of entries and return the root hash.

    If no entries, returns the SHA256 of an empty string.
    If one entry, returns that entry's current_hash.
    Otherwise, pairs up hashes and computes intermediate hashes level by level
    until a single root remains.
    """
    if not entries:
        return hashlib.sha256(b"").hexdigest()

    hashes: list[str] = [e["current_hash"] for e in entries if "current_hash" in e]

    if not hashes:
        return hashlib.sha256(b"").hexdigest()

    while len(hashes) > 1:
        next_level: list[str] = []
        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i + 1] if i + 1 < len(hashes) else left
            combined = _compute_hash(left, right)
            next_level.append(combined)
        hashes = next_level

    return hashes[0]
