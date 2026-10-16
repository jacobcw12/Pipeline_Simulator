"""Serve the pipeline map front end and the network data behind it.

Run inside the venv:  .venv/bin/python server.py  then open http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from gas_network import build_gas_network

STATIC_DIR = Path(__file__).parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/api/network":
            # ?disabled_nodes=HRM,TAR&disabled_edges=HRM>FER,MEL>GEL
            query = parse_qs(url.query)
            split = lambda key: [x for v in query.get(key, []) for x in v.split(",") if x]
            network = build_gas_network(
                disabled_nodes=set(split("disabled_nodes")),
                disabled_edges={tuple(x.split(">", 1)) for x in split("disabled_edges") if ">" in x},
            )
            body = json.dumps(network.to_dict()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"Serving pipeline map at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
