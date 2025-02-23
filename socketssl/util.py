import select
import sys
from dataclasses import dataclass
from threading import Event

from pydantic import BaseModel

HEADER = 64


def async_input(stop_event: Event, prompt: str = "") -> str | None:
    print(prompt, end='', flush=True)
    while not stop_event.is_set():
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.readline().strip()


class Payload(BaseModel):
    source: str
    destination: str
    data: str


@dataclass
class Response:
    source: str
    destination: str
    data: str
