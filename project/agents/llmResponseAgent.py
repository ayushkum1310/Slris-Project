from project.mcp.messageBus import MessageBus
from project.documentParsers.parsers import DocumentParser
from google import genai
class LLMResponseAgent:
    def __init__(self, bus: MessageBus, google_api_key: str):
        self.bus = bus
        self.name = "LLMResponseAgent"
        self.client = genai.Client(api_key=google_api_key)
        self.bus.subscribe(self.name, self.handle_message)

    def handle_message(self, msg):
        if msg["type"] == "RETRIEVAL_RESULT" and msg["receiver"] == self.name:
            context = msg["payload"]["retrieved_context"]
            query = msg["payload"]["query"]
            trace_id = msg["trace_id"]
            prompt = self.format_prompt(context, query)
            response_text = self.call_llm(prompt)
            response = {
                "sender": self.name,
                "receiver": "CoordinatorAgent",
                "type": "LLM_RESPONSE",
                "trace_id": trace_id,
                "payload": {
                    "answer": response_text,
                    "source_chunks": context
                }
            }
            self.bus.send(response)

    def format_prompt(self, context, query):
        context_text = "\n---\n".join(context)
        return f"Answer the question based on the following context:\n{context_text}\n\nQuestion: {query}\nAnswer:"

    def call_llm(self, prompt):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite", contents=[prompt]
        )
        return response.text.strip()
