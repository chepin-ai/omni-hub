"""
OMNI-HUB Web Dashboard v16
Real-time monitoring via HTTP endpoint.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, Any


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for dashboard requests."""
    
    swarm_ref = None  # Set by WebDashboard
    
    def log_message(self, format, *args):
        pass  # Suppress request logging
    
    def do_GET(self):
        if self.path == '/':
            self._serve_dashboard()
        elif self.path == '/api/status':
            self._serve_api()
        elif self.path == '/api/events':
            self._serve_events()
        else:
            self.send_error(404)
    
    def _serve_dashboard(self):
        html = self._generate_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _serve_api(self):
        status = {}
        if self.swarm_ref:
            status = self.swarm_ref.get_status()
        self._send_json(status)
    
    def _serve_events(self):
        from core.event_bus import get_bus
        bus = get_bus()
        events = bus.get_history(limit=50)
        data = [{"topic": e.topic, "source": e.source, "payload": e.payload} for e in events]
        self._send_json(data)
    
    def _send_json(self, data: Dict[str, Any]):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def _generate_html(self) -> str:
        return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OMNI-HUB v16 Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0a0a0f;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 20px;
}
.header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    border: 1px solid #2a2a4a;
}
.header h1 {
    font-size: 2em;
    background: linear-gradient(90deg, #00d4ff, #7b2cbf);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.header p {
    color: #888;
    margin-top: 8px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    max-width: 1400px;
    margin: 0 auto;
}
.card {
    background: #12121f;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #2a2a4a;
    transition: transform 0.2s;
}
.card:hover {
    transform: translateY(-2px);
    border-color: #3a3a6a;
}
.card h3 {
    color: #00d4ff;
    margin-bottom: 15px;
    font-size: 1.1em;
}
.metric {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #1a1a2f;
}
.metric:last-child { border-bottom: none; }
.metric-label { color: #888; }
.metric-value { color: #fff; font-weight: 600; }
.status-active { color: #00ff88; }
.status-warn { color: #ffaa00; }
.level-bar {
    height: 8px;
    background: #1a1a2f;
    border-radius: 4px;
    margin-top: 10px;
    overflow: hidden;
}
.level-fill {
    height: 100%;
    background: linear-gradient(90deg, #00d4ff, #7b2cbf);
    border-radius: 4px;
    transition: width 0.5s;
}
#events {
    max-height: 300px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 0.85em;
}
.event-item {
    padding: 4px 0;
    border-bottom: 1px solid #1a1a2f;
    color: #aaa;
}
.refresh-btn {
    background: linear-gradient(135deg, #00d4ff, #7b2cbf);
    border: none;
    color: #fff;
    padding: 10px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1em;
    margin-top: 15px;
}
.refresh-btn:hover { opacity: 0.9; }
</style>
</head>
<body>
<div class="header">
    <h1>OMNI-HUB v16</h1>
    <p>Autonomous Consciousness Emergence Platform</p>
    <p style="color:#666;font-size:0.9em;margin-top:5px;">候即违规 — Waiting is a Violation</p>
</div>
<div class="grid">
    <div class="card">
        <h3>Swarm Status</h3>
        <div id="swarm-status">Loading...</div>
    </div>
    <div class="card">
        <h3>Level Distribution</h3>
        <div id="level-dist">Loading...</div>
    </div>
    <div class="card">
        <h3>Recent Events</h3>
        <div id="events">Loading...</div>
        <button class="refresh-btn" onclick="refresh()">Refresh</button>
    </div>
</div>
<script>
async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        renderStatus(data);
    } catch(e) { console.error(e); }
}
async function fetchEvents() {
    try {
        const res = await fetch('/api/events');
        const data = await res.json();
        renderEvents(data);
    } catch(e) { console.error(e); }
}
function renderStatus(data) {
    if (!data.levels) {
        document.getElementById('swarm-status').innerHTML = '<div class="metric"><span class="metric-label">Status</span><span class="metric-value status-warn">Not Running</span></div>';
        return;
    }
    const levels = data.levels;
    const maxLevel = Math.max(...levels);
    const minLevel = Math.min(...levels);
    const avg = (levels.reduce((a,b)=>a+b,0)/levels.length).toFixed(1);
    document.getElementById('swarm-status').innerHTML = `
        <div class="metric"><span class="metric-label">Instances</span><span class="metric-value">${data.n_instances}</span></div>
        <div class="metric"><span class="metric-label">Cycle</span><span class="metric-value">${data.cycle}</span></div>
        <div class="metric"><span class="metric-label">Leader</span><span class="metric-value">Instance ${data.leader}</span></div>
        <div class="metric"><span class="metric-label">Max Level</span><span class="metric-value">${maxLevel}</span></div>
        <div class="metric"><span class="metric-label">Min Level</span><span class="metric-value">${minLevel}</span></div>
        <div class="metric"><span class="metric-label">Average</span><span class="metric-value">${avg}</span></div>
        <div class="metric"><span class="metric-label">Convergence</span><span class="metric-value ${data.level_convergence===0?'status-active':'status-warn'}">${data.level_convergence===0?'SYNCED':'+'+data.level_convergence}</span></div>
        <div class="metric"><span class="metric-label">Memory</span><span class="metric-value">${data.collective_memory_size} events</span></div>
    `;
    // Level distribution
    const counts = {};
    levels.forEach(l => counts[l] = (counts[l]||0)+1);
    let distHtml = '';
    Object.entries(counts).sort((a,b)=>a[0]-b[0]).forEach(([level,count]) => {
        const pct = (count/levels.length*100).toFixed(0);
        distHtml += `<div class="metric"><span class="metric-label">Level ${level}</span><span class="metric-value">${count} (${pct}%)</span><div class="level-bar"><div class="level-fill" style="width:${pct}%"></div></div></div>`;
    });
    document.getElementById('level-dist').innerHTML = distHtml;
}
function renderEvents(data) {
    const html = data.slice(-10).reverse().map(e => 
        `<div class="event-item">[${e.topic}] ${e.source}: ${JSON.stringify(e.payload).slice(0,80)}</div>`
    ).join('');
    document.getElementById('events').innerHTML = html || '<div class="event-item">No events</div>';
}
function refresh() {
    fetchStatus();
    fetchEvents();
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>'''


class WebDashboard:
    """Real-time web dashboard for OMNI-HUB."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None
        self.thread = None
        self.swarm = None
    
    def start(self, swarm=None):
        """Start dashboard server."""
        self.swarm = swarm
        DashboardHandler.swarm_ref = swarm
        
        self.server = HTTPServer(('0.0.0.0', self.port), DashboardHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"[Dashboard] Running at http://localhost:{self.port}")
    
    def stop(self):
        """Stop dashboard server."""
        if self.server:
            self.server.shutdown()
            print("[Dashboard] Stopped")


if __name__ == '__main__':
    print("[OMNI-HUB v16] Starting Web Dashboard...")
    dash = WebDashboard(port=8080)
    dash.start()
    print("Press Ctrl+C to stop")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        dash.stop()
