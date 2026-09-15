"""Frozen M1 JSON schemas and a dependency-free, fail-closed validator.

Only the deliberately small JSON Schema subset used by this application is
supported. Unknown schema keywords are errors rather than ignored checks.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

SCHEMA_VERSION = "1.0"
ENGINE_VERSION = "m1-1"


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def _text() -> dict[str, Any]:
    return {"type": "string", "minLength": 1}


def _refs() -> dict[str, Any]:
    return {"type": "array", "items": _text(), "uniqueItems": True}


def _identifier() -> dict[str, Any]:
    return {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]*$", "maxLength": 120}


def _identifiers() -> dict[str, Any]:
    return {"type": "array", "items": _identifier(), "uniqueItems": True}


def program_schema() -> dict[str, Any]:
    """Return a fresh strict structured-output schema for strategy programs."""
    test = _object({"fact": _text(), "equals": {"type": "boolean"}})
    prerequisite = _object({"fact": _text(), "equals": {"type": "boolean"},
                            "reason": _text()})
    action = _object({
        "id": _identifier(), "title": _text(), "description": _text(),
        "kind": {"type": "string", "enum": ["preparation", "negotiation", "execution", "evaluation"]},
        "when": _object({"operator": {"type": "string", "enum": ["all", "any"]},
                         "tests": {"type": "array", "items": test, "maxItems": 32}}),
        "prerequisites": {"type": "array", "items": prerequisite, "maxItems": 32},
        "depends_on": _identifiers(), "evidence_refs": _refs(), "assumption_refs": _refs(),
        "reconsideration_triggers": _refs(),
        "fallbacks": {"type": "array", "items": _object({"action_id": _identifier(), "reason": _text()})},
    })
    return _object({
        "schema_version": {"type": "string", "const": SCHEMA_VERSION},
        "engine_version": {"type": "string", "const": ENGINE_VERSION},
        "id": _identifier(), "title": _text(),
        "architecture": {"type": "string", "enum": ["centralized", "federated", "project_specific"]},
        "rationale": _text(), "parent_ids": _identifiers(), "feedback_ids": _identifiers(),
        "evidence_refs": _refs(), "assumption_refs": _refs(),
        "actions": {"type": "array", "items": action, "minItems": 1, "maxItems": 24},
    })


_SUPPORTED = {"type", "properties", "required", "additionalProperties", "items", "enum",
              "const", "minItems", "maxItems", "uniqueItems", "minLength", "maxLength",
              "pattern", "minimum", "maximum", "description", "title", "$schema", "$id"}


def validate_json(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Validate the supported strict schema subset, raising useful ValueErrors.

    JSON numbers must be finite; Python bool is deliberately not an integer.
    This interpreter never evaluates values as Python or shell expressions.
    """
    if not isinstance(schema, dict):
        raise ValueError(f"{path}: schema must be an object")
    unsupported = set(schema) - _SUPPORTED
    if unsupported:
        raise ValueError(f"{path}: unsupported schema keywords {sorted(unsupported)}")
    kinds = schema.get("type")
    kinds = kinds if isinstance(kinds, list) else [kinds] if kinds else []
    predicates = {
        "object": lambda v: isinstance(v, dict) and all(isinstance(k, str) for k in v),
        "array": lambda v: isinstance(v, list), "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool), "null": lambda v: v is None,
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
        and math.isfinite(v),
    }
    if any(kind not in predicates for kind in kinds):
        raise ValueError(f"{path}: unsupported schema type")
    if kinds and not any(predicates[kind](instance) for kind in kinds):
        raise ValueError(f"{path}: expected {' or '.join(kinds)}")
    if "const" in schema and (instance != schema["const"] or type(instance) is not type(schema["const"])):
        raise ValueError(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and not any(instance == item and type(instance) is type(item) for item in schema["enum"]):
        raise ValueError(f"{path}: value is outside enum")
    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(instance)
        if missing:
            raise ValueError(f"{path}: missing required keys {sorted(missing)}")
        extra = set(instance) - set(properties)
        additional = schema.get("additionalProperties", True)
        if additional is False and extra:
            raise ValueError(f"{path}: unexpected keys {sorted(extra)}")
        for key, value in instance.items():
            if key in properties:
                validate_json(value, properties[key], f"{path}.{key}")
            elif isinstance(additional, dict):
                validate_json(value, additional, f"{path}.{key}")
    elif isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", float("inf")):
            raise ValueError(f"{path}: invalid array length")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, allow_nan=False) for item in instance]
            if len(canonical) != len(set(canonical)):
                raise ValueError(f"{path}: array values must be unique")
        if "items" in schema:
            for index, value in enumerate(instance):
                validate_json(value, schema["items"], f"{path}[{index}]")
    elif isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0) or len(instance) > schema.get("maxLength", float("inf")):
            raise ValueError(f"{path}: invalid string length")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise ValueError(f"{path}: string does not match pattern")
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if not math.isfinite(instance):
            raise ValueError(f"{path}: non-finite number")
        if instance < schema.get("minimum", -float("inf")) or instance > schema.get("maximum", float("inf")):
            raise ValueError(f"{path}: number is outside range")
