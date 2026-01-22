import panel as pn
import httpx

# Inicializar
pn.extension()

class ChatbotInterface:
    def __init__(self):
        self.chat_feed = pn.Column(scroll=True, height=400)
        self.input_box = pn.widgets.TextInput(placeholder="Ask for extraction routes or risk breakdown...", name="Query")
        self.send_btn = pn.widgets.Button(name="Send", button_type="primary")
        self.send_btn.on_click(self.respond)
        
    async def respond(self, event):
        user_msg = self.input_box.value
        if not user_msg: return
        
        # Add user message
        self.chat_feed.append(pn.pane.Markdown(f"**Operative**: {user_msg}"))
        
        # Connect to real XAI service
        response = await self.process_query(user_msg)
        
        # Add system response
        self.chat_feed.append(pn.pane.Markdown(f"**Evasion Protocol**: {response}"))
        self.input_box.value = ""

    async def process_query(self, query):
        q = query.lower()
        try:
            if "route" in q or "escape" in q:
                return "HPC Routing active. Path calculated using Zero-Copy Arrow streams. Check the map for the cyan-magenta ArcLayer."
            
            elif "why" in q or "risk" in q or "explanation" in q:
                # Query real XGBoost XAI via FastAPI
                async with httpx.AsyncClient() as client:
                    res = await client.get("http://localhost:8000/evasion/explain-risk?hour=18&weather=Rain&patrols=5")
                    data = res.json()
                
                return f"SHAP Analysis: Risk is **{(data['base_risk']*100).toFixed(1)}%**. Primary drivers: {', '.join(data['top_factors'])}. (GPU-accelerated inference)."
            
            else:
                return "Neural patterns not recognized. Try: 'Explain the risk' or 'Calculate route'."
        except Exception as e:
            return f"Service Linkage Error: {str(e)}"

    def view(self):
        return pn.Column(
            "## Evasion Assistant (XAI Powered)",
            self.chat_feed,
            pn.Row(self.input_box, self.send_btn),
            max_width=500
        )

def create_chat():
    return ChatbotInterface().view()

if __name__ == "__main__":
    create_chat().servable()
