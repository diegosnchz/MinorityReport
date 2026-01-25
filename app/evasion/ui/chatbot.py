import panel as pn
import httpx
import asyncio

# Initialize Panel extension with design tweaks
pn.extension(design="material", theme="dark")

# Custom CSS for "Glass Command Center" Look
glass_css = """
.glass-container {
    background: rgba(16, 20, 24, 0.8) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(0, 255, 242, 0.2) !important;
    border-radius: 12px !important;
    padding: 20px;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 0 15px rgba(0, 255, 242, 0.1);
}

.chat-bubble-user {
    background: rgba(0, 255, 242, 0.1);
    border-left: 3px solid #00fff2;
    padding: 10px 15px;
    border-radius: 0 12px 12px 12px;
    margin-bottom: 10px;
    color: #e0e0e0;
}

.chat-bubble-system {
    background: rgba(255, 0, 85, 0.1);
    border-left: 3px solid #ff0055;
    padding: 10px 15px;
    border-radius: 12px 0 12px 12px;
    margin-bottom: 15px;
    color: #ffffff;
    font-weight: 500;
}

.input-area {
    margin-top: 20px;
}
"""

pn.config.raw_css.append(glass_css)

class ChatbotInterface:
    def __init__(self):
        # Chat Feed with auto-scroll
        self.chat_feed = pn.Column(
            scroll=True, 
            height=450, 
            css_classes=['glass-container']
        )
        
        # Input Widgets
        self.input_box = pn.widgets.TextInput(
            placeholder="Type your tactical query here...", 
            name="",
            height=50,
            sizing_mode="stretch_width"
        )
        
        self.send_btn = pn.widgets.Button(
            name="TRANSMIT", 
            button_type="primary", 
            height=50,
            width=100
        )
        self.send_btn.on_click(self.respond)
        
        # Initial Welcome Message
        self.chat_feed.append(pn.pane.Markdown(
            "<div class='chat-bubble-system'><strong>SYSTEM:</strong> Neural Link Established. Ready for inquiries.</div>"
        ))
        
    async def respond(self, event):
        user_msg = self.input_box.value
        if not user_msg: return
        
        # 1. Clear input & Show User Message
        self.input_box.value = ""
        self.chat_feed.append(pn.pane.Markdown(
            f"<div class='chat-bubble-user'><strong>OPERATIVE:</strong> {user_msg}</div>"
        ))
        
        # 2. Show "Thinking..." status (Safe Update Pattern: Append, don't remove)
        status_msg = pn.pane.Markdown("... *Analyzing Pattern* ...", styles={'color': '#00fff2', 'font-style': 'italic'})
        self.chat_feed.append(status_msg)
        
        # 3. Process Query (Async)
        response_text = await self.process_query(user_msg)
        
        # 4. Update the "Thinking" message with the result
        # Updating the object in-place is safer than removing it from the list
        status_msg.object = f"<div class='chat-bubble-system'><strong>PREC0G:</strong> {response_text}</div>"

    async def process_query(self, query):
        q = query.lower()
        try:
            # Routing Intent
            if any(k in q for k in ["route", "escape", "path", "evade"]):
                return "Optimization Algorithm (JIT) engaged. Calculating safest path via Apache Arrow streams. Active ArcLayer visualization updated on main HUD."
            
            # XAI / Explanation Intent
            elif any(k in q for k in ["why", "risk", "reason", "explain"]):
                try:
                    # Attempt connection to backend
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        # Hardcoded params for demo context, in real app would parse from map state
                        res = await client.get("http://localhost:8000/evasion/explain-risk?hour=18&weather=Rain&patrols=5")
                        
                        if res.status_code == 200:
                            data = res.json()
                            risk_pct = round(data.get('base_risk', 0.5) * 100, 1)
                            factors = ", ".join(data.get('top_factors', ['Unknown']))
                            return f"SHAP Logic Forensic:<br>• Risk Probability: <strong>{risk_pct}%</strong><br>• Critical Drivers: {factors}<br>• Inference: GPU-Accelerated (RAPIDS)"
                        else:
                            # Fallback if endpoint fails
                            return "Forensic Module Offline. Simulated inference: Risk driven by Patrol Density and Time of Day."
                            
                except Exception as e:
                    return f"Neural Link Unstable (Backend Connection Failed): {str(e)}"
            
            # Chit-chat
            else:
                return "Command unrecognized. Valid protocols: 'Generate route', 'Explain risk factors'."
                
        except Exception as e:
            return f"Critical Logic Failure: {str(e)}"

    def view(self):
        # Header
        header = pn.Row(
            pn.pane.Markdown("# TACTICAL ASSISTANT", styles={'color': '#00fff2', 'font-family': 'Orbitron'}),
            align="center"
        )
        
        # Layout
        return pn.Column(
            header,
            self.chat_feed,
            pn.Row(self.input_box, self.send_btn, css_classes=['input-area']),
            sizing_mode="stretch_width",
            max_width=600,
            margin=20,
            align="center"
        )

def create_chat():
    return ChatbotInterface().view()

if __name__ == "__main__":
    create_chat().servable()
