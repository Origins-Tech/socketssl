# Sockets Streamlined
A wrapper around the python socket library for easy streamlined use.

## Installation
```bash
pip install socketssl
```

## Usage
### Server-Side
```python
from socketssl import Server

if __name__ == "__main__":
    server = Server(host="localhost", port=9999, num_clients=3)
```

### Client-Side
```python
import threading

from socketssl import Client, async_input


def main():
    shutdown = threading.Event()
    client = Client(host="localhost", port=9999, name="<NAME>", disconnect_event=shutdown)

    try:
        while True:
            message = async_input(shutdown, "Enter message to send: ")
            if message:
                client.send("<DESTINATION>", message)
            elif message is None:
                break
    except:
        client.disconnect()


if __name__ == "__main__":
    main()
```