# mcp/message_protocol.py
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional
import uuid
import time

class MessageType(str, Enum):
    CONTEXT_REQUEST  = "CONTEXT_REQUEST"
    CONTEXT_RESPONSE = "CONTEXT_RESPONSE"
    RETRIEVAL_RESULT = "RETRIEVAL_RESULT"
    LLM_QUERY        = "LLM_QUERY"
    LLM_ANSWER       = "LLM_ANSWER"
    ERROR            = "ERROR"

@dataclass
class MCPMessage:
    sender: str
    receiver: str
    type: MessageType
    payload: Dict[str, Any]
    traceId: str = uuid.uuid4().hex
    timestamp: float = time.time()

    def toDict(self) -> Dict[str, Any]:
        return asdict(self)
