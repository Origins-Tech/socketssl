import logging
import socket
from threading import Event, Thread
from typing import Callable

from .util import HEADER, Payload, Response

logger = logging.getLogger(__name__)

class Client:

    def __init__(self, *, host: str, port: int, name: str, disconnect_event: Event,
                 callback: Callable[[Response], None] = None):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self._disconnect_event = disconnect_event
        self._callback = callback
        self._client.connect((host, port))
        if self._has_valid_name():
            logger.info(f"Connected to '{host}:{port}'")
            Thread(target=self._receive).start()
        else:
            self._client.close()
            raise Exception(f"Name '{self.name}' cannot be used as it is already taken'.")

    def send(self, destination: str, message: str) -> None:
        if not self._disconnect_event.is_set():
            if message == '[DISCONNECT]':
                message = message.__repr__()
            payload = Payload(source=self.name, destination=destination, data=message).model_dump_json().encode()
            send_length = str(len(payload)).encode()
            send_length += b' ' * (HEADER - len(send_length))
            self._client.send(send_length)
            self._client.send(payload)

    def disconnect(self) -> None:
        payload = Payload(source=self.name, destination="SERVER", data="[DISCONNECT]").model_dump_json().encode()
        send_length = str(len(payload)).encode()
        send_length += b' ' * (HEADER - len(send_length))
        self._client.send(send_length)
        self._client.send(payload)
        self._disconnect_event.set()

    def _receive(self) -> None:
        while True:
            recv_length = self._client.recv(HEADER).decode()
            if recv_length:
                payload = Payload.model_validate_json(self._client.recv(int(recv_length)).decode())
                if payload.data == '[DISCONNECT]':
                    if self._disconnect_event.is_set():
                        self._client.close()
                        break
                    self.disconnect()
                elif self._callback:
                    self._callback(Response(payload.source, payload.destination, payload.data))

    def _has_valid_name(self):
        self.send("SERVER", self.name)
        return bool(int(self._client.recv(1).decode()))
