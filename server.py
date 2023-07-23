import socket, threading, datetime, pickle

from typing import Optional
from commusocket import Server, Address, Message

PORT = 2422

class MainServer(object):
    def __init__(self):
        self.servers: list[Server] = []
        self.users: dict[Address, Optional[Server]] = {}
        self.clients: dict[Address, socket.socket] = {}

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        try:
            self.localIP = s.getsockname()[0]
        finally:
            s.close()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.localIP, PORT))
        self.sock.listen(5)
        print(f"Server started. Listening on {':'.join((self.localIP, str(PORT)))}...")
        while True:
            client, address = self.sock.accept()
            address_obj = Address(address[0], address[1])
            self.clients[address_obj] = client
            threading.Thread(target=self.listen_to_client, args=(client, address_obj)).start()

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
                data.split(b'/')

                if data.startswith(b"CREATE_SERVER"):
                    details: dict[str, str | int] = pickle.loads(data.split(b'|')[1])
                    self.servers.append(Server(address, details["name"], details["capacity"], details["password"]))
                    self.users[address] = self.servers[-1]
                    client.send(b"SUCCESS")
                elif data.startswith(b"GET_MASTERLIST"):
                    client.send(pickle.dumps(self.servers))
                elif data.startswith(b"JOIN_SERVER"):
                    server: Server = pickle.loads(data.split(b'|')[1])
                    server.append_user(address)
                    client.send(b"SUCCESS")
                elif data.startswith(b"QUIT_SERVER"):
                    server: Server = pickle.loads(data.split(b'|')[1])
                    server.remove_user(address)
                    client.send(b"SUCCESS")
                elif data.startswith(b"SEND_MESSAGE"):
                    message: bytes = data.split(b'|')[1]
                    for member in [self.clients[user] for user in self.users[address].users if user != address]:
                        member.send(b"SEND_MESSAGE|" + message)
            else:
                continue

    def create_server(self, client, data):
        details: dict[str, str | int] = pickle.loads(data.split(b'|')[1])
        self.servers.append(Server(address, details["name"], details["capacity"], details["password"]))
        self.users[address] = self.servers[-1]
        client.send(b"SUCCESS")

    def get_masterlist(self, client, data):
        client.send(pickle.dumps(self.servers))
        
    def join_server(self, client, data):
        ...

    def quit_server(self, client, data):
        ...

    def send_message(self, client, data):
        ...


if __name__ == "__main__":
    MainServer()