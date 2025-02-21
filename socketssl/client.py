import json
import socket
from threading import Event, Thread
from typing import Callable

from .util import HEADER, Role


class Client:

    def __init__(self, *, host: str, port: int, role: Role, name: str, disconnect_event: Event,
                 callback: Callable[[str], None] = None):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self.role = role
        self._disconnect_event = disconnect_event
        self._callback = callback
        self._client.connect((host, port))
        if self._has_valid_role():
            print(f"Connected to '{host}:{port}'...")
            Thread(target=self._receive).start()
        else:
            self._client.close()
            raise Exception(f"Role {self.role} is in wrong position of the data flow.")

    def send(self, message: str) -> None:
        if not self._disconnect_event.is_set():
            send_length = str(len(message.encode())).encode()
            send_length += b' ' * (HEADER - len(send_length))
            self._client.send(send_length)
            self._client.send(message.encode())

    def disconnect(self) -> None:
        self.send('[DISCONNECT]')
        self._disconnect_event.set()

    def _receive(self) -> None:
        while True:
            msg_length = self._client.recv(HEADER).decode()
            if msg_length:
                message = self._client.recv(int(msg_length)).decode()
                if message == '[DISCONNECT]':
                    if self._disconnect_event.is_set():
                        self._client.close()
                        break
                    self.disconnect()
                elif self._callback:
                    self._callback(message)

    def _has_valid_role(self) -> bool:
        self.send(json.dumps({"role": self.role, "name": self.name}))
        return bool(int(self._client.recv(1).decode()))
