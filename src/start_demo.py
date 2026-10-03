"""Serve the prepared static demo on loopback using Python's standard library."""
import argparse
import errno
import functools
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
REQUIRED_PAGES = ("index.html", "projects.html", "model.html")


class DemoHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format, *args):
        # Keep the presenter's Terminal focused on the demo URL and stop command.
        pass


def bind_server(preferred_port):
    """Bind before announcing a URL; never reuse or stop someone else's server."""
    handler = functools.partial(DemoHandler, directory=str(WEB))
    ports = [0] if preferred_port == 0 else [
        *range(preferred_port, min(preferred_port + 10, 65536)), 0
    ]
    occupied = []
    for port in ports:
        try:
            return ThreadingHTTPServer(("127.0.0.1", port), handler), occupied
        except OSError as error:
            if error.errno != errno.EADDRINUSE:
                raise
            occupied.append(port)
    raise RuntimeError("Could not allocate a local demo port.")


def smoke_check(server, base_url):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        local_http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for page in REQUIRED_PAGES:
            with local_http.open(base_url + "/" + page, timeout=5) as response:
                body = response.read().decode("utf-8")
                if response.status != 200 or "Public Investment Map" not in body:
                    raise RuntimeError("Unexpected demo response for " + page)
                if response.headers.get("Cache-Control") != "no-store":
                    raise RuntimeError("Demo response can be stale: " + page)
        print("PASS: index, project explorer, and proposal page served on loopback.", flush=True)
    finally:
        server.shutdown()
        thread.join(timeout=5)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765,
                        help="Preferred local port; busy ports are skipped. Use 0 for any free port.")
    parser.add_argument("--project", default="dilworth-park", help="Project slug to open (default: dilworth-park).")
    parser.add_argument("--no-browser", action="store_true", help="Print the URL without opening a browser.")
    parser.add_argument("--smoke-test", action="store_true", help="Check all three pages, then stop; never opens a browser.")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    missing = [page for page in REQUIRED_PAGES if not (WEB / page).is_file()]
    if missing:
        parser.error("Prepared demo pages are missing: " + ", ".join(missing)
                     + ". Rebuild the site before the presentation.")
    server, occupied = bind_server(args.port)
    port = server.server_address[1]
    base_url = "http://127.0.0.1:" + str(port)
    url = base_url + "/projects.html?" + urllib.parse.urlencode({"project": args.project})
    try:
        if occupied:
            print("Ports already in use: " + ", ".join(map(str, occupied))
                  + ". Existing services were left running.", flush=True)
        print("Public Investment Map demo\n" + url, flush=True)
        if args.smoke_test:
            smoke_check(server, base_url)
            return 0
        print("Keep this Terminal window open. Press Control-C here to stop this demo.\n"
              "No network connection, raw Yelp files, or model rebuild is needed.", flush=True)
        if not args.no_browser:
            if sys.platform == "darwin":
                try:
                    opened = subprocess.run(["open", url], check=False)
                    if opened.returncode:
                        print("Open the URL above in your browser.", flush=True)
                except OSError:
                    print("Open the URL above in your browser.", flush=True)
            else:
                print("Open the URL above in your browser.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nDemo stopped.", flush=True)
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as error:
        print("Could not start the local demo: " + str(error), file=sys.stderr)
        raise SystemExit(1)
