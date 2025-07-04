import uuid
from project.mcp.messageBus import MessageBus
from project.documentParsers.parsers import DocumentParser

class IngestionAgent:
    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.name = "IngestionAgent"
        self.bus.subscribe(self.name, self.handle_message)
        self.parser = DocumentParser()

    def handle_message(self, msg):
        if msg["type"] == "QUERY" and msg["receiver"] == self.name:
            trace_id = msg["trace_id"]
            doc_path = msg["payload"]["doc_path"]
            chunks = self.parser.parse(doc_path)
            # send parsed chunks to RetrievalAgent
            response = {
                "sender": self.name,
                "receiver": "RetrievalAgent",
                "type": "INGESTION_RESULT",
                "trace_id": trace_id,
                "payload": {
                    "chunks": chunks,
                    "source": doc_path
                }
            }
            print("InjestionAgent: Parsed chunks from document:", response)
            self.bus.send(response)

