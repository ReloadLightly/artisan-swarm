"""Content-addressed checks and append-only research snapshots."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value, *, immutable=True):
    """Never rewrite a research snapshot, including when recovering a run."""
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable:
        try:
            with path.open("xb") as f:
                f.write(data)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError(f"Immutable artifact differs: {path.name}") from None
    else:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)


def semantic_diff(parent: dict, child: dict) -> dict:
    changes = []
    old = {a["id"]: a for a in parent["actions"]}
    new = {a["id"]: a for a in child["actions"]}
    executable_fields = {"when", "prerequisites", "depends_on", "fallbacks"}
    for key in sorted(old.keys() | new.keys()):
        if key not in old or key not in new:
            changes.append({"action_id": key, "field": "action", "before": old.get(key), "after": new.get(key), "executable": True})
        else:
            for field in sorted(old[key].keys() | new[key].keys()):
                if old[key].get(field) != new[key].get(field):
                    changes.append({"action_id": key, "field": field, "before": old[key].get(field), "after": new[key].get(field), "executable": field in executable_fields})
    return {"parent_id": parent["id"], "child_id": child["id"], "changes": changes,
            "executable_change": any(c["executable"] for c in changes),
            "note": "Structural comparison; action descriptions and a model review are also needed to assess strategic value."}


def control_signature(program: dict) -> dict:
    """Decision-relevant structure, excluding prose and advisory trace links.

    The preserved semantic_diff flags changed fields, including descriptive
    changes inside those fields. This stricter signature establishes that a
    revision actually changes action eligibility or the action population.
    """
    return {a["id"]: {
        "when": {"operator": a["when"]["operator"], "tests": sorted(
            ((t["fact"], t["equals"]) for t in a["when"]["tests"]))},
        "prerequisites": sorted((t["fact"], t["equals"]) for t in a["prerequisites"]),
        "depends_on": sorted(a["depends_on"]),
    } for a in program["actions"]}
