#!/usr/bin/python3
"""Exercise firstboot authentication against an actual local HTTP server."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / "overlay/usr/lib/inithooks/bin/jellyfin-server.py"


class StartupAuthentication(unittest.TestCase):
    def exercise(self, statuses, password_status=204, error=None):
        calls = []
        statuses = list(statuses)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                calls.append((self.path, payload))
                if self.path == "/Users/AuthenticateByName":
                    status = statuses.pop(0) if statuses else 200
                    body = json.dumps({"AccessToken": "fixture-token"}).encode() if status == 200 else b"Server still starting"
                elif self.path == "/Users/Password":
                    status = password_status if self.headers.get("X-Emby-Token") == "fixture-token" else 403
                    body = b"" if status == 204 else b"Password update failed"
                else:
                    status, body = 404, b"Unexpected endpoint"
                self.send_response(status)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            spec = importlib.util.spec_from_file_location("jellyfin_firstboot", HELPER)
            helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            helper.BASE_URL = "http://127.0.0.1:%d" % server.server_port
            with tempfile.TemporaryDirectory() as tmp:
                credential = Path(tmp) / "bootstrap"
                credential.write_text("fixture-bootstrap\n")
                helper.BOOTSTRAP_PASSWORD_FILE = str(credential)
                with patch("sys.argv", ["jellyfin-server.py", "--pass-stdin"]), patch("sys.stdin", io.StringIO("fixture-new-password")), patch.object(helper.time, "sleep") as sleep:
                    started = time.monotonic()
                    if error:
                        with self.assertRaisesRegex(RuntimeError, error) as failure:
                            helper.main()
                        if isinstance(failure.exception.__cause__, urllib.error.HTTPError):
                            failure.exception.__cause__.close()
                        self.assertTrue(credential.exists())
                    else:
                        helper.main()
                        self.assertFalse(credential.exists())
                    elapsed = time.monotonic() - started
                    waits = sleep.call_args_list[:]
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
        return calls, waits, elapsed

    def test_ready_server_uses_two_requests_without_waiting(self):
        calls, waits, elapsed = self.exercise([200])
        self.assertEqual([path for path, _ in calls], ["/Users/AuthenticateByName", "/Users/Password"])
        self.assertEqual(waits, [])
        self.assertEqual(calls[-1][1], {"CurrentPw": "fixture-bootstrap", "NewPw": "fixture-new-password", "ResetPassword": False})
        print("healthy HTTP flow: %.6fs, no waits" % elapsed)

    def test_startup_503s_recover_before_one_password_change(self):
        calls, waits, _ = self.exercise([503, 503, 200])
        self.assertEqual([path for path, _ in calls], ["/Users/AuthenticateByName"] * 3 + ["/Users/Password"])
        self.assertEqual(len(waits), 2)

    def test_invalid_credentials_fail_immediately(self):
        calls, waits, _ = self.exercise([401], error="HTTP 401")
        self.assertEqual(len(calls), 1)
        self.assertEqual(waits, [])

    def test_password_mutations_are_never_retried(self):
        calls, waits, _ = self.exercise([200], password_status=503, error="HTTP 503")
        self.assertEqual([path for path, _ in calls], ["/Users/AuthenticateByName", "/Users/Password"])
        self.assertEqual(waits, [])

    def test_persistent_startup_failure_is_bounded(self):
        calls, waits, _ = self.exercise([503] * 60, error="HTTP 503")
        self.assertTrue(1 < len(calls) <= 6)
        self.assertTrue(all(path == "/Users/AuthenticateByName" for path, _ in calls))
        self.assertLessEqual(sum(call.args[0] for call in waits), 30)


if __name__ == "__main__":
    unittest.main()
