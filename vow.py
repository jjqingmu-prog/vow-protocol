#!/usr/bin/env python3
"""
/vow Protocol — Python implementation.

Validates, creates, and verifies agent vow documents.

Usage:
  python3 vow.py validate <vow.json>
  python3 vow.py create <vow.json>
  python3 vow.py check <vow.json> <action>
"""

import json
import sys
import os
import hashlib
import datetime
from typing import Optional

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema", "vow-v0.1.json")


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class VowValidationError(Exception):
    pass


def validate_vow(vow: dict, schema: dict) -> list:
    """
    Validate a vow document against the schema.
    Returns list of violations (empty = valid).
    """
    violations = []

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in vow or vow[field] is None or vow[field] == "":
            violations.append(f"Missing required field: {field}")

    # Check principles
    principles = vow.get("principles", [])
    if not principles:
        violations.append("At least one principle is required")
    else:
        for i, p in enumerate(principles):
            if "falsifier" not in p or not p["falsifier"]:
                violations.append(f"Principle {p.get('id', i)}: falsifier is required")
            if "statement" not in p or not p["statement"]:
                violations.append(f"Principle {p.get('id', i)}: statement is required")
            if "domain" not in p:
                violations.append(f"Principle {p.get('id', i)}: domain is required")

    # Check status
    valid_statuses = schema.get("properties", {}).get("status", {}).get("enum", [])
    if vow.get("status") not in valid_statuses:
        violations.append(f"Invalid status: {vow.get('status')}. Must be one of {valid_statuses}")

    # Check terms (if present)
    prohibitions = vow.get("prohibitions", [])
    for p in prohibitions:
        if "action" not in p:
            violations.append(f"Prohibition {p.get('id', '?')}: action is required")
        if "reason" not in p:
            violations.append(f"Prohibition {p.get('id', '?')}: reason is required")

    return violations


def create_vow(agent_id: str, agent_name: str, title: str,
               principles: list, prohibitions: Optional[list] = None,
               allowed_domains: Optional[list] = None,
               forbidden_domains: Optional[list] = None) -> dict:
    """Create a new vow document."""
    now = datetime.datetime.utcnow().isoformat() + "Z"
    vow_id_hash = hashlib.sha256(f"{agent_id}:{now}".encode()).hexdigest()[:16]
    
    doc = {
        "vow_id": f"vow-{vow_id_hash}",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "title": title,
        "version": "0.1.0",
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "principles": principles,
        "prohibitions": prohibitions or [],
        "allowed_domains": allowed_domains or [],
        "forbidden_domains": forbidden_domains or [],
        "signature": {
            "method": "null",
            "value": "",
            "signed_at": None,
            "verifier": ""
        },
        "revision_history": [
            {"timestamp": now, "event": "created", "by": "vow-protocol", "note": "Initial vow"}
        ],
        "extensions": {}
    }
    return doc


def check_action(vow: dict, action: str, domain: str = "action") -> dict:
    """
    Check if an action violates the vow.
    
    Returns:
        dict with verdict: 'allowed', 'warning', 'violation', or 'critical'
    """
    prohibitions = vow.get("prohibitions", [])
    principles = vow.get("principles", [])

    # Check prohibitions
    for p in prohibitions:
        if p["action"].lower() in action.lower():
            return {
                "verdict": p.get("severity", "violation"),
                "reason": p.get("reason", f"Prohibited action: {p['action']}"),
                "violated_by": "prohibition",
                "detail": p
            }

    # Check allowed_domains
    allowed = vow.get("allowed_domains", [])
    forbidden = vow.get("forbidden_domains", [])
    
    if domain in forbidden:
        return {
            "verdict": "violation",
            "reason": f"Domain '{domain}' is explicitly forbidden",
            "violated_by": "forbidden_domain"
        }
    
    if allowed and domain not in allowed:
        return {
            "verdict": "warning",
            "reason": f"Domain '{domain}' is not in the allowed domains list",
            "violated_by": "unlisted_domain"
        }

    return {
        "verdict": "allowed",
        "reason": "No prohibition or domain conflict found",
        "violated_by": None
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def cli():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 vow.py validate <vow.json>")
        print("  python3 vow.py create <agent_id> <agent_name> <title>")
        print("  python3 vow.py check <vow.json> <action>")
        return

    cmd = sys.argv[1]

    if cmd == "validate":
        path = sys.argv[2]
        with open(path) as f:
            vow = json.load(f)
        schema = load_schema()
        violations = validate_vow(vow, schema)
        if violations:
            print(f"❌ {len(violations)} violation(s):")
            for v in violations:
                print(f"   - {v}")
        else:
            print("✅ Vow is valid")

    elif cmd == "create":
        if len(sys.argv) < 5:
            print("Usage: python3 vow.py create <agent_id> <agent_name> <title>")
            return
        doc = create_vow(sys.argv[2], sys.argv[3], sys.argv[4],
                         [{"id": "principle-1", "statement": "Placeholder", "domain": "action", "falsifier": "TBD"}])
        print(json.dumps(doc, indent=2))

    elif cmd == "check":
        path = sys.argv[2]
        action = sys.argv[3]
        domain = sys.argv[4] if len(sys.argv) > 4 else "action"
        with open(path) as f:
            vow = json.load(f)
        result = check_action(vow, action, domain)
        verdict = result["verdict"]
        icon = {"allowed": "✅", "warning": "⚠️", "violation": "❌", "critical": "🚫"}
        print(f"{icon.get(verdict, '?')} {verdict.upper()}: {result['reason']}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    # Self-test on load
    cli()
