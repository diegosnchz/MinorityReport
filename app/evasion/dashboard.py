
import panel as pn
import pandas as pd
import numpy as np
import pydeck as pdk
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
import datetime

# Inicializar Panel con extensión DeckGL
pn.extension('deckgl', 'bokeh', 'tabulator')

# --- 1. DATA SOURCE (MOCK RAPIDS/ARROW STREAM) ---
def get_live_data():
    """Simula la obtención de datos del Core (GAT predictions)."""
    # Generar puntos aleatorios en Madrid
    n = 100
    df = pd.DataFrame({
        'lat': np.random.normal(40.4168, 0.01, n),
        'lon': np.random.normal(-3.7038, 0.01, n),
        'risk': np.random.uniform(0, 1, n),
        'id': [f"S-{i}" for i in range(n)]
    })
    return df

data = get_live_data()

# --- 2. MAPA 3D (DECK.GL) ---
def create_deck_map(df):
    """Capa de visualización geoespacial acelerada."""
    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation="risk * 1000",
        elevation_scale=1,
        radius=50,
        get_fill_color="[risk * 255, (1-risk) * 255, 100, 200]",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=40.4168,
        longitude=-3.7038,
        zoom=12,
        pitch=45,
        bearing=0
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Subject: {id}\nRisk: {risk}"},
        map_style="mapbox://styles/mapbox/dark-v11"
    )
    return r

deck_pane = pn.pane.DeckGL(create_deck_map(data), height=600, sizing_mode='stretch_width')

# --- 3. TIMELINE INTERACTIVO (BOKEH) ---
def create_timeline():
    """Análisis Forense Temporal."""
    p = figure(height=250, sizing_mode='stretch_width', title="Crime Probability Density (24h)",
               background_fill_color="#1e293b", border_fill_color="#0f172a", outline_line_color=None)
    
    x = np.linspace(0, 24, 100)
    y = np.sin(x) + np.random.normal(0, 0.1, 100)
    
    source = ColumnDataSource(data=dict(x=x, y=y))
    p.line('x', 'y', source=source, line_width=2, color="#38bdf8")
    p.add_tools(HoverTool(tooltips=[("Hour", "@x"), ("Risk", "@y")]))
    p.axis.axis_label_text_color = "#94a3b8"
    p.title.text_color = "#f8fafc"
    p.grid.grid_line_alpha = 0.1
    return p

timeline_pane = pn.pane.Bokeh(create_timeline())

# --- 4. LUMEN CHATBOT (SIMULATION) ---
chat_feed = pn.WidgetBox(height=400, scroll=True)
chat_input = pn.widgets.TextInput(placeholder="Interrogate data...")

def on_chat_send(event):
    msg = chat_input.value
    chat_feed.append(pn.pane.Markdown(f"**CDO**: {msg}", style={'color': '#38bdf8'}))
    
    # Simple NLP Switch
    response = "Querying Core..."
    if "risk" in msg.lower():
        response = f"**System**: Current Risk Level is {data['risk'].mean():.2f} (ELEVATED). Hotspot identified in Sector 7."
    elif "deploy" in msg.lower():
        response = "**System**: Deploying nearest drone squads to coordinates [40.41, -3.70]."
    else:
        response = "**System**: Command not recognized by Lumen Engine."
        
    chat_feed.append(pn.pane.Markdown(response, style={'color': '#4ade80', 'background': '#1e293b', 'padding': '10px', 'border-radius': '5px'}))
    chat_input.value = ""

chat_input.param.watch(on_chat_send, 'value')

# --- 5. LAYOUT FINAL ---
template = pn.template.FastListTemplate(
    title="THE EVASION PROTOCOL | COMMAND CENTER",
    theme="dark",
    accent_base_color="#38bdf8",
    header_background="#0f172a",
    sidebar=[
        pn.pane.Markdown("### Controls"),
        pn.widgets.FloatSlider(name="Risk Threshold", start=0, end=1, value=0.5),
        pn.widgets.Select(name="Layer Mode", options=["Heatmap", "Hexbin", "Scatter"]),
        pn.layout.Divider(),
        pn.pane.Markdown("### Lumen Protocol"),
        chat_feed,
        chat_input
    ],
    main=[
        pn.Row(deck_pane),
        pn.Row(timeline_pane)
    ]
).servable()
