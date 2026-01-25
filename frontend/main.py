"""Ghost Client para el navegador - PyScript Module."""

import asyncio
import json
import random
from datetime import datetime
from typing import TYPE_CHECKING

# Constantes de umbral para validación
THREAT_HIGH_THRESHOLD = 0.6
RISK_SCORE_LOW = 0.3
RISK_SCORE_MID = 0.6
LOOP_ITERATIONS = 40
MAX_LOG_LINES = 15
SAFE_ROUTES_LIMIT = 3

# Importaciones de PyScript/Pyodide - válidas en contexto del navegador
try:
    from bokeh.embed import json_item
    from bokeh.plotting import figure
    from js import console, document, window
    from pyodide.http import pyfetch
except ImportError:
    # Para development/testing sin PyScript
    if TYPE_CHECKING:
        from bokeh.embed import json_item  # type: ignore
        from bokeh.plotting import figure  # type: ignore
        from js import console, document, window  # type: ignore
        from pyodide.http import pyfetch  # type: ignore


class GhostClient:
    def __init__(self, data):
        self.nodes = data["nodes"]
        self.links = data["links"]

        # Determine starting node: First 'hideout' location
        hideouts = [n["id"] for n in self.nodes if n.get("type") == "hideout"]
        self.current_node_id = hideouts[0] if hideouts else self.nodes[0]["id"]

        self.is_panicking = False
        self.panic_route = []
        self.panic_index = 0

        # Build adjacency maps for different relationship types
        self.adj_conecta = {}  # Physical paths
        self.social_map = {}  # KNOWS/INTERACTS_WITH
        self.vision_targets = {}  # Vision -> Location

        self.nodes_map = {n["id"]: n for n in self.nodes}

        for link in self.links:
            s, t = link["source"], link["target"]
            l_type = link.get("type", "CONECTA_CON")

            # Physical paths
            if l_type == "CONECTA_CON":
                if s not in self.adj_conecta:
                    self.adj_conecta[s] = []
                if t not in self.adj_conecta:
                    self.adj_conecta[t] = []
                self.adj_conecta[s].append(link)
                self.adj_conecta[t].append(link)

            # Social links
            elif l_type in ["KNOWS", "INTERACTS_WITH"]:
                if s not in self.social_map:
                    self.social_map[s] = []
                self.social_map[s].append(t)

            # Visions
            elif l_type == "TARGETS":
                self.vision_targets[s] = t

            link["source_pos"] = self.nodes_map[s]
            link["target_pos"] = self.nodes_map[t]

    def get_current_node(self):
        return self.nodes_map[self.current_node_id]

    async def update_risks(self):
        """Simulates dynamic network danger fluctuations for paths."""
        for link in self.links:
            if link.get("type") == "CONECTA_CON":
                variation = (random.random() - 0.5) * 0.1
                base = link.get("baseRiesgo", 0.5)
                link["riesgo"] = max(0.05, min(0.95, base + variation))

    def calculate_threat_level(self):
        """Calculates threat based on nearby Police or Visions."""
        node = self.get_current_node()
        base_threat = node.get("env_risk", 0.1)

        # Check if this location is targeted by any Vision
        for vision_id, target_loc in self.vision_targets.items():
            if target_loc == self.current_node_id:
                vision = self.nodes_map.get(vision_id)
                if vision and vision.get("status") == "OPEN":
                    base_threat += vision.get("probability", 0.5)

        return min(1.0, base_threat)

    async def move(self):
        try:
            if self.is_panicking and self.panic_index < len(self.panic_route):
                self.current_node_id = self.panic_route[self.panic_index]
                self.panic_index += 1
                if self.panic_index >= len(self.panic_route):
                    self.is_panicking = False
                    self.log("✅ EVASION SUCCESSFUL - REACHED BREEZEWAY")
            else:
                # Standard Movement: Physical paths only
                neighbors = self.adj_conecta.get(self.current_node_id, [])
                if neighbors:
                    # Avoid highest risk links
                    sorted_neighbors = sorted(
                        neighbors, key=lambda x: x.get("riesgo", 0.5)
                    )
                    link = random.choice(
                        sorted_neighbors[:2]
                    )  # Choose from 2 least risky
                    target = (
                        link["target"]
                        if link["source"] == self.current_node_id
                        else link["source"]
                    )
                    self.current_node_id = target

            node = self.get_current_node()
            self.log(f"🏃 SECTOR ENTRY: {node['name'].upper()}")
            self.update_ui()
        except Exception as e:
            console.error(f"Move error: {e}")

    def log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        new_log = f"> [{time_str}] {message}<br>"
        log_el = document.getElementById("log-content")
        if log_el:
            current_logs = log_el.innerHTML
            lines = (new_log + current_logs).split("<br>")
            log_el.innerHTML = "<br>".join(lines[:15])
            log_el.scrollTop = 0

    def update_ui(self):
        node = self.get_current_node()
        status_el = document.getElementById("status-value")
        threat_val_el = document.getElementById("threat-value")

        type_label = node.get("type", "Unknown").upper()
        if status_el:
            status_el.innerText = type_label
            status_el.style.color = (
                "#00ff95" if node["type"] in ["hideout", "blindspot"] else "#ff3e3e"
            )

        threat = self.calculate_threat_level()
        if threat_val_el:
            threat_val_el.innerText = f"{int(threat * 100)}%"
            threat_val_el.style.color = (
                "#ff3e3e" if threat > THREAT_HIGH_THRESHOLD else "#00f2ff"
            )

        window.updateDeckLayers(
            json.dumps(self.nodes), json.dumps(self.links), self.current_node_id
        )
        window.onGhostMove(node["x"] / 100, node["y"] / 100)


