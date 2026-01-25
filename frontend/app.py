import random
from datetime import datetime

from faker import Faker
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

# Constantes de umbral
RISK_THRESHOLD = 0.6

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="")
CORS(app)

# Inicializar Faker
fake = Faker()


# Generar datos falsos con Faker
def generate_fake_data():
    """Genera datos falsos para el grafo usando Faker."""
    nodes = []
    links = []

    # Generar ciudadanos
    for i in range(1, 7):
        nodes.append(
            {
                "id": f"CIT_{i}",
                "name": fake.name(),
                "type": "citizen",
                "born": fake.year(),
                "status": "ACTIVE",
                "job": fake.job(),
                "criminal_degree": round(random.uniform(0.1, 0.9), 2),
                "risk_seed": round(random.uniform(0.1, 0.9), 2),
                "embedding": [round(random.random(), 1) for _ in range(3)],
                "preCrimeRiskScore": round(random.uniform(0.05, 0.95), 2),
                "x": random.randint(-250, 150),
                "y": random.randint(50, 150),
                "z": 0,
            }
        )

    # Generar localizaciones
    location_types = [
        ("police", "Police Station", 0.05, 0.2),
        ("bank", "Bank", 0.3, 0.6),
        ("hideout", "Hideout", 0.7, 0.95),
        ("blindspot", "Blindspot", 0.6, 0.9),
        ("station", "Station", 0.2, 0.5),
        ("junction", "Square", 0.2, 0.4),
    ]

    for i, (loc_type, prefix, min_risk, max_risk) in enumerate(location_types, 1):
        for j in range(1, 3):
            loc_id = f"LOC_{len(nodes) - 5 + i + j}"
            nodes.append(
                {
                    "id": loc_id,
                    "name": f"{fake.street_name()} {prefix}",
                    "type": loc_type,
                    "latitude": round(fake.latitude(), 4),
                    "longitude": round(fake.longitude(), 4),
                    "env_risk": round(random.uniform(min_risk, max_risk), 2),
                    "historical_crime_count": random.randint(1, 30),
                    "x": random.randint(-250, 250),
                    "y": random.randint(-150, 150),
                    "z": 0,
                }
            )

    # Generar visiones
    for i in range(1, 3):
        nodes.append(
            {
                "id": f"VIS_{i}",
                "name": f"{fake.color_name()} Ball Prediction",
                "type": "vision",
                "probability": round(random.uniform(0.7, 0.95), 2),
                "status": random.choice(["OPEN", "CLOSED"]),
                "timestamp": fake.iso8601(),
                "model": f"{fake.word().upper()}GAN_v{random.randint(1, 3)}.{random.randint(0, 9)}",
                "x": random.randint(-50, 50),
                "y": random.randint(-50, 50),
                "z": 0,
            }
        )

    # Generar links sociales
    citizens = [n["id"] for n in nodes if n["type"] == "citizen"]
    for i in range(len(citizens) - 1):
        links.append(
            {
                "source": citizens[i],
                "target": citizens[i + 1],
                "type": random.choice(["KNOWS", "INTERACTS_WITH"]),
                "riesgo": round(random.uniform(0.1, 0.6), 2),
            }
        )

    # Generar links de visiones
    visions = [n["id"] for n in nodes if n["type"] == "vision"]
    locations = [n["id"] for n in nodes if n["type"] in ["bank", "hideout", "station"]]
    for i, vision in enumerate(visions):
        if i < len(locations):
            links.append(
                {
                    "source": vision,
                    "target": locations[i],
                    "type": "TARGETS",
                    "riesgo": round(random.uniform(0.7, 1.0), 2),
                }
            )

    # Generar conexiones físicas entre localizaciones
    loc_nodes = [
        n["id"]
        for n in nodes
        if n["type"]
        in ["bank", "station", "hideout", "blindspot", "police", "junction"]
    ]
    for i in range(len(loc_nodes) - 1):
        base_risk = round(random.uniform(0.2, 0.8), 2)
        links.append(
            {
                "source": loc_nodes[i],
                "target": loc_nodes[i + 1],
                "type": "CONECTA_CON",
                "riesgo": base_risk,
                "baseRiesgo": base_risk,
            }
        )

    # Generar algunos links adicionales aleatorios
    for _ in range(5):
        if len(loc_nodes) >= 2:
            src, tgt = random.sample(loc_nodes, 2)
            base_risk = round(random.uniform(0.2, 0.8), 2)
            links.append(
                {
                    "source": src,
                    "target": tgt,
                    "type": "CONECTA_CON",
                    "riesgo": base_risk,
                    "baseRiesgo": base_risk,
                }
            )

    return {"nodes": nodes, "links": links}


# Generar datos al inicio
GRAPH_DATA = generate_fake_data()

# Cargar datos del grafo (mantener compatibilidad)


