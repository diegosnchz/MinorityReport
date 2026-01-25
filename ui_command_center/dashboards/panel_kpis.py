
# ui_command_center/dashboards/panel_kpis.py
import panel as pn
import numpy as np

# Styles
CARD_STYLE = {
    'background': '#1e293b', 
    'border': '1px solid #334155', 
    'padding': '10px', 
    'border-radius': '8px',
    'color': 'white'
}

def create_kpi_card(title, value, unit, delta=None):
    """Creates a styled KPI card."""
    delta_html = ""
    if delta:
        color = "#4ade80" if delta > 0 else "#ef4444"
        arrow = "▲" if delta > 0 else "▼"
        delta_html = f"<span style='color: {color}; font-size: 0.8em;'>{arrow} {abs(delta)}%</span>"

    content = f"""
    <div style='text-align: center;'>
        <div style='color: #94a3b8; font-size: 0.9em; text-transform: uppercase;'>{title}</div>
        <div style='font-size: 2em; font-weight: bold; color: #38bdf8;'>{value} <span style='font-size: 0.5em; color: #64748b;'>{unit}</span></div>
        {delta_html}
    </div>
    """
    return pn.pane.HTML(content, styles=CARD_STYLE, width=200, height=100)

def get_realtime_kpis():
    """Returns a Row of KPI cards."""
    # Mock Real-time Data
    evasion_rate = np.random.randint(12, 25)
    gpu_latency = np.random.randint(15, 45)
    active_patrols = np.random.randint(5, 12)
    
    kpi_row = pn.Row(
        create_kpi_card("Current Evasion Rate", evasion_rate, "%", delta=-2),
        create_kpi_card("GPU Inference Latency", gpu_latency, "ms", delta=1.5),
        create_kpi_card("Active Drone Squads", active_patrols, "units"),
        sizing_mode='stretch_width'
    )
    return kpi_row

# Serveable component
if __name__.startswith("bokeh"):
    get_realtime_kpis().servable()
