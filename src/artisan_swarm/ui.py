"""Read-only artifact browser with explicit replay and live-run controls.

The localhost server exposes only the orchestrator's public view. It never serves
arbitrary files from a run directory and never starts a model from a GET request.
"""

from __future__ import annotations

import importlib
import json
import secrets
import threading
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

STATIC_DIR = Path(__file__).with_name("static")
MAX_BODY = 4096


def make_handler(
    run_dir: Path,
    *,
    build_view: Callable[..., Any] | None = None,
    replay: Callable[..., Any] | None = None,
    run_live: Callable[..., Any] | None = None,
    scenario_view: Callable[..., Any] | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Build an isolated handler; injectable operations keep HTTP tests offline."""
    current_dir = Path(run_dir).resolve()
    if any(fn is None for fn in (build_view, replay, run_live, scenario_view)):
        workflow = importlib.import_module("artisan_swarm.orchestrator")
        build_view = build_view or workflow.build_view
        replay = replay or workflow.replay
        run_live = run_live or workflow.run_live
        scenario_view = scenario_view or workflow.scenario_view
    token = secrets.token_urlsafe(32)
    lock = threading.Lock()
    state: dict[str, Any] = {
        "current_dir": current_dir,
        "previous_dir": current_dir,
        "busy": None,
        "live": None,
        "replay": None,
    }

    def public_view() -> dict[str, Any]:
        with lock:
            active = state["current_dir"]
            previous = state["previous_dir"]
            metadata = {key: deepcopy(state[key]) for key in ("busy", "live", "replay")}
        try:
            result = dict(build_view(active))
        except (FileNotFoundError, ValueError, KeyError) as error:
            if active == previous:
                result = {"manifest": {"status": "partial"}, "run_dir": str(active)}
            else:
                result = dict(build_view(previous))
            metadata["view_notice"] = str(error)[:1000]
        result["ui"] = metadata
        return result

    def live_job(destination: Path) -> None:
        try:
            run_live(destination)
            with lock:
                state["live"]["status"] = "finished"
        except Exception as error:  # The server remains inspectable after failure.
            with lock:
                state["live"]["status"] = "failed"
                state["live"]["error"] = f"{type(error).__name__}: {error}"[:1000]
        finally:
            with lock:
                state["busy"] = None
                state["live"]["finished_at"] = datetime.now(timezone.utc).isoformat()

    class Handler(BaseHTTPRequestHandler):
        server_version = "ArtisanSwarm/1.0"

        def log_message(self, format: str, *args: Any) -> None:
            # Do not log request content or accidental secrets in query strings.
            pass

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, payload: Any) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def _local_host(self) -> bool:
            try:
                host = urlsplit("http://" + self.headers.get("Host", ""))
                return host.hostname in {"127.0.0.1", "localhost", "::1"} and host.port == self.server.server_port
            except ValueError:
                return False

        def do_GET(self) -> None:
            if not self._local_host():
                self._json(403, {"error": "This interface accepts localhost requests only."})
                return
            path = urlsplit(self.path).path
            try:
                if path == "/":
                    content = (STATIC_DIR / "index.html").read_text().replace("__CSRF_TOKEN__", token)
                    self._send(200, content.encode(), "text/html; charset=utf-8")
                elif path in {"/static/app.js", "/static/app.css"}:
                    content_type = "text/javascript" if path.endswith(".js") else "text/css"
                    self._send(200, (STATIC_DIR / Path(path).name).read_bytes(), content_type + "; charset=utf-8")
                elif path == "/api/run":
                    self._json(200, public_view())
                elif path == "/api/brief":
                    brief = public_view().get("brief") or "No decision brief is available for this run yet."
                    if not isinstance(brief, str):
                        brief = json.dumps(brief, ensure_ascii=False, indent=2)
                    self._send(200, brief.encode(), "text/markdown; charset=utf-8")
                elif path == "/favicon.ico":
                    self._send(204, b"", "image/x-icon")
                else:
                    self._json(404, {"error": "Not found"})
            except Exception as error:
                self._json(500, {"error": f"{type(error).__name__}: {error}"[:1000]})

        def do_POST(self) -> None:
            if not self._local_host():
                self._json(403, {"error": "This interface accepts localhost requests only."})
                return
            origin = self.headers.get("Origin")
            expected_origin = "http://" + self.headers.get("Host", "")
            if (origin and origin != expected_origin) or not secrets.compare_digest(
                self.headers.get("X-CSRF-Token", ""), token
            ):
                self._json(403, {"error": "A same-origin request with the local action token is required."})
                return
            if self.headers.get_content_type() != "application/json":
                self._json(415, {"error": "Use application/json."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_BODY:
                    raise ValueError("Request body is too large.")
                payload = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(payload, dict):
                    raise ValueError("The request must be a JSON object.")
            except (ValueError, UnicodeDecodeError) as error:
                self._json(400, {"error": str(error)})
                return
            path = urlsplit(self.path).path
            try:
                if path == "/api/scenario":
                    changed = payload.get("changed")
                    if not isinstance(changed, bool):
                        self._json(400, {"error": "changed must be true or false."})
                        return
                    with lock:
                        active = state["current_dir"]
                    self._json(200, scenario_view(active, changed=changed))
                elif path == "/api/replay":
                    with lock:
                        if state["busy"]:
                            self._json(409, {"error": "Another run action is in progress."})
                            return
                        state["busy"] = "replay"
                        active = state["current_dir"]
                    try:
                        result = replay(active)
                        with lock:
                            state["replay"] = result
                        self._json(200, result)
                    finally:
                        with lock:
                            state["busy"] = None
                elif path == "/api/live":
                    if payload.get("confirm") != "start_new_live_run":
                        self._json(400, {"error": "Confirm this deliberate new live run."})
                        return
                    with lock:
                        if state["busy"]:
                            self._json(409, {"error": "Another run action is in progress."})
                            return
                        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                        destination = current_dir.parent / f"m1-{stamp}-{secrets.token_hex(3)}"
                        state["busy"] = "live"
                        state["previous_dir"] = state["current_dir"]
                        state["current_dir"] = destination
                        state["live"] = {
                            "status": "running", "run_id": destination.name,
                            "started_at": datetime.now(timezone.utc).isoformat(),
                        }
                        launch = dict(state["live"])
                    threading.Thread(target=live_job, args=(destination,), daemon=True).start()
                    self._json(202, launch)
                else:
                    self._json(404, {"error": "Not found"})
            except Exception as error:
                self._json(500, {"error": f"{type(error).__name__}: {error}"[:1000]})

    return Handler


def serve(run_dir: Path, port: int = 8765) -> None:
    """Serve the artifact interface on IPv4 localhost until interrupted."""
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(Path(run_dir)))
    print(f"Artisan Swarm: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
