import panel as pn
import bokeh.plotting as bp
from bokeh.models import HoverTool, ColumnDataSource
import pandas as pd
import numpy as np
import os

# Inicializar extensión
pn.extension('bokeh')

class DashboardManager:
    def __init__(self):
        self.title = "The Evasion Protocol | Hybrid Analytics"
        self.map_url = os.getenv("MAP_URL", "http://localhost:8000/map-view")

    def get_kpis(self):
        """Genera KPIs estáticos principales"""
        kpi1 = pn.indicators.Number(
            name='Evasion Success Rate', value=87.5, format='{value}%',
            colors=[(80, 'green'), (50, 'gold'), (0, 'red')]
        )
        kpi2 = pn.indicators.Number(
            name='Active Routes', value=12, format='{value}',
            colors=[(10, 'green'), (5, 'gold'), (0, 'red')]
        )
        return pn.Row(kpi1, kpi2, align='center', margin=(20, 20))

    def get_forensic_chart(self):
        """
        Gráfico Bokeh interactivo: Distancia vs Riesgo.
        """
        # Datos simulados (mock)
        data = {
            'node_id': [f'N{i}' for i in range(100)],
            'distance': np.random.uniform(0.5, 5.0, 100),
            'risk_score': np.random.beta(2, 5, 100),
            'type': np.random.choice(['Safe', 'Compromised', 'Unknown'], 100)
        }
        df = pd.DataFrame(data)
        source = ColumnDataSource(df)

        p = bp.figure(
            title="Forensic Analysis: Risk Distribution", 
            tools="pan,wheel_zoom,box_select,reset,save",
            width=800, height=400
        )
        
        # Color mapper simple
        colors = {'Safe': 'green', 'Compromised': 'red', 'Unknown': 'grey'}
        df['color'] = df['type'].map(colors)
        source = ColumnDataSource(df)

        p.circle('distance', 'risk_score', source=source, size=10, color='color', alpha=0.6, legend_field='type')
        
        p.add_tools(HoverTool(tooltips=[
            ("ID", "@node_id"),
            ("Risk", "@risk_score"),
            ("Type", "@type")
        ]))
        
        p.xaxis.axis_label = "Distance to Safehouse (km)"
        p.yaxis.axis_label = "Predicted Risk Score (GAT)"
        
        return p

    def view(self):
        """Retorna la vista completa del Dashboard"""
        back_to_map = pn.widgets.Button(name="↩ Volver al mapa", button_type="primary")
        back_to_map.js_on_click(code=f"window.location.href = '{self.map_url}';")

        template = pn.template.FastListTemplate(
            title=self.title,
            sidebar=[
                pn.pane.Markdown("## Controls"),
                back_to_map,
                pn.widgets.Select(name="Sector", options=['Sector 4', 'Usera', 'Castellana']),
                pn.widgets.Button(name="Run Optimization", button_type="primary")
            ],
            main=[
                pn.Row(self.get_kpis()),
                pn.Column(self.get_forensic_chart())
            ],
            theme="dark",
            header_background="#0f172a"
        )
        return template

# Entry point para `panel serve`
def create_app():
    dashboard = DashboardManager()
    return dashboard.view()

if __name__ == "__main__":
    create_app().servable()
