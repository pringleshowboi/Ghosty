import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
import networkx as nx
import os
import json
import socket
import time
import requests
from supply_chain.agentic.ai_triage import analyze_threat, summarize_news
from supply_chain.wazuh.alerts_client import fetch_recent_alerts
import feedparser
from supply_chain.agentic.hitl_governor import list_proposals, decide_proposal
from supply_chain.agentic.aibom_agent import write_aibom

def generate_mock_data():
    np.random.seed(42)
    users = ['admin_jim', 'user_alice', 'user_bob', 'svc_backup']
    services = ['PC-001', 'PC-002', 'FileServer', 'SQL-Prod', 'DomainController']
    data = []
    for _ in range(200):
        u = np.random.choice(users[1:3])
        data.append([u, 4624, np.random.randint(8, 17), 'PC-001', 0])
    for _ in range(5):
        data.append(['user_alice', 4769, 2, 'DomainController', 1])
    return pd.DataFrame(data, columns=['User', 'EventID', 'Hour', 'Target', 'Is_Attacker'])

def _port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except Exception:
        return False

def _try_http(url: str, proxies: dict = None, timeout: float = 5.0) -> bool:
    try:
        r = requests.get(url, proxies=proxies, timeout=timeout, headers={"User-Agent": "curl/7.88"})
        return r.status_code == 200 and len(r.content) > 0
    except Exception:
        return False

