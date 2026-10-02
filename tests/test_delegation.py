"""Static delegation checks. No public ingress or webhook is exercised."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DelegationTests(unittest.TestCase):
    def test_client_discovery(self):
        data = json.loads((ROOT / ".well-known/matrix/client").read_text())
        self.assertEqual(data, {"m.homeserver": {"base_url": "https://matrix.nop.team"}})

    def test_server_delegation(self):
        data = json.loads((ROOT / ".well-known/matrix/server").read_text())
        self.assertEqual(data, {"m.server": "matrix.nop.team:443"})

    @unittest.skipUnless(shutil.which("nginx"), "nginx not installed")
    def test_operator_nginx_snippet_syntax(self):
        snippet = (ROOT / "ops/matrix.nop.team.nginx.example").read_text()
        self.assertEqual(snippet.count("__MATRIX_UPSTREAM_URL__"), 1)
        # This is a syntax-only, deliberately unroutable test fixture URL.
        snippet = snippet.replace("__MATRIX_UPSTREAM_URL__", "http://127.0.0.1:1")
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "nginx.conf"
            config.write_text(
                f"pid {tmp}/nginx.pid; error_log {tmp}/error.log;\n"
                "events {}\nhttp { access_log off; "
                f"client_body_temp_path {tmp}/client_body; "
                f"proxy_temp_path {tmp}/proxy; "
                f"fastcgi_temp_path {tmp}/fastcgi; "
                f"uwsgi_temp_path {tmp}/uwsgi; "
                f"scgi_temp_path {tmp}/scgi; "
                "server { listen 127.0.0.1:18080; "
                "server_name matrix.nop.team;\n"
                + snippet
                + "\n} }\n"
            )
            result = subprocess.run(
                [
                    "nginx", "-t", "-e", str(Path(tmp) / "error.log"),
                    "-p", tmp + "/", "-c", str(config),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
