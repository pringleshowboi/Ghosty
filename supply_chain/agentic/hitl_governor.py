import os
import json
import time
import uuid
from typing import Dict, List, Optional

PROPOSALS_PATH = os.path.join(os.getcwd(), "supply_chain", "agentic", "proposals.json")
ACTION_LOG_PATH = r"c:\ProgramData\Wazuh\logs\ghost_actions.json"

def _load() -> List[Dict]:
    if os.path.isfile(PROPOSALS_PATH):
        try:
            with open(PROPOSALS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save(items: List[Dict]) -> None:
    os.makedirs(os.path.dirname(PROPOSALS_PATH), exist_ok=True)
    with open(PROPOSALS_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

def add_proposal(actor: str, action: str, payload: Dict, reason: str, expires_sec: int = 1800) -> str:
    items = _load()
    pid = str(uuid.uuid4())
    now = int(time.time())
    items.append({
        "id": pid,
        "actor": actor,
        "action": action,
        "payload": payload,
        "reason": reason,
        "status": "pending",
        "created_at": now,
        "expires_at": now + max(60, expires_sec)
    })
    _save(items)
    return pid

def list_proposals(status: Optional[str] = None) -> List[Dict]:
    items = _load()
    if status:
        items = [i for i in items if i.get("status") == status]
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)

def decide_proposal(pid: str, decision: str) -> Optional[Dict]:
    decision = decision.lower()
    assert decision in ("approved", "denied")
    items = _load()
    target = None
    for it in items:
        if it.get("id") == pid:
            it["status"] = decision
            it["decided_at"] = int(time.time())
            target = it
            break
    _save(items)
    if target and decision == "approved":
        execute_proposal(target)
    return target

def execute_proposal(prop: Dict) -> None:
    os.makedirs(os.path.dirname(ACTION_LOG_PATH), exist_ok=True)
    entry = {
        "source": "hitl",
        "type": "proposal_exec",
        "id": prop.get("id"),
        "actor": prop.get("actor"),
        "action": prop.get("action"),
        "payload": prop.get("payload"),
        "ts": int(time.time())
    }
    try:
        with open(ACTION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    if prop.get("action") == "inject_wazuh_rule":
        rule_text = prop.get("payload", {}).get("xml", "")
        out_dir = os.path.join(os.getcwd(), "supply_chain", "wazuh", "staged_rules")
        os.makedirs(out_dir, exist_ok=True)
        out_fp = os.path.join(out_dir, f"proposed_{prop.get('id')}.xml")
        try:
            with open(out_fp, "w", encoding="utf-8") as f:
                f.write(rule_text)
        except Exception:
            pass
    elif prop.get("action") == "block_ip":
        ip = prop.get("payload", {}).get("ip", "")
        if ip:
            lists_dir = r"c:\ProgramData\Wazuh\lists"
            os.makedirs(lists_dir, exist_ok=True)
            try:
                with open(os.path.join(lists_dir, "malicious-ips.cdb"), "a", encoding="utf-8") as f:
                    f.write(f"{ip}:1\n")
            except Exception:
                pass
