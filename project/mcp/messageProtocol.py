from typing import TypedDict, Literal, Any, Dict

class MCPPayload(TypedDict, total=False):
    top_chunks: list[str]
    query: str
    retrieved_context: list[str]
    answer: str
    source_chunks: list[str]

class MCPMessage(TypedDict):
    sender: str
    receiver: str
    type: Literal[
        "INGESTION_RESULT",
        "RETRIEVAL_RESULT",
        "LLM_RESPONSE",
        "QUERY"
    ]
    trace_id: str
    payload: MCPPayload
