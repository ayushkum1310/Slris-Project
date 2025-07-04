from typing import Callable, Dict, List
from threading import Lock

class MessageBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = Lock()

    def subscribe(self, agent_name: str, callback: Callable):
        with self.lock:
            if agent_name not in self.subscribers:
                self.subscribers[agent_name] = []
            self.subscribers[agent_name].append(callback)

    def send(self, message: dict):
        receiver = message.get("receiver")
        with self.lock:
            callbacks = self.subscribers.get(receiver, [])
        for cb in callbacks:
            cb(message)