client = None


def trigger_panic(event=None):
    if not client:
        return
    client.log("🚨 PRE-CRIME ALERT DETECTED! INITIATING GHOST PROTOCOL...")
    # Find hideouts
    hideouts = [
        n["id"]
        for n in client.nodes
        if n["type"] == "hideout" and n["id"] != client.current_node_id
    ]
    if hideouts:
        client.panic_route = [client.current_node_id, hideouts[0]]
        client.panic_index = 0
        client.is_panicking = True
    else:
        client.log("⚠️ ALL SECTORS COMPROMISED")


window.trigger_panic = trigger_panic


def create_bokeh_chart(data):
    # Stats on Citizens per risk degree
    citizens = [n for n in data["nodes"] if n["type"] == "citizen"]
    risk_ranges = ["LOW (0-0.3)", "MED (0.3-0.6)", "HIGH (0.6-1.0)"]
    counts = [0, 0, 0]
    for c in citizens:
        score = c.get("preCrimeRiskScore", 0)
        if score < RISK_SCORE_LOW:
            counts[0] += 1
        elif score < RISK_SCORE_MID:
            counts[1] += 1
        else:
            counts[2] += 1

    p = figure(
        x_range=risk_ranges,
        height=140,
        width=280,
        title="Citizen Risk Distribution",
        toolbar_location=None,
        tools="",
        background_fill_color=None,
        border_fill_color=None,
        outline_line_color=None,
        sizing_mode="fixed",
    )

    p.vbar(x=risk_ranges, top=counts, width=0.7, color="#ff3e3e", alpha=0.8)
    p.title.text_color = "#00ff95"
    p.title.text_font_size = "9pt"
    p.title.align = "center"
    p.axis.visible = False
    p.grid.grid_line_color = None
    p.min_border = 0
    return p


async def main():
    global client
    try:
        response = await pyfetch("data.json")
        data = await response.json()
        client = GhostClient(data)

        for _ in range(LOOP_ITERATIONS):
            if hasattr(window, "deck") and hasattr(window, "Bokeh"):
                break
            await asyncio.sleep(0.5)

        window.initDeck(json.dumps(client.nodes), json.dumps(client.links))

        try:
            p = create_bokeh_chart(data)
            p_json = json_item(p, "bokeh-chart")
            js_p_json = window.JSON.parse(json.dumps(p_json))
            window.Bokeh.embed.embed_item(js_p_json)
        except Exception as be:
            console.warn(f"Bokeh display suppressed: {be}")

        client.update_ui()
        loading_el = document.getElementById("loading")
        if loading_el:
            loading_el.style.display = "none"

        client.log("GHOST CLIENT (PROTOCOL v3) ONLINE.")

        counter = 0
        while True:
            await asyncio.sleep(1)
            counter += 1
            if counter % 4 == 0:
                await client.move()
            if counter % 2 == 0:
                await client.update_risks()

    except Exception as e:
        console.error(f"FATAL: {e}")
        loading_el = document.getElementById("loading")
        if loading_el:
            loading_el.style.display = "none"


asyncio.ensure_future(main())
