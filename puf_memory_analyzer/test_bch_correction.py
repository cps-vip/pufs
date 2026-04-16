"""
BCH Fuzzy Extractor using SRAM PUF data.

Enrollment: average all 40 trials via majority vote → clean reference PUF
Reproduction: take a single noisy trial, XOR with helper data, BCH-correct back
              to the enrolled secret.

Key bchlib API note:
  bch.decode(data, recv_ecc) → nerr  (returns -1 on uncorrectable failure)
  bch.correct(data, ecc)     → None  (always None; applies fixes in-place)
  The correct workflow is decode() first to get nerr, then correct() to apply.
"""

import sys
import os
import random
from pathlib import Path
import bchlib

# ---------------------------------------------------------------------------
# Configuration (Simplified for m=8)
# ---------------------------------------------------------------------------
BCH_T   = 64          # errors to correct
BCH_M   = 10           # m parameter for BCH code which dictates the block size we use
BOARD   = "1724_SRAM4_data"
SECRET  = b"This is a secret" # depends on our payload size

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_trial(path: Path) -> list[int]:
    """Return a list of ints (0/1) from a .bits file."""
    return [int(ch) for ch in path.read_text().strip() if ch in "01"]


def load_all_trials(board: str, max_trials: int = 40) -> list[list[int]]:
    base = Path(__file__).parent / "bits_output" / board
    if not base.exists():
        raise FileNotFoundError(f"Data directory not found: {base}")

    trials = []
    for i in range(1, max_trials + 1):
        p = base / f"trial{i}.bits"
        if p.exists():
            trials.append(load_trial(p))
        else:
            print(f"  [warn] {p.name} missing – stopping at {len(trials)} trials")
            break

    if not trials:
        raise RuntimeError("No trial files loaded.")
    return trials


def majority_vote(trials: list[list[int]]) -> list[int]:
    """
    Bit-wise majority vote across all trials.
    Each output bit is 1 iff more than half the trials show a 1 at that position.
    This is the 'averaging' step that removes random thermal noise.
    """
    n_bits   = min(len(t) for t in trials)
    n_trials = len(trials)
    return [1 if sum(t[i] for t in trials) > n_trials / 2 else 0
            for i in range(n_bits)]


def bits_to_bytes(bits: list[int], n_bits: int) -> bytes:
    """
    Pack exactly n_bits from `bits` into bytes, MSB-first.
    Truncates or zero-pads as needed.
    """
    buf = bytearray((n_bits + 7) // 8)
    for i in range(n_bits):
        if i < len(bits) and bits[i]:
            buf[i // 8] |= 0x80 >> (i % 8)
    return bytes(buf)

def count_bit_errors(a: list[int], b: list[int], n: int) -> int:
    return sum(a[i] != b[i] for i in range(min(n, len(a), len(b))))

def bits_to_bytes(bits: list[int], n_bits: int) -> bytes:
    """Pack n_bits MSB-first. Toggle to (0x01 << (i % 8)) if C library is LSB."""
    buf = bytearray((n_bits + 7) // 8)
    for i in range(min(n_bits, len(bits))):
        if bits[i]:
            buf[i // 8] |= 0x80 >> (i % 8)
    return bytes(buf)

def enroll(bch, ref_bits, secret):
    n_total = (bch.n + 7) // 8
    ecc_b = bch.ecc_bytes
    k_bytes = n_total - ecc_b

    # Zero-pad secret to fit the exact payload size
    payload = secret + b"\x00" * (k_bytes - len(secret))
    ecc = bch.encode(payload)
    codeword = payload + ecc 

    puf_ref = bits_to_bytes(ref_bits, bch.n)
    return bytes(p ^ c for p, c in zip(puf_ref, codeword))

def reproduce(bch, noisy_bits, helper, secret_len):
    n_total = (bch.n + 7) // 8
    k_bytes = n_total - bch.ecc_bytes

    puf_noisy = bits_to_bytes(noisy_bits, bch.n)
    noisy_cw = bytearray(n ^ h for n, h in zip(puf_noisy, helper))

    msg, ecc = noisy_cw[:k_bytes], noisy_cw[k_bytes:]
    nerr = bch.decode(msg, ecc)
    
    if nerr >= 0:
        bch.correct(msg, ecc)
        return bytes(msg[:secret_len]), nerr
    return None, -1

def main():
    trials = load_all_trials(BOARD,40)
    ref = majority_vote(trials)
    bch = bchlib.BCH(BCH_T, m=BCH_M)
    
    k_bytes = (bch.n + 7) // 8 - bch.ecc_bytes
    current_secret = SECRET[:k_bytes]
    
    print(f"BCH(n={bch.n}, k_bytes={k_bytes}, t={BCH_T})")
    print(f"Testing with secret: {current_secret}")

    helper = enroll(bch, ref, current_secret)
    
    passed = 0
    for idx, trial in enumerate(trials):
        recovered, nerr = reproduce(bch, trial, helper, len(current_secret))
        ber = count_bit_errors(ref, trial, bch.n)
        
        if recovered == current_secret:
            print(f"  Trial {idx+1:02d}: PASS (Errors: {nerr}, Physical Diff: {ber})")
            passed += 1
        else:
            print(f"  Trial {idx+1:02d}: FAIL (Physical Diff: {ber} vs Capacity: {BCH_T})")

    print(f"\nResult: {passed}/{len(trials)} passed.")

if __name__ == "__main__":
    main()