class GhostClientLogic:
    def __init__(self, data):
        self.nodes = data["nodes"]
        self.links = data["links"]
        self.nodes_map = {n["id"]: n for n in self.nodes}
        self.current_node_id = next(
            (n["id"] for n in self.nodes if n.get("type") == "hideout"),
            self.nodes[0]["id"],
        )
        self.is_panicking = False

    def calculate_threat_level(self):
        """Calcula nivel de amenaza en la ubicación actual."""
        node = self.nodes_map.get(self.current_node_id, {})
        return min(1.0, node.get("env_risk", 0.1))

    def get_safe_routes(self):
        """Retorna rutas seguras desde la ubicación actual."""
        safe_routes = []
        for link in self.links:
            if link.get("type") == "CONECTA_CON":
                risk = link.get("riesgo", link.get("baseRiesgo", 0.5))
                if risk < RISK_THRESHOLD:
                    safe_routes.append(
                        {"from": link["source"], "to": link["target"], "risk": risk}
                    )
        return sorted(safe_routes, key=lambda x: x["risk"])[:3]


client_logic = GhostClientLogic(GRAPH_DATA)


@app.route("/")
def index():
    """Servir la página principal."""
    return render_template("index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Servir archivos estáticos (CSS, JS, etc)."""
    return send_from_directory(".", filename)


@app.route("/api/graph-data", methods=["GET"])
def get_graph_data():
    """Retornar datos del grafo."""
    return jsonify(GRAPH_DATA)


@app.route("/api/panic", methods=["POST"])
def trigger_panic():
    """Procesar alerta de pánico."""
    hideouts = [n["id"] for n in client_logic.nodes if n["type"] == "hideout"]
    safe_routes = client_logic.get_safe_routes()

    return jsonify(
        {
            "status": "alert_received",
            "timestamp": datetime.now().isoformat(),
            "safe_routes": safe_routes,
            "nearest_hideout": hideouts[0] if hideouts else None,
            "threat_level": client_logic.calculate_threat_level(),
        }
    )


@app.route("/api/move", methods=["POST"])
def move():
    """Registrar movimiento del cliente."""
    if not request.json:
        return jsonify({"status": "error", "message": "No JSON data"}), 400

    node_id = request.json.get("node_id")

    if node_id and node_id in client_logic.nodes_map:
        client_logic.current_node_id = node_id
        node = client_logic.nodes_map[node_id]
        return jsonify(
            {
                "status": "moved",
                "current_location": node["name"],
                "threat_level": client_logic.calculate_threat_level(),
            }
        )

    return jsonify({"status": "error"}), 400


@app.route("/api/status", methods=["GET"])
def get_status():
    """Obtener estado actual del cliente."""
    node = client_logic.nodes_map.get(client_logic.current_node_id, {})
    return jsonify(
        {
            "current_location": node.get("name"),
            "threat_level": client_logic.calculate_threat_level(),
            "is_panicking": client_logic.is_panicking,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/dashboard")
def dashboard():
    """Servir página del dashboard de crímenes."""
    return render_template("dashboard.html")


@app.route("/api/crimes", methods=["GET"])
def get_crimes():
    """Obtener datos de crímenes en la ciudad generados con Faker."""

    # Generar datos aleatorios de crímenes
    total_crimes = random.randint(200, 350)
    arrested = random.randint(60, 150)

    # Generar crímenes por hora (24 horas)
    crimes_by_hour = []
    for hour in range(24):
        # Más crímenes durante el día (8-22h)
        if 8 <= hour <= 22:
            count = random.randint(10, 25)
        else:
            count = random.randint(2, 10)
        crimes_by_hour.append({"hour": f"{hour:02d}:00", "count": count})

    # Generar localizaciones con crímenes
    crime_locations = []
    crime_types = [
        "Robbery",
        "Theft",
        "Assault",
        "Fraud",
        "Vandalism",
        "Burglary",
        "Pickpocketing",
        "Illegal Activities",
    ]

    for node in client_logic.nodes:
        node_type = node.get("type")

        if node_type in ["bank", "station", "hideout", "blindspot", "police"]:
            crimes_count = random.randint(5, 35)
            crime_locations.append(
                {
                    "location": node.get("name"),
                    "type": node_type,
                    "crimes": crimes_count,
                    "crime_type": random.choice(crime_types),
                    "x": node.get("x"),
                    "y": node.get("y"),
                }
            )

    # Ordenar por cantidad de crímenes y tomar top 10
    crime_locations = sorted(crime_locations, key=lambda x: x["crimes"], reverse=True)[
        :10
    ]

    crimes_data = {
        "total_crimes": total_crimes,
        "arrested_criminals": arrested,
        "crimes_by_hour": crimes_by_hour,
        "crime_locations": crime_locations,
        "timestamp": datetime.now().isoformat(),
    }
    return jsonify(crimes_data)


if __name__ == "__main__":
    print("🚀 THE GHOST - EVASION PROTOCOL STARTING...")
    print("📍 Server running at http://localhost:5000")
    print("🌐 Web interface at http://localhost:5000/")
    app.run(debug=True, port=5000, use_reloader=False)
