"""Explicit live / replay / validate / serve commands; no inference at import."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .archive import read
from .workers import ROOT, WorkerError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Artisan Swarm M1 executable discovery and repair")
    sub = parser.add_subparsers(dest="command", required=True)
    live = sub.add_parser("live", help="Start or resume six actual Codex research jobs")
    live.add_argument("--run-dir", type=Path, required=True)
    live.add_argument("--data-dir", type=Path, default=ROOT / "data" / "m1")
    for command, help_text in (("replay", "Verify and execute saved outputs with zero model calls"),
                               ("validate", "Validate frozen evidence and, if supplied, a complete run"),
                               ("serve", "Open the local interface; page loads never call a model")):
        p = sub.add_parser(command, help=help_text)
        p.add_argument("--run-dir", type=Path, required=command != "validate")
        if command == "serve": p.add_argument("--port", type=int, default=8765)
        if command == "validate": p.add_argument("--data-dir", type=Path, default=ROOT / "data" / "m1")
    args = parser.parse_args(argv)
    try:
        if args.command == "live":
            from .orchestrator import run_live
            result = run_live(args.run_dir, args.data_dir)
        elif args.command == "replay":
            from .orchestrator import replay
            result = replay(args.run_dir)
        elif args.command == "validate":
            from .evidence import validate_dossier, validate_case, apply_disruption
            dossier = read(args.data_dir / "dossier.json")
            case = read(args.data_dir / "case.json")
            disruption = read(args.data_dir / "disruption.json")
            validate_dossier(dossier)
            validate_case(case, dossier)
            validate_case(apply_disruption(case, disruption), dossier)
            result = {"status": "passed", "sources": len(dossier["sources"]), "claims": len(dossier["claims"]), "model_calls": 0}
            if args.run_dir:
                from .orchestrator import replay
                result["run_replay"] = replay(args.run_dir)
        else:
            from .ui import serve
            serve(args.run_dir, args.port)
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, WorkerError, OSError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False))
        return 1
