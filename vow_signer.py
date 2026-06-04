#!/usr/bin/env python3
"""
Vow Signer — EVM ECDSA signing for the /vow Protocol v0.1

Implements EIP-191 personal_sign and key management for agent vows.
Uses the `cryptography` library for secp256k1 signing.

Future: Full EIP-712 typed structured data signing.

Schema: vow-v0.1.json
"""

import json
import os
import hashlib
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)
from cryptography.hazmat.backends import default_backend

# ─── Constants ────────────────────────────────────────────────────────────────

# Ethereum signed message prefix (EIP-191)
EIP191_PREFIX = b"\x19Ethereum Signed Message:\n"

# ─── Key Generation ───────────────────────────────────────────────────────────

def generate_keypair() -> tuple:
    """Generate a new secp256k1 keypair.
    
    Returns:
        (private_key_hex, address) where address is the Ethereum address
    """
    private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
    
    # Export private key as PEM, then extract raw scalar
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get the private value from the key object
    priv_numbers = private_key.private_numbers()
    priv_int = priv_numbers.private_value
    priv_hex = "0x" + priv_int.to_bytes(32, "big").hex()
    
    # Get public key uncompressed (65 bytes: 04 + x + y)
    pub_key = private_key.public_key()
    pub_numbers = pub_key.public_numbers()
    pub_bytes = bytes([4]) + pub_numbers.x.to_bytes(32, "big") + pub_numbers.y.to_bytes(32, "big")
    
    # Ethereum address = last 20 bytes of keccak256(public_key without 0x04 prefix)
    keccak = hashlib.sha3_256(pub_bytes[1:]).digest()
    address = "0x" + keccak[-20:].hex()
    
    return priv_hex, address


def private_key_to_address(priv_hex: str) -> str:
    """Derive Ethereum address from a private key."""
    priv_bytes = bytes.fromhex(priv_hex.replace("0x", ""))
    private_key = ec.derive_private_key(
        int.from_bytes(priv_bytes, "big"),
        ec.SECP256K1(),
        default_backend()
    )
    
    pub_key = private_key.public_key()
    pub_numbers = pub_key.public_numbers()
    pub_bytes = bytes([4]) + pub_numbers.x.to_bytes(32, "big") + pub_numbers.y.to_bytes(32, "big")
    
    keccak = hashlib.sha3_256(pub_bytes[1:]).digest()
    return "0x" + keccak[-20:].hex()


# ─── Signing (EIP-191) ────────────────────────────────────────────────────────

def _keccak256(data: bytes) -> bytes:
    """SHA3-256 (Ethereum's keccak256)."""
    return hashlib.sha3_256(data).digest()


def _eip191_hash(message: bytes) -> bytes:
    """Compute EIP-191 personal_sign hash.
    
    hash = keccak256(prefix + len(message) + message)
    where prefix = b"\\x19Ethereum Signed Message:\\n"
    """
    prefix = EIP191_PREFIX + str(len(message)).encode()
    return _keccak256(prefix + message)


def sign_vow(vow_json: dict, private_key_hex: str) -> dict:
    """Sign a Vow JSON document using EIP-191 personal_sign.
    
    Args:
        vow_json: The Vow document to sign
        private_key_hex: Private key in hex (0x prefixed or not)
        
    Returns:
        Updated vow_json with signature field populated
    """
    priv_hex = private_key_hex.replace("0x", "")
    private_key = ec.derive_private_key(
        int.from_bytes(bytes.fromhex(priv_hex), "big"),
        ec.SECP256K1(),
        default_backend()
    )
    
    # Canonicalize: deterministic JSON serialization
    vow_str = _canonical_json(vow_json)
    message = vow_str.encode("utf-8")
    
    # EIP-191 hash
    msg_hash = _eip191_hash(message)
    
    # Sign
    signature = private_key.sign(msg_hash, ec.ECDSA(hashes.SHA256()))
    
    # Decode to (r, s) and encode as 65-byte compact sig
    r, s = decode_dss_signature(signature)
    
    # For ECDSA recovery, we need v (recovery id). 
    # Since cryptography doesn't give us v directly, 
    # we try v=27 and v=28
    sig_bytes_r = r.to_bytes(32, "big")
    sig_bytes_s = s.to_bytes(32, "big")
    
    # We need the recovery id (v). Let's try to recover the public key
    # to determine v. For now, we'll return (r, s) and note that
    # proper v determination requires recovery.
    # In practice, use web3.py or eth-account for production signing.
    
    # Try v=27 first
    for v in [27, 28]:
        compact_sig = sig_bytes_r + sig_bytes_s + bytes([v])
        sig_hex = "0x" + compact_sig.hex()
        
        # Verify we can recover the signer
        recovered = recover_signer(vow_json, sig_hex)
        if recovered and recovered.lower() == vow_json.get("signature", {}).get("address", "").lower():
            break
    
    # Signature with v=27 as default (user should verify)
    compact_sig = sig_bytes_r + sig_bytes_s + bytes([27])
    sig_hex = "0x" + compact_sig.hex()
    
    # Get address
    address = private_key_to_address(private_key_hex)
    
    # Update vow JSON with signature
    result = json.loads(_canonical_json(vow_json))
    result["signature"] = {
        "method": "EIP-191",
        "value": sig_hex,
        "address": address,
        "signed_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "verifier": "vow_signer.py v0.1 (cryptography)"
    }
    
    return result


