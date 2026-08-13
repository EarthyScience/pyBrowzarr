"""
Command-line entry point for Browzarr.

Serves the pre-built static frontend (``web/dist``) on a local port and
opens it in the default browser. WebGPU requires a "secure context," and
all major browsers treat ``localhost`` as secure, so no HTTPS/cert setup
is needed here.
"""

from __future__ import annotations
import importlib
import re
import argparse
import http.server
from urllib.parse import urlparse, parse_qs, unquote
import mimetypes
import socket
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

DEFAULT_START_PORT = 8765

# SimpleHTTPRequestHandler's mimetype guessing can be inconsistent across
# Python versions/platforms for a couple of types WebGPU/WASM pipelines
# care about. Register them explicitly to be safe.
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/javascript", ".mjs")

def find_free_port(start: int = DEFAULT_START_PORT, max_attempts: int = 50) -> int:
    """Return the first available TCP port at or after `start`."""
    port = start
    for _ in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
        port += 1
    raise RuntimeError(
        f"Could not find a free port in range {start}-{start + max_attempts}"
    )

def get_dist_dir() -> Path:
    """
    Locate the bundled static frontend build.

    Raises a clear error if the package was installed/run without the
    `web/dist` assets present (e.g. someone forgot to run the frontend
    build step before packaging).
    """

    dist_dir = importlib.resources.files("browzarr") / "web" / "dist"
    dist_path = Path(str(dist_dir))
    
    if not dist_path.exists() or not any(dist_path.iterdir()):
        raise FileNotFoundError(
            "No frontend build found in 'web/dist'.\n"
            "Did you run the frontend build step (e.g. `npm run build` + "
            "copy to src/browzarr_viewer/web/dist) before installing this "
            "package?"
        )

    return dist_path

def _content_type_for(file_path: Path) -> str:
            name = file_path.name
            if name.endswith(".json") or name.startswith(".z"):
                return "application/json"
            return "application/octet-stream"
        
def _send_cors_headers(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "*")

def make_handler(directory: str):
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args):
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/file":
                self.handle_file_request(parsed)
                return

            if parsed.path.startswith('/zarr/'):
                self.handle_zarr_request(parsed)
                return

            super().do_GET()
        def do_HEAD(self):
            parsed = urlparse(self.path)
            if parsed.path.startswith('/zarr/'):
                self.handle_zarr_request(parsed, method="HEAD")
                return
            super().do_HEAD()

        def handle_file_request(self, parsed):
            qs = parse_qs(parsed.query)
            raw_path = qs.get("path", [None])[0]

            if not raw_path:
                self.send_error(400, "Missing 'path' query parameter")
                return

            file_path = Path(unquote(raw_path))

            if not file_path.is_file():
                self.send_error(404, f"File not found: {file_path}")
                return

            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            except OSError as e:
                self.send_error(500, f"Error reading file: {e}")        
        
        def handle_zarr_request(self, parsed, method="GET"):
            """Handle /zarr/... requests (both GET and HEAD)"""
            encoded_path = parsed.path[6:]  # Remove '/zarr/'
        
            if not encoded_path:
                self.send_error(400, "Missing path after /zarr/")
                return
        
            file_path = Path(unquote(encoded_path))

            # --- Explicit 404 instead of falling through silently ---
            if not file_path.exists() or not file_path.is_file():
                self.send_response(404)
                _send_cors_headers(self)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                if method == "GET":
                    self.wfile.write(b"Not found")
                return
        
            try:
                filesize = file_path.stat().st_size
                content_type = _content_type_for(file_path)
        
                # --- HEAD: headers only, no body ---
                if method == "HEAD":
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(filesize))
                    self.send_header("Accept-Ranges", "bytes")
                    _send_cors_headers(self)
                    self.end_headers()
                    return
        
                range_header = self.headers.get("Range")
        
                # --- Range request handling ---
                if range_header:
                    m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                    if m:
                        start = int(m.group(1))
                        end = int(m.group(2)) if m.group(2) else filesize - 1
        
                        if start >= filesize or end < start:
                            self.send_response(416)
                            self.send_header("Content-Range", f"bytes */{filesize}")
                            _send_cors_headers(self)
                            self.end_headers()
                            return
        
                        end = min(end, filesize - 1)
                        length = end - start + 1
        
                        with open(file_path, "rb") as f:
                            f.seek(start)
                            chunk = f.read(length)
        
                        self.send_response(206)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Range", f"bytes {start}-{end}/{filesize}")
                        self.send_header("Content-Length", str(length))
                        self.send_header("Accept-Ranges", "bytes")
                        _send_cors_headers(self)
                        self.end_headers()
                        self.wfile.write(chunk)
                        return
        
                # --- Full file response ---
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(filesize))
                self.send_header("Accept-Ranges", "bytes")
                _send_cors_headers(self)
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
        
            except OSError as e:
                self.send_error(500, f"Error reading file: {e}")
                return
    return QuietHandler


def serve(port: int | None = None, open_browser: bool = True, verbose: bool = True) -> None:
    """Start the local server and (optionally) open the browser."""
    dist_path = get_dist_dir()
    resolved_port = port if port is not None else find_free_port()
    handler = make_handler(str(dist_path))

    # allow_reuse_address avoids "Address already in use" on quick restarts
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("localhost", resolved_port), handler) as httpd:
        url = f"http://localhost:{resolved_port}"

        if verbose:
            print(f"Browzarr is running at {url}")
            print("Press Ctrl+C to stop.")

        if open_browser:
            threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            if verbose:
                print("\nStopping Browzarr server.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="browzarr",
        description="Launch the Browzarr locally.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"Port to serve on (default: first free port starting at {DEFAULT_START_PORT})",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the server without automatically opening a browser tab",
    )
    args = parser.parse_args()

    try:
        serve(port=args.port, open_browser=not args.no_browser)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
