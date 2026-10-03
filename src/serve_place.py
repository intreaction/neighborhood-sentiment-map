"""Serve the static Place Lab demo on loopback.

Run: python3 src/serve_place.py [--port 8766] [--open]
The same web assets can be hosted by any static HTTP server.
"""
import argparse
import errno
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


class PlaceServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler=None):
        if address[0] != "127.0.0.1":
            raise ValueError("Place's demo server must bind to 127.0.0.1")
        super().__init__(address, handler or PlaceHandler)


class PlaceHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def log_message(self, *_args):
        # Keep the demo terminal focused on the launch URL.
        pass

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def json_response(self, code, value):
        raw = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def local_request(self):
        port = self.server.server_port
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if not ipaddress.ip_address(self.client_address[0]).is_loopback or host not in allowed:
            self.json_response(403, {"error": "This demo endpoint is available only on its loopback origin."})
            return False
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + host:
            self.json_response(403, {"error": "Use the app served by this local server."})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            self.json_response(404, {"error": "Place Lab is a static app with no API endpoints."})
        else:
            target = Path(self.translate_path(path)).resolve()
            if WEB.resolve() not in target.parents and target != WEB.resolve():
                self.json_response(403, {"error": "Outside the demo directory."})
                return
            if any(part.startswith(".") for part in Path(unquote(path)).parts):
                self.send_error(404)
                return
            super().do_GET()

    def do_HEAD(self):
        # Reuse the same origin/path checks; HEAD is deliberately not an API surface.
        if self.local_request():
            target = Path(self.translate_path(urlsplit(self.path).path)).resolve()
            if WEB.resolve() in target.parents and not any(part.startswith(".") for part in target.relative_to(WEB.resolve()).parts):
                super().do_HEAD()
            else:
                self.send_error(404)

    def list_directory(self, _path):
        self.send_error(404, "Directory listing disabled")
        return None

    def do_POST(self):
        if self.local_request():
            self.json_response(405, {"error": "This static demo accepts only GET and HEAD requests."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--open", action="store_true", help="Open Place Lab in the default browser.")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    try:
        server = PlaceServer(("127.0.0.1", args.port))
    except OSError as error:
        if error.errno != errno.EADDRINUSE:
            raise
        server = PlaceServer(("127.0.0.1", 0))
        print(f"Port {args.port} is occupied; using a free port. Existing services remain running.", flush=True)
    with server:
        url = f"http://127.0.0.1:{server.server_port}/place.html"
        print("Place Lab: " + url, flush=True)
        if args.open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