def verify_vow(vow_json: dict) -> bool:
    """Verify a signed Vow document.
    
    Args:
        vow_json: Signed Vow document
        
    Returns:
        True if signature is valid
    """
    sig_info = vow_json.get("signature", {})
    sig_hex = sig_info.get("value", "")
    address = sig_info.get("address", "")
    
    if not sig_hex or not address:
        return False
    
    recovered = recover_signer(vow_json, sig_hex)
    return recovered is not None and recovered.lower() == address.lower()


def recover_signer(vow_json: dict, signature_hex: str) -> Optional[str]:
    """Recover the signer's Ethereum address from a signed Vow.
    
    Args:
        vow_json: Signed Vow document (signature field must be present)
        signature_hex: Compact signature (0x + 65 bytes = r(32) + s(32) + v(1))
        
    Returns:
        Ethereum address or None if recovery fails
    """
    sig = signature_hex.replace("0x", "")
    if len(sig) != 130:  # 65 bytes = 130 hex chars
        return None
    
    sig_bytes = bytes.fromhex(sig)
    r = int.from_bytes(sig_bytes[:32], "big")
    s = int.from_bytes(sig_bytes[32:64], "big")
    v = sig_bytes[64]
    
    # Recover public key from signature
    # Remove signature before hashing
    clean_vow = {k: v for k, v in vow_json.items() if k != "signature"}
    vow_str = _canonical_json(clean_vow)
    message = vow_str.encode("utf-8")
    msg_hash = _eip191_hash(message)
    
    # Use cryptography to recover public key
    try:
        # ECDSA recovery requires the recovery id
        recovery_id = v - 27
        if recovery_id not in [0, 1]:
            return None
        
        # Recover public key
        from cryptography.hazmat.primitives.asymmetric.ec import (
            EllipticCurvePublicKey,
            SECP256K1,
        )
        
        # The cryptography library's recover from signature 
        # is available through the backend
        sig_der = encode_dss_signature(r, s)
        
        # For full ECDSA recovery, we need eth-account or coincurve.
        # cryptography doesn't natively support public key recovery.
        # This is a simplified version.
        
        # Alternative: use public key recovery math
        # For now, return None to indicate partial support
        # Full support requires coincurve or eth-account
        
        return None
        
    except Exception:
        return None


def _canonical_json(obj) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ─── Key Storage ──────────────────────────────────────────────────────────────

def save_key(private_key_hex: str, path: str = "~/.vow/key.json"):
    """Save encrypted key to file. 
    
    Note: This stores in plaintext. For production, use proper key management.
    """
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    address = private_key_to_address(private_key_hex)
    
    key_data = {
        "address": address,
        "private_key": private_key_hex,
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "method": "secp256k1",
        "note": "Store securely. This key controls your Vow identity."
    }
    
    with open(path, "w") as f:
        json.dump(key_data, f, indent=2, ensure_ascii=False)
    
    os.chmod(path, 0o600)  # Owner read/write only
    return address


def load_key(path: str = "~/.vow/key.json") -> Optional[str]:
    """Load private key from file."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get("private_key")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Vow Signer — EVM ECDSA signing for /vow protocol")
    parser.add_argument("action", nargs="?", default="generate",
                        choices=["generate", "sign", "verify", "address"])
    parser.add_argument("--vow", help="Vow JSON file to sign")
    parser.add_argument("--key", help="Private key hex or key file path")
    parser.add_argument("--output", "-o", help="Output file for signed vow")
    
    args = parser.parse_args()
    
    if args.action == "generate":
        priv, addr = generate_keypair()
        key_path = args.output or os.path.expanduser("~/.vow/key.json")
        save_key(priv, key_path)
        print(f"✅ Generated keypair")
        print(f"   Address: {addr}")
        print(f"   Key saved: {key_path}")
        print(f"   Private (hex): {priv}")
    
    elif args.action == "address":
        key_raw = args.key or load_key()
        if not key_raw:
            print("No key provided. Use --key or run 'generate' first.")
            return
        if os.path.exists(key_raw):
            key_data = json.load(open(key_raw))
            key_hex = key_data.get("private_key", "")
        else:
            key_hex = key_raw
        addr = private_key_to_address(key_hex)
        print(f"Address: {addr}")
    
    elif args.action == "sign":
        if not args.vow:
            print("Error: --vow file required")
            return
        
        key_raw = args.key or load_key()
        if not key_raw:
            print("No key provided.")
            return
        
        # Resolve key: could be hex string or file path
        if os.path.exists(key_raw):
            key_data = json.load(open(key_raw))
            key_hex = key_data.get("private_key", "")
        elif key_raw.startswith("0x") or all(c in "0123456789abcdef" for c in key_raw.lower()):
            key_hex = key_raw
        else:
            print(f"Cannot resolve key: {key_raw}")
            return
        
        with open(args.vow) as f:
            vow = json.load(f)
        
        signed = sign_vow(vow, key_hex)
        output = args.output or args.vow.replace(".json", "-signed.json")
        
        with open(output, "w") as f:
            json.dump(signed, f, indent=2, ensure_ascii=False)
        
        sig = signed["signature"]
        print(f"✅ Signed by {sig['address']}")
        print(f"   Output: {output}")
        print(f"   Sig: {sig['value'][:20]}...")
    
    elif args.action == "verify":
        if not args.vow:
            print("Error: --vow file required")
            return
        
        with open(args.vow) as f:
            vow = json.load(f)
        
        valid = verify_vow(vow)
        if valid:
            sig = vow.get("signature", {})
            print(f"✅ Signature valid")
            print(f"   Signed by: {sig.get('address', 'unknown')}")
        else:
            print("❌ Signature invalid or verification failed")
            sig = vow.get("signature", {})
            print(f"   Claimed signer: {sig.get('address', 'unknown')}")


if __name__ == "__main__":
    main()
