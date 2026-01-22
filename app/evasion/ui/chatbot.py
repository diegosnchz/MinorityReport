import panel as pn

# Inicializar
pn.extension()

class ChatbotInterface:
    def __init__(self):
        self.chat_feed = pn.WidgetBox()
        self.input_box = pn.widgets.TextInput(placeholder="Ask for extraction routes...", name="Query")
        self.send_btn = pn.widgets.Button(name="Send", button_type="primary")
        self.send_btn.on_click(self.respond)
        
    def respond(self, event):
        user_msg = self.input_box.value
        if not user_msg: return
        
        # Add user message
        self.chat_feed.append(pn.pane.Markdown(f"**Operative**: {user_msg}"))
        
        # Mock Logic (Here we would connect to Lumen/LLM)
        response = self.process_query(user_msg)
        
        # Add system response
        self.chat_feed.append(pn.pane.Markdown(f"**Evasion Protocol**: {response}"))
        self.input_box.value = ""

    def process_query(self, query):
        if "safe" in query.lower():
            return "Analyzed Sector 4. Route Alpha via 'Usera Chinatown' is 92% safe. Avoid 'Castellana' due to heavy rain."
        elif "risk" in query.lower():
            return "Current system risk is MODERATE. 3 nodes have been compromised in the last hour."
        else:
            return "Query processed. Optimization running..."

    def view(self):
        return pn.Column(
            "## Evasion Assistant",
            self.chat_feed,
            pn.Row(self.input_box, self.send_btn)
        )

# Simple Panel App Wrapper
def create_chat():
    return ChatbotInterface().view()

if __name__ == "__main__":
    create_chat().servable()
