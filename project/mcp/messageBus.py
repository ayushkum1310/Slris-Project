# mcp/message_bus.py
from collections import defaultdict
from queue import Queue, Empty
from threading import Thread
from typing import Callable, Dict

from .messageProtocol import MCPMessage

class MessageBus:
    """Publish / subscribe, in‑memory."""
    def __init__(self):
        self.queues: Dict[str, Queue] = defaultdict(Queue)

    def publish(self, message: MCPMessage) -> None:
        self.queues[message.receiver].put(message)

    def subscribe(self, agentName: str, handler: Callable[[MCPMessage], None]) -> None:
        def _listen():
            while True:
                try:
                    msg = self.queues[agentName].get(timeout=0.1)
                    handler(msg)
                except Empty:
                    continue
        Thread(target=_listen, daemon=True).start()
