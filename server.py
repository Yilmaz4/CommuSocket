import socket, threading, datetime, pickle

from typing import Optional
from commusocket import Server, Address, Message

PORT = 2422

class MainServer(object):
    def __init__(self):
        self.servers: list[Server] = []
        self.users: dict[Address, Optional[Server]] = {}
        self.clients: dict[Address, socket.socket] = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.get_localIP(), PORT))
        self.sock.listen(5)
        print(f"Server started. Listening on {':'.join((self.get_localIP(), str(PORT)))}...")
        while True:
            client, address = self.sock.accept()
            address_obj = Address(address[0], address[1])
            self.clients[address_obj] = client
            threading.Thread(target=self.listen_to_client, args=(client, address_obj)).start()

    @staticmethod
    def get_localIP() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        try:
            return s.getsockname()[0]
        finally:
            s.close()

    def listen_to_client(self, client: socket.socket, address: Address):
        self.users[address] = None
        while True:
            try:
                data = client.recv(1024)
            except TimeoutError:
                continue
            except ConnectionResetError:
                return
            if data:
                if data.startswith(b"CREATE_SERVER"):
                    details: dict[str, str | int] = pickle.loads(data.split(b'|')[1])
                    self.servers.append(Server(address, details["name"], details["capacity"], details["password"]))
                    self.users[address] = self.servers[-1]
                    client.send(b"SUCCESS")
                elif data.startswith(b"GET_SERVERS"):
                    client.send(pickle.dumps(self.servers))
                elif data.startswith(b"JOIN_SERVER"):
                    server: Server = pickle.loads(data.split(b'|')[1])
                    server.append_user(address)
                    client.send(b"SUCCESS")
                elif data.startswith(b"LEAVE_SERVER"):
                    server: Server = pickle.loads(data.split(b'|')[1])
                    server.remove_user(address)
                    client.send(b"SUCCESS")
                elif data.startswith(b"SEND_MESSAGE"):
                    message: bytes = data.split(b'|')[1]
                    for member in [self.clients[user] for user in self.users[address].users if user != address]:
                        member.send(b"SEND_MESSAGE|" + message)
            else:
                continue

if __name__ == "__main__":
    MainServer()