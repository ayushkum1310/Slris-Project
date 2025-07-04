from project.mcp.messageBus import MessageBus
import uuid

class CoordinatorAgent:
    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.name = "CoordinatorAgent"
        self.bus.subscribe(self.name, self.handle_message)

    def handle_message(self, msg):
        if msg["type"] == "LLM_RESPONSE" and msg["receiver"] == self.name:
            print(f"Answer:\n{msg['payload']['answer']}")
            print(f"Sources:\n{msg['payload']['source_chunks']}")
        if msg["type"] == "USER_QUERY" and msg["receiver"] == self.name:
            trace_id = str(uuid.uuid4())
            query    = msg["payload"]["query"]

            # ingest only if user supplied a file
            if "doc_paths" in msg["payload"]:
                for doc_path in msg["payload"]["doc_paths"]:
                    ingestion_msg = {
                        "sender":   self.name,
                        "receiver": "IngestionAgent",
                        "type":     "QUERY",
                        "trace_id": trace_id,
                        "payload":  {"doc_path": doc_path},
                    }
                    self.bus.send(ingestion_msg)
                

            # always forward the question to retrieval
            self.bus.send({
                "sender":   self.name,
                "receiver": "RetrievalAgent",
                "type":     "QUERY",
                "trace_id": trace_id,
                "payload":  {"query": query},
            })
