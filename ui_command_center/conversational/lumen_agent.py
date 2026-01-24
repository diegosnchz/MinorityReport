
# ui_command_center/conversational/lumen_agent.py
import panel as pn
import pandas as pd
import numpy as np
import random

# Initializing Panel Extension for Chat Interface
pn.extension()

class LumenAgent:
    """
    Conversational Agent for The Evasion Protocol.
    Translates NLP queries into Data Filters and Visualization Requests.
    """
    def __init__(self):
        # Mocking the Prediction DataFrame (Output of Phase 2)
        dates = pd.date_range(start='2026-01-24', periods=100, freq='H')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'risk_score': np.random.uniform(0, 1, 100),
            'sector': np.random.choice(['Sector-4', 'Sector-7', 'Sector-9'], 100),
            'predicted_route': [f"Route-{i}" for i in range(100)]
        })
        
        self.chat_feed = pn.WidgetBox(height=400, scroll=True, css_classes=['chat-box'])

    def process_query(self, query):
        """
        NLU Logic (Simple Heuristic for Demo).
        """
        query = query.lower()
        response_cards = []

        # 1. Temporal Analysis Intent
        if "risk" in query and "sector" in query:
            # "Analiza el riesgo del Sector 4..."
            sector = "Sector-4" if "4" in query else "Sector-7"
            subset = self.df[self.df['sector'] == sector]
            avg_risk = subset['risk_score'].mean()
            
            # Create a Mini-KPI Card
            card = pn.pane.Markdown(
                f"""
                <div style="background: #0f172a; padding: 10px; border-left: 4px solid #ef4444; color: white;">
                    <strong>RISK REPORT: {sector}</strong><br>
                    Average Probability: {avg_risk:.2%}<br>
                    Status: {'CRITICAL' if avg_risk > 0.5 else 'STABLE'}
                </div>
                """
            )
            return card

        # 2. Escape Route Intent
        elif "route" in query or "escape" in query:
            # "Show escape routes"
            top_route = self.df.sort_values('risk_score', ascending=False).iloc[0]['predicted_route']
            return pn.pane.Markdown(f"**Tactical AI**: Most probable evasion vector identified: `{top_route}` based on GAT topology.")

        # Default
        else:
            return pn.pane.Markdown(f"**Lumen**: Listening. Protocols available: [Risk Analysis], [Route Prediction].")

    def view(self):
        """Returns the chat interface component."""
        text_input = pn.widgets.TextInput(placeholder="Ask tactical computer...")
        
        def send(event):
            user_msg = text_input.value
            if not user_msg: return
            
            # User Message
            self.chat_feed.append(pn.pane.Markdown(f"**Operator**: {user_msg}", style={'color': '#38bdf8'}))
            text_input.value = ""
            
            # Bot Response
            response = self.process_query(user_msg)
            self.chat_feed.append(response)

        text_input.param.watch(send, 'value')
        
        layout = pn.Column(
            pn.pane.Markdown("### LUMEN TACTICAL AGENT"),
            self.chat_feed,
            text_input
        )
        return layout

# Serve
agent = LumenAgent()
if __name__.startswith("bokeh"):
    agent.view().servable()
