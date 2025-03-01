from __future__ import annotations

import logging
import socket
from threading import Thread

from .util import HEADER, Payload

logger = logging.getLogger(__name__)


class Server:
    class _Client:
        def __init__(self, client: socket.socket, name: str):
            self._client = client
            self.name = name

        def send(self, payload: Payload):
            payload = payload.model_dump_json().encode()
            send_length = str(len(payload)).encode()
            send_length += b' ' * (HEADER - len(send_length))
            self._client.send(send_length)
            self._client.send(payload)

        def receive(self, bufsize: int) -> str:
            return self._client.recv(bufsize).decode()

        def close(self):
            self._client.close()

    def __init__(self, *, host: str, port: int, num_clients: int = None):
        self.clients: list[Server._Client] = []
        self.name = "SERVER"

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        logger.info(f"Listening on '{host}:{port}'...")

        try:
            while True:
                if num_clients is None or len(self.clients) < num_clients:
                    client_socket, addr = server.accept()
                    name, is_duplicate = self._get_name(client_socket)
                    if is_duplicate:
                        logger.info(f"Client '{addr[0]}:{addr[1]}' connection blocked: Name '{name}' already taken")
                        client_socket.close()
                        continue
                    client = Server._Client(client_socket, name)
                    Thread(target=self._handle_client, args=(client, addr)).start()
                    logger.info(f"'{name}' with '{addr[0]}:{addr[1]}' connected")
                    self.clients.append(client)
                    if len(self.clients) == num_clients:
                        logger.info(f"Maximum number of clients reached: {num_clients} - Won't accept more clients")
        finally:
            for client in self.clients:
                client.send(Payload(source=self.name, destination=client.name, data='[DISCONNECT]'))

    def _handle_client(self, client: Server._Client, addr) -> None:
        while True:
            recv_length = client.receive(HEADER)
            if recv_length:
                payload = Payload.model_validate_json(client.receive(int(recv_length)))
                if payload.data == '[DISCONNECT]':
                    client.send(Payload(source=self.name, destination=payload.source, data=payload.data))
                    break
                destination = next((client_ for client_ in self.clients if client_.name == payload.destination), None)
                if destination:
                    destination.send(payload)
                    logger.info(f"Forwarded data from '{client.name}' to '{destination.name}'")

        self.clients.remove(client)
        client.close()
        logger.info(f"'{client.name}' with '{addr[0]}:{addr[1]}' disconnected")

    def _get_name(self, client: socket.socket) -> (str, bool):
        while True:
            recv_length = client.recv(HEADER).decode()
            if recv_length:
                name = Payload.model_validate_json(client.recv(int(recv_length))).data
                duplicate = next((client for client in self.clients if client.name == name), None)
                if not duplicate and name != self.name:
                    client.send("1".encode())
                    return name, False
                client.send("0".encode())
                client.close()
                return name, True
