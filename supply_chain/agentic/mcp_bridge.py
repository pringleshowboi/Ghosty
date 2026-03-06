import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from supply_chain.wazuh.alerts_client import fetch_recent_alerts

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/query/alerts":
            qs = parse_qs(u.query)
            minutes = int(qs.get("minutes", ["60"])[0])
            query = (qs.get("query", [""])[0]).lower()
            try:
                alerts = fetch_recent_alerts(minutes=minutes, limit=200)
                if query:
                    filtered = [a for a in alerts if query in json.dumps(a).lower()]
                else:
                    filtered = alerts
                self._send(200, {"items": filtered, "count": len(filtered)})
            except Exception as e:
                self._send(500, {"error": str(e)})
        else:
            self._send(404, {"error": "not_found"})

def serve(host: str = "127.0.0.1", port: int = 8765):
    httpd = HTTPServer((host, port), Handler)
    httpd.serve_forever()

if __name__ == "__main__":
    serve()
