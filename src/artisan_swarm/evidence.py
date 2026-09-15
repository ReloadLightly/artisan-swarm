"""Evidence ledger integrity checks, distinct from semantic source review.

These checks establish that citations and epistemic labels are present. They do
not establish that a source actually supports a claim or grants permission.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

CLAIM_TYPES = {"documented_fact", "interpretation", "assumption", "unknown"}


def _text(record: dict[str, Any], key: str, where: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{key}: expected nonempty string")
    return value


def _records(value: Any, where: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{where}: expected nonempty array")
    result = {}
    for record in value:
        if not isinstance(record, dict):
            raise ValueError(f"{where}: each record must be an object")
        identifier = _text(record, "id", where)
        if identifier in result:
            raise ValueError(f"{where}: duplicate ID {identifier}")
        result[identifier] = record
    return result


def _references(value: Any, available: dict[str, Any], where: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{where}: expected string array")
    if len(set(value)) != len(value):
        raise ValueError(f"{where}: duplicate references")
    missing = set(value) - set(available)
    if missing:
        raise ValueError(f"{where}: missing references {sorted(missing)}")


def validate_dossier(dossier: dict[str, Any]) -> None:
    """Require retrievable provenance and typed claims; do not infer support."""
    if not isinstance(dossier, dict):
        raise ValueError("dossier: expected object")
    sources = _records(dossier.get("sources"), "sources")
    claims = _records(dossier.get("claims"), "claims")
    for identifier, source in sources.items():
        where = f"sources.{identifier}"
        for key in ("title", "publisher", "url", "retrieved_at", "locator"):
            _text(source, key, where)
        url = urlparse(source["url"])
        if url.scheme not in {"https", "http"} or not url.netloc:
            raise ValueError(f"{where}.url: expected retrievable HTTP(S) source")
        if "publication_date" not in source or (source["publication_date"] is not None
                and (not isinstance(source["publication_date"], str) or not source["publication_date"].strip())):
            raise ValueError(f"{where}.publication_date: expected date string or explicit null")
        try:
            retrieved = datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{where}.retrieved_at: invalid ISO timestamp") from exc
        if retrieved.tzinfo is None:
            raise ValueError(f"{where}.retrieved_at: timestamp needs timezone")
    for identifier, claim in claims.items():
        where = f"claims.{identifier}"
        for key in ("text", "type", "locator"):
            _text(claim, key, where)
        if claim["type"] not in CLAIM_TYPES:
            raise ValueError(f"{where}.type: unsupported epistemic type")
        _references(claim.get("source_ids"), sources, f"{where}.source_ids")
        if claim["type"] in {"documented_fact", "interpretation"} and not claim["source_ids"]:
            raise ValueError(f"{where}: factual and interpretive claims require a source")
        for key in ("contradiction_source_ids",):
            if key in claim:
                _references(claim[key], sources, f"{where}.{key}")
        for key in ("supports_claim_ids", "contradicts_claim_ids"):
            if key in claim:
                _references(claim[key], claims, f"{where}.{key}")
                if identifier in claim[key]:
                    raise ValueError(f"{where}.{key}: self-reference is invalid")


def validate_case(case: dict[str, Any], dossier: dict[str, Any]) -> None:
    """Every externally fixed case fact has a claim or explicit scenario basis."""
    if not isinstance(case, dict):
        raise ValueError("case: expected object")
    for key in ("id", "title", "description"):
        _text(case, key, "case")
    facts = case.get("facts")
    if not isinstance(facts, dict) or not facts:
        raise ValueError("case.facts: expected nonempty object")
    for key, value in facts.items():
        if not isinstance(key, str) or not key.strip() or not (value is None or isinstance(value, bool)):
            raise ValueError("case.facts: expected named true, false, or null values")
    references = case.get("fact_claims")
    if not isinstance(references, dict) or set(references) != set(facts):
        raise ValueError("case.fact_claims: exactly one mapping per case fact required")
    claims = _records(dossier.get("claims"), "claims")
    for key, ids in references.items():
        _references(ids, claims, f"case.fact_claims.{key}")
        if not ids:
            raise ValueError(f"case.fact_claims.{key}: fact needs claim or scenario reference")
        if facts[key] is not None and all(claims[cid]["type"] == "unknown" for cid in ids):
            raise ValueError(f"case.facts.{key}: an unknown claim cannot establish a boolean fact")


def apply_disruption(case: dict[str, Any], disruption: dict[str, Any]) -> dict[str, Any]:
    """Copy a case and apply an explicitly hypothetical, finite fact change."""
    if not isinstance(disruption, dict) or disruption.get("label") != "hypothetical":
        raise ValueError("disruption must have label='hypothetical'")
    for key in ("id", "description"):
        _text(disruption, key, "disruption")
    changes = disruption.get("changes")
    if not isinstance(changes, dict) or not changes:
        raise ValueError("disruption.changes: expected nonempty object")
    references = disruption.get("fact_claims")
    if not isinstance(references, dict) or set(references) != set(changes):
        raise ValueError("disruption.fact_claims: exactly one mapping per changed fact required")
    for key, ids in references.items():
        if (not isinstance(ids, list) or not ids or
                any(not isinstance(cid, str) or not cid.strip() for cid in ids) or
                len(set(ids)) != len(ids)):
            raise ValueError(f"disruption.fact_claims.{key}: expected nonempty unique claim IDs")
    revised = deepcopy(case)
    facts = revised.get("facts", {})
    for key, value in changes.items():
        if key not in facts:
            raise ValueError(f"disruption.changes: unknown fact {key}")
        if not (value is None or isinstance(value, bool)):
            raise ValueError(f"disruption.changes.{key}: expected boolean or null")
        facts[key] = value
        revised.setdefault("fact_claims", {})[key] = list(references[key])
    revised["id"] = f"{case['id']}::{disruption['id']}"
    revised["applied_disruption"] = deepcopy(disruption)
    return revised
