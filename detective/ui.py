"""Failed Build Detective - Web UI Server and Launcher.

Launches a lightweight local dashboard server and automatically opens the
Failed Build Detective interactive user interface in your default browser.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detective.analyzer import (
    BuildLogAnalyzer,
    CATEGORY_BUILD,
    CATEGORY_DEPENDENCY,
    CATEGORY_SUCCESS,
    CATEGORY_TEST,
    CATEGORY_UNKNOWN,
)

WEB_DIR = Path(__file__).resolve().parent / "web"
PORT = 8080


class DetectiveHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving web assets and providing /api/analyze."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_POST(self) -> None:
        """Handle POST requests to /api/analyze."""
        if self.path == "/api/analyze":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
                log_content = data.get("log", "")
                analyzer = BuildLogAnalyzer(log_content)
                result = analyzer.analyze()

                # Determine CSS class suffix & severity
                class_suffix = "cat-dependency"
                severity = "HIGH PRIORITY"
                if result.category == CATEGORY_BUILD:
                    class_suffix = "cat-build"
                    severity = "CRITICAL FAILURE"
                elif result.category == CATEGORY_TEST:
                    class_suffix = "cat-test"
                    severity = "DEFECT DETECTED"
                elif result.category == CATEGORY_SUCCESS:
                    class_suffix = "cat-success"
                    severity = "CLEAN PIPELINE"
                elif result.category == CATEGORY_UNKNOWN:
                    class_suffix = "cat-build"
                    severity = "UNCLASSIFIED ERROR"

                payload = {
                    "category": result.category,
                    "icon": result.icon,
                    "classSuffix": class_suffix,
                    "severity": severity,
                    "headline": result.headline,
                    "errorMessage": result.error_message,
                    "snippet": result.error_snippet,
                    "fixes": result.suggested_fixes,
                    "isFailure": result.is_failure,
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except Exception as exc:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_server(port: int = PORT) -> None:
    """Start local web server and open browser."""
    # Find available port if 8080 is taken
    current_port = port
    server = None
    for p in range(current_port, current_port + 10):
        try:
            server = HTTPServer(("127.0.0.1", p), DetectiveHandler)
            current_port = p
            break
        except OSError:
            continue

    if not server:
        print(f"Error: Could not bind to port {port} or next 10 ports.")
        sys.exit(1)

    url = f"http://localhost:{current_port}"

    print("=" * 68)
    print(" 🕵️   FAILED BUILD DETECTIVE - INTERACTIVE WEB DASHBOARD")
    print("=" * 68)
    print(f"  ➜ Dashboard URL:  {url}")
    print(f"  ➜ Web Root:       {WEB_DIR}")
    print("  ➜ Status:         Ready and listening for pipeline logs")
    print("  ➜ Press Ctrl+C in this terminal to stop the server")
    print("=" * 68)

    # Open browser automatically after 1 second
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Failed Build Detective Web UI...")
        server.server_close()


if __name__ == "__main__":
    start_server()
