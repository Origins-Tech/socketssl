import select
import sys
from enum import Enum
from queue import Queue
from threading import Event

HEADER = 64


class Role(int, Enum):
    SENDER = 0
    MIDDLEWARE = 1
    RECEIVER = 2


def async_input(stop_event: Event, prompt: str = "") -> str | None:
    print(prompt, end='', flush=True)
    while not stop_event.is_set():
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            if (text := sys.stdin.readline().strip()) == "[DISCONNECT]":
                return text.__repr__()
            return text


class PeekableQueue(Queue):
    def peek(self):
        with self.mutex:
            if self.queue:
                return self.queue[0]
            return None
