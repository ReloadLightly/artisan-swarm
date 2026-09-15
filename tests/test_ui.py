"""HTTP tests use explicit fixtures, never purported live research artifacts."""

from __future__ import annotations

import http.client
import json
import re
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from artisan_swarm.ui import make_handler


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temporary.name) / "fixture-run"
        self.run_dir.mkdir()
        self.calls = {"view": [], "replay": [], "live": [], "scenario": []}
        self.live_started = threading.Event()
        self.live_release = threading.Event()
        self.fixture_view = {
            "manifest": {"mode": "fixture", "status": "completed", "run_id": "fixture-run"},
            "candidates": [{"id": "fixture-parent", "title": "<script>window.compromised = true</script>"}],
            "brief": "# Fixture brief\nThis is a hand-authored HTTP test fixture.",
        }

        def view(path):
            self.calls["view"].append(path)
            return self.fixture_view

        def replay(path):
            self.calls["replay"].append(path)
            return {"status": "passed", "mode": "replay", "model_calls": 0}

        def live(path):
            self.calls["live"].append(path)
            self.live_started.set()
            self.live_release.wait(5)

        def scenario(path, *, changed):
            self.calls["scenario"].append((path, changed))
            return {"changed": changed, "executions": {}, "model_calls": 0}

        handler = make_handler(self.run_dir, build_view=view, replay=replay, run_live=live, scenario_view=scenario)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.host = f"127.0.0.1:{self.server.server_port}"
        status, _, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)

    def tearDown(self):
        self.live_release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, method, path, payload=None, *, authenticated=False, extra_headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Host": self.host}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if authenticated:
            headers["X-CSRF-Token"] = self.token
            headers["Origin"] = "http://" + self.host
        headers.update(extra_headers or {})
        connection.request(method, path, body=json.dumps(payload) if payload is not None else None, headers=headers)
        response = connection.getresponse()
        body = response.read().decode()
        result = (response.status, dict(response.getheaders()), body)
        connection.close()
        return result

    def test_load_refresh_assets_and_brief_never_start_models(self):
        for path in ("/", "/api/run", "/api/run", "/static/app.js", "/static/app.css", "/api/brief"):
            with self.subTest(path=path):
                status, headers, _ = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
                self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.calls["live"], [])
        self.assertEqual(self.calls["replay"], [])
        self.assertEqual(self.calls["scenario"], [])

    def test_replay_and_scenario_execute_without_live_backend(self):
        status, _, body = self.request("POST", "/api/replay", {}, authenticated=True)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["model_calls"], 0)
        for changed in (True, False):
            status, _, body = self.request("POST", "/api/scenario", {"changed": changed}, authenticated=True)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["changed"], changed)
        self.assertEqual(self.calls["live"], [])
        self.assertEqual(self.calls["replay"], [self.run_dir])
        self.assertEqual(self.calls["scenario"], [(self.run_dir, True), (self.run_dir, False)])

    def test_live_requires_token_origin_and_explicit_confirmation(self):
        confirmation = {"confirm": "start_new_live_run"}
        self.assertEqual(self.request("POST", "/api/live", confirmation)[0], 403)
        self.assertEqual(self.request("POST", "/api/live", confirmation, authenticated=True,
                                      extra_headers={"Origin": "https://untrusted.example"})[0], 403)
        self.assertEqual(self.request("POST", "/api/live", {}, authenticated=True)[0], 400)
        self.assertEqual(self.request("POST", "/api/live", {"confirm": True}, authenticated=True)[0], 400)
        self.assertEqual(self.request("GET", "/api/live")[0], 404)
        self.assertEqual(self.calls["live"], [])

    def test_deliberate_live_action_starts_one_new_run_and_allows_status_polling(self):
        status, _, body = self.request("POST", "/api/live", {"confirm": "start_new_live_run"}, authenticated=True)
        self.assertEqual(status, 202)
        self.assertTrue(self.live_started.wait(2))
        destination = self.calls["live"][0]
        self.assertEqual(destination.parent, self.run_dir.parent)
        self.assertNotEqual(destination, self.run_dir)
        self.assertEqual(json.loads(body)["run_id"], destination.name)
        status, _, body = self.request("GET", "/api/run")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["ui"]["busy"], "live")
        self.assertEqual(self.request("POST", "/api/live", {"confirm": "start_new_live_run"}, authenticated=True)[0], 409)
        self.assertEqual(self.request("POST", "/api/replay", {}, authenticated=True)[0], 409)
        self.assertEqual(len(self.calls["live"]), 1)

    def test_arbitrary_paths_and_nonlocal_hosts_are_rejected(self):
        for path in ("/static/../ui.py", "/static/%2e%2e/ui.py", "/api/artifact?path=/etc/passwd", "/manifest.json"):
            self.assertEqual(self.request("GET", path)[0], 404)
        self.assertEqual(self.request("GET", "/api/run", extra_headers={"Host": "malicious.example"})[0], 403)
        self.assertEqual(self.request("GET", "/", extra_headers={"Host": "localhost:invalid"})[0], 403)

    def test_scenario_requires_a_boolean_and_known_json_shape(self):
        for payload in ({"changed": "false"}, {"changed": 1}, {}, []):
            self.assertEqual(self.request("POST", "/api/scenario", payload, authenticated=True)[0], 400)
        self.assertEqual(self.calls["scenario"], [])

    def test_artifact_text_is_not_embedded_in_html_and_client_uses_text_nodes(self):
        _, _, html = self.request("GET", "/")
        self.assertNotIn("window.compromised", html)
        _, _, raw = self.request("GET", "/api/run")
        self.assertIn("<script>", json.loads(raw)["candidates"][0]["title"])
        _, _, js = self.request("GET", "/static/app.js")
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("insertAdjacentHTML", js)
        self.assertIn("document.createTextNode", js)


if __name__ == "__main__":
    unittest.main()
