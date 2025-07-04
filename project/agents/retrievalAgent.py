from project.mcp.messageBus import MessageBus
from project.documentParsers.parsers import DocumentParser
from project.vectorStore.faissStore import FaissStore

class RetrievalAgent:
    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.name = "RetrievalAgent"
        self.bus.subscribe(self.name, self.handle_message)
        self.store = FaissStore()

    def handle_message(self, msg):
        if msg["type"] == "INGESTION_RESULT" and msg["receiver"] == self.name:
            chunks = msg["payload"]["chunks"]
            source = msg["payload"]["source"]
            self.store.add(chunks, source)
        elif msg["type"] == "QUERY" and msg["receiver"] == self.name:
            query = msg["payload"]["query"]
            trace_id = msg["trace_id"]
            results = self.store.search(query, k=3)
            response = {
                "sender": self.name,
                "receiver": "LLMResponseAgent",
                "type": "RETRIEVAL_RESULT",
                "trace_id": trace_id,
                "payload": {
                    "retrieved_context": [r["text"] for r in results],
                    "query": query
                }
            }
            self.bus.send(response)
