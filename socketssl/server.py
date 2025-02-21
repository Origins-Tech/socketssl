import json
import socket
from threading import Thread, Event

from .util import HEADER, Role, PeekableQueue


class Server:
    def __init__(self, *, host: str, port: int, num_clients: int, data_flow: list[str]):
        if len(data_flow) < 2:
            raise Exception("Data flow needs at least 2 elements.")
        self.data_flow = data_flow
        self.queue = PeekableQueue()
        self.clients = []
        self.shutdown = Event()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"[SERVER] Listening on '{host}:{port}'...")

        try:
            while True:
                if len(self.clients) < num_clients:
                    client, addr = server.accept()
                    role, name, next_ = self._validate_role(client)
                    if role is not None:
                        client_shutdown = Event()
                        Thread(target=self._handle_client_send, args=(client, client_shutdown, name)).start()
                        Thread(target=self._handle_client_receive, args=(client, addr, client_shutdown, next_)).start()
                        print(f"[SERVER] '{addr[0]}:{addr[1]}' connected")
                        self.clients.append(client)
        except KeyboardInterrupt:
            self.shutdown.set()
            for client in self.clients:
                self._send(client, '[DISCONNECT]')

    @staticmethod
    def _send(client: socket.socket, message: str) -> None:
        send_length = str(len(message.encode())).encode()
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message.encode())

    def _handle_client_send(self, client: socket.socket, client_shutdown: Event, name: str) -> None:
        while not (self.shutdown.is_set() or client_shutdown.is_set()):
            if self.queue.peek() and self.queue.peek()[0] == name:
                self._send(client, self.queue.get()[1])

    def _handle_client_receive(self, client: socket.socket, addr, client_shutdown: Event, next_: str) -> None:
        while True:
            msg_length = client.recv(HEADER).decode()
            if msg_length:
                message = client.recv(int(msg_length)).decode()
                if message == '[DISCONNECT]':
                    self._send(client, message)
                    break
                self.queue.put((next_, message))

        client_shutdown.set()
        self.clients.remove(client)
        client.close()
        print(f"[SERVER] '{addr[0]}:{addr[1]}' disconnected")

    def _validate_role(self, client: socket.socket) -> (Role, str, str):
        while True:
            data_length = client.recv(HEADER).decode()
            if data_length:
                data: dict = json.loads(client.recv(int(data_length)).decode())
                role = data.get("role")
                if len(self.data_flow) > 2:
                    for i, name in enumerate(self.data_flow):
                        if data.get("name") == name and role == (len(self.data_flow) + i) % 3:
                            client.send("1".encode())
                            return Role(role), name, self.data_flow[i + 1] if i < len(self.data_flow) else None
                else:
                    pos = self.data_flow.index(data.get("name"))
                    if pos == 0 and role == 0:
                        client.send("1".encode())
                        return Role(role), data.get("name"), self.data_flow[1]
                    elif pos == 1 and role == 2:
                        client.send("1".encode())
                        return Role(role), data.get("name"), None
                break
        client.send("0".encode())
        client.close()
