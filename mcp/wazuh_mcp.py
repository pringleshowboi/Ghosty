import os
import json
from typing import List, Dict

from supply_chain.wazuh.alerts_client import fetch_recent_alerts
from supply_chain.agentic.hitl_governor import add_proposal
def get_critical_alerts(limit: int = 5, minutes: int = 120, min_level: int = 12) -> List[Dict]:
    alerts = fetch_recent_alerts(minutes=minutes, limit=max(limit * 10, 50))
    def level_of(a: Dict) -> int:
        rule = a.get("rule", {})
        if isinstance(rule, dict):
            return int(rule.get("level", 0))
        # some events may have top-level level
        try:
            return int(a.get("level", 0))
        except Exception:
            return 0
    crit = [a for a in alerts if level_of(a) >= int(min_level)]
    return crit[:int(limit)]

def block_ip(ip_address: str, reason: str = "Requested via MCP") -> Dict:
    pid = add_proposal(
        actor="mcp",
        action="block_ip",
        payload={"ip": ip_address},
        reason=reason,
        expires_sec=1800,
    )
    return {"proposal_id": pid, "status": "submitted", "action": "block_ip", "ip": ip_address}

# Try to expose these tools via FastMCP if available
def _run_fastmcp() -> None:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception:
        raise
    mcp = FastMCP("WazuhSentinel")

    @mcp.tool()
    def mcp_get_critical_alerts(limit: int = 5, minutes: int = 120, min_level: int = 12):
        return get_critical_alerts(limit=limit, minutes=minutes, min_level=min_level)

    @mcp.tool()
    def mcp_block_ip(ip_address: str, reason: str = "Requested via MCP"):
        return block_ip(ip_address=ip_address, reason=reason)

    mcp.run()

def _run_http_fallback() -> None:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/tools/get_critical_alerts":
                qs = parse_qs(parsed.query)
                limit = int(qs.get("limit", ["5"])[0])
                minutes = int(qs.get("minutes", ["120"])[0])
                min_level = int(qs.get("min_level", ["12"])[0])
                data = get_critical_alerts(limit=limit, minutes=minutes, min_level=min_level)
                body = json.dumps(data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == "/tools/block_ip":
                qs = parse_qs(parsed.query)
                ip = qs.get("ip", [""])[0]
                reason = qs.get("reason", ["Requested via HTTP fallback"])[0]
                data = block_ip(ip_address=ip, reason=reason)
                body = json.dumps(data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

    port = int(os.environ.get("MCP_FALLBACK_PORT", "8088"))
    httpd = HTTPServer(("0.0.0.0", port), Handler)
    httpd.serve_forever()

if __name__ == "__main__":
    try:
        _run_fastmcp()
    except Exception:
        _run_http_fallback()