def check_ghost_status():
    tor_env = os.environ.get("TOR_SOCKS", "socks5h://127.0.0.1:9050")
    vera_mount = os.environ.get("VERACRYPT_MOUNT", "/mnt/ghost_vault")
    proxies_list = [
        {"http": tor_env, "https": tor_env},
        {"http": "socks5h://host.docker.internal:9050", "https": "socks5h://host.docker.internal:9050"},
        {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
    ]
    tor_port_ok = _port_open("127.0.0.1", 9050) or _port_open("host.docker.internal", 9050)
    tor_http_ok = False
    for p in proxies_list:
        if _try_http("https://check.torproject.org/", proxies=p):
            tor_http_ok = True
            break
    direct_ok = _try_http("https://check.torproject.org/")
    vault_ok = os.path.exists(vera_mount)
    status_file = os.path.join("c:\\ProgramData\\Wazuh\\logs", "ghost_status.json")
    tracked_flag = False
    try:
        if os.path.isfile(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                j = json.load(f)
                tracked_flag = bool(j.get("tracked", False))
    except Exception:
        pass
    verdict = "Unknown"
    if tracked_flag:
        verdict = "At Risk"
    else:
        if tor_http_ok and not direct_ok and vault_ok:
            verdict = "Invisible"
        elif (not tor_http_ok) or direct_ok or (not vault_ok):
            verdict = "At Risk"
    details = {
        "tor_port": tor_port_ok,
        "tor_http": tor_http_ok,
        "direct_http": direct_ok,
        "vault_present": vault_ok,
        "tracked_flag": tracked_flag,
        "veracrypt_mount": os.environ.get("VERACRYPT_MOUNT", "/mnt/ghost_vault")
    }
    return verdict, details

st.set_page_config(page_title="AD Anomaly Hunter", layout="wide")
st.title("AD Anomaly Hunter: Blast Radius Dashboard")

st.write("### Ghost Status")
verdict, details = check_ghost_status()
if verdict == "Invisible":
    st.success("Invisible")
elif verdict == "At Risk":
    st.error("At Risk")
else:
    st.warning("Unknown")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Tor Port", "OK" if details.get("tor_port") else "Fail")
c2.metric("Tor HTTP", "OK" if details.get("tor_http") else "Fail")
c3.metric("Direct HTTP", "Blocked" if not details.get("direct_http") else "Reachable")
c4.metric("Vault", "Present" if details.get("vault_present") else "Missing")
c5.metric("Tracked Flag", "Yes" if details.get("tracked_flag") else "No")
if st.button("Re-check Ghost Status"):
    time.sleep(0.3)
    st.rerun()

df = generate_mock_data()
df['User_Code'] = df['User'].astype('category').cat.codes
df['Target_Code'] = df['Target'].astype('category').cat.codes
features = ['EventID', 'Hour', 'User_Code', 'Target_Code']
X = df[features]
model = IsolationForest(contamination=0.03, random_state=42)
model.fit(X)
df['Decision'] = model.decision_function(X)
df['Prediction'] = pd.Series(model.predict(X)).map({-1: 'Suspected Lateral Movement', 1: 'Normal'})

st.write("### Detected Anomalies")
anomalies = df[df['Prediction'] == 'Suspected Lateral Movement'].copy()
anomalies = anomalies.sort_values('Decision')
st.dataframe(anomalies[['User', 'EventID', 'Hour', 'Target', 'Decision']])

suspects = anomalies['User'].unique().tolist()
selected_user = None
if len(suspects) > 0:
    selected_user = st.sidebar.selectbox("Suspected account", suspects)
else:
    st.sidebar.info("No suspected accounts found at current contamination level.")

def build_blast_graph(df_all, user):
    df_user = df_all[df_all['User'] == user]
    targets = df_user['Target'].unique().tolist()
    anomalous_targets = set(df_user[df_user['Prediction'] == 'Suspected Lateral Movement']['Target'].tolist())
    G = nx.Graph()
    G.add_node(user, node_type='user', bipartite=0)
    for t in targets:
        G.add_node(t, node_type='target', bipartite=1)
    for t in targets:
        edge_df = df_user[df_user['Target'] == t]
        w = int(edge_df.shape[0])
        is_anom = t in anomalous_targets
        G.add_edge(user, t, weight=w, anomaly=is_anom)
    left_nodes = [n for n, d in G.nodes(data=True) if d.get('bipartite') == 0]
    pos = nx.bipartite_layout(G, left_nodes, align='vertical', scale=1.0)
    edge_traces = []
    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        color = 'red' if d.get('anomaly') else 'rgba(150,150,150,0.4)'
        width = 2 if d.get('anomaly') else max(1, int(np.log2(d.get('weight', 1) + 1)))
        edge_traces.append(go.Scatter(x=[x0, x1], y=[y0, y1], mode='lines', line=dict(color=color, width=width), hoverinfo='none', showlegend=False))
    user_x, user_y = pos[user]
    target_x = []
    target_y = []
    target_text = []
    target_color = []
    for t in targets:
        tx, ty = pos[t]
        target_x.append(tx)
        target_y.append(ty)
        count = int(df_user[df_user['Target'] == t].shape[0])
        target_text.append(f"{t} • events: {count}")
        target_color.append('red' if t in anomalous_targets else 'blue')
    node_user = go.Scatter(x=[user_x], y=[user_y], mode='markers+text', text=[user], textposition='top center', marker=dict(size=18, color='#ff7f0e'), hovertext=[user], hoverinfo='text', name='User')
    node_targets = go.Scatter(x=target_x, y=target_y, mode='markers+text', text=targets, textposition='bottom center', marker=dict(size=14, color=target_color), hovertext=target_text, hoverinfo='text', name='Targets')
    fig = go.Figure(data=edge_traces + [node_user, node_targets])
    fig.update_layout(title="Blast Radius Map", xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation='h'))
    return fig, len(anomalous_targets)

if selected_user:
    st.write("### The Blast Radius Map")
    fig, radius_size = build_blast_graph(df, selected_user)
    col1, col2 = st.columns(2)
    col1.metric(label="Blast Radius size", value=radius_size)
    col2.metric(label="Anomalies total", value=anomalies.shape[0])
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.info("The model uses Isolation Forests to find login events deviating from baseline.")

def read_json_lines(paths):
    for p in paths:
        if os.path.isfile(p):
            out = []
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
            return out
    return []

novirus_events = read_json_lines([
    "c:\\ProgramData\\Wazuh\\logs\\novirus_events.json",
    os.path.join(os.getcwd(), "wazuh_events.json")
])

supply_events = read_json_lines([
    "c:\\ProgramData\\Wazuh\\logs\\supply_chain.json"
])

st.write("### NoVirus Events")
if len(novirus_events) > 0:
    st.dataframe(pd.DataFrame(novirus_events))
else:
    st.info("No NoVirus events found.")

st.write("### Supply Chain Events")
if len(supply_events) > 0:
    st.dataframe(pd.DataFrame(supply_events))
else:
    st.info("No supply chain events found.")

st.write("### Agentic Triage")
source_choice = st.selectbox("Source", ["NoVirus", "Supply Chain"])
src_df = pd.DataFrame(novirus_events if source_choice == "NoVirus" else supply_events)
if not src_df.empty:
    idx = st.number_input("Event index", min_value=0, max_value=len(src_df) - 1, value=0, step=1)
    selected = src_df.iloc[int(idx)].to_dict()
    verdict = analyze_threat(selected)
    st.text_area("AI Verdict", verdict, height=240)
    st.warning("Review and approve actions before execution.")

st.write("### Wazuh Context Pull")
minutes = st.slider("Lookback minutes", 5, 120, 10, step=5)
if st.button("Fetch recent Wazuh alerts"):
    try:
        alerts = fetch_recent_alerts(minutes=minutes, limit=100)
        st.dataframe(pd.DataFrame(alerts))
    except Exception as e:
        st.error(str(e))

st.write("### Safety Dashboard")
try:
    vera_mount = os.environ.get("VERACRYPT_MOUNT", "/mnt/ghost_vault")
    st.write(f"Monitoring: System logs, authentication, process events")
    st.write(f"NOT Monitoring: Vault content at {vera_mount}")
except Exception:
    pass
if st.button("Kill Switch"):
    try:
        from journalism_lab.safety.deadman import main as kill_main
        kill_main()
        try:
            from .trae.tools.anti_forensics import secure_cleanup
        except Exception:
            from trae.tools.anti_forensics import secure_cleanup
        staging = os.environ.get("STAGING_DIR", os.path.join(os.environ.get("VERACRYPT_MOUNT", "/mnt/ghost_vault"), "intake", "staging"))
        secure_cleanup(staging)
        st.success("Kill Switch executed")
    except Exception as e:
        st.error(str(e))
st.write("### Morning Report")
rss_url = st.text_input("RSS feed URL", "https://isc.sans.edu/rssfeed.xml")
if st.button("Generate briefing"):
    feed = feedparser.parse(rss_url)
    items = [e.title for e in feed.entries[:5]] if hasattr(feed, "entries") else []
    summary = summarize_news(items)
    st.text_area("Briefing", summary, height=240)
st.write("### News Feeds")
default_feeds = [
    "https://isc.sans.edu/rssfeed.xml",
    "https://krebsonsecurity.com/feed/",
    "https://www.whonix.org/blog/feed/",
    "https://theintercept.com/feed/?rss"
]
sel = st.multiselect("Select feeds", default_feeds, default_feeds)
if st.button("Fetch news"):
    rows = []
    for url in sel:
        ok = False
        try:
            tor_env = os.environ.get("TOR_SOCKS", "socks5h://127.0.0.1:9050")
            proxies = {"http": tor_env, "https": tor_env}
            r = requests.get(url, proxies=proxies, timeout=15, headers={"User-Agent": "curl/7.88"})
            if r.status_code == 200:
                f = feedparser.parse(r.content)
                for e in f.entries[:10]:
                    rows.append({"feed": url, "title": getattr(e, "title", ""), "link": getattr(e, "link", "")})
                ok = True
        except Exception:
            pass
        if not ok:
            try:
                f = feedparser.parse(url)
                for e in f.entries[:5]:
                    rows.append({"feed": url, "title": getattr(e, "title", ""), "link": getattr(e, "link", "")})
            except Exception:
                pass
    if rows:
        df_news = pd.DataFrame(rows)
        st.dataframe(df_news)
        if st.button("Summarize top items"):
            titles = [r["title"] for r in rows[:10]]
            summ = summarize_news(titles)
            st.text_area("Summary", summ, height=240)

st.write("### Proposals (HITL)")
pending = list_proposals(status="pending")
if len(pending) == 0:
    st.info("No pending proposals.")
else:
    for p in pending[:10]:
        st.json(p)
        c1, c2 = st.columns(2)
        if c1.button(f"Approve {p.get('id')}", key=f"approve_{p.get('id')}"):
            decide_proposal(p.get("id"), "approved")
            st.success(f"Approved proposal {p.get('id')}")
        if c2.button(f"Deny {p.get('id')}", key=f"deny_{p.get('id')}"):
            decide_proposal(p.get("id"), "denied")
            st.warning(f"Denied proposal {p.get('id')}")

st.write("### AIBOM (AI Bill of Materials)")
if st.button("Generate AIBOM"):
    out_path = os.path.join(os.getcwd(), "aibom.json")
    write_aibom(out_path)
    try:
        with open(out_path, "r", encoding="utf-8") as f:
            data = f.read()
        st.text_area("AIBOM", data, height=240)
        st.download_button("Download AIBOM", data, file_name="aibom.json", mime="application/json")
    except Exception as e:
        st.error(str(e))

st.write("### Security Agent (MCP)")
limit = st.slider("Critical alerts limit", 1, 25, 5, step=1)
min_level = st.slider("Minimum Wazuh level", 1, 15, 12, step=1)
minutes_mcp = st.slider("Lookback minutes (MCP)", 5, 240, 120, step=5)
if st.button("Get critical alerts via MCP"):
    try:
        from mcp.wazuh_mcp import get_critical_alerts
        crit = get_critical_alerts(limit=limit, minutes=minutes_mcp, min_level=min_level)
        st.dataframe(pd.DataFrame(crit))
        titles = []
        for a in crit:
            rule = a.get("rule", {})
            desc = rule.get("description") if isinstance(rule, dict) else ""
            if desc:
                titles.append(desc)
        if titles:
            reasoning = summarize_news(titles)
            st.text_area("AI Reasoning", reasoning, height=240)
    except Exception as e:
        st.error(str(e))

ip_to_block = st.text_input("IP to block (HITL proposal)")
if st.button("Submit block IP proposal via MCP"):
    try:
        from mcp.wazuh_mcp import block_ip
        if ip_to_block.strip():
            resp = block_ip(ip_to_block.strip(), reason="Requested from Streamlit MCP UI")
            st.json(resp)
        else:
            st.warning("Enter a valid IP")
    except Exception as e:
        st.error(str(e))
