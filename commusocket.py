import socket, datetime

class Address(object):
    def __init__(self, ip: str, port: int):
        self.__ip, self.__port = ip, port
    @property
    def ip(self) -> str:
        return self.__ip
    @property
    def port(self) -> int:
        return self.__port

    def __repr__(self):
        return ':'.join((self.ip, str(self.port)))

    def __str__(self):
        return self.__repr__()

    def __eq__(self, __o: object) -> bool:
        return self.__repr__() == __o.__repr__()

    def __hash__(self):
        return hash(self.__repr__())

class Server(object):
    def __init__(self, owner: Address, name: str, capacity: int = 10, password: str = None):
        self.owner, self.name, self.capacity, self.password = owner, name, capacity, password

        self.__messages: list[Message] = []
        self.__users: list[Address] = []

    @property
    def users(self) -> list[Address]:
        return self.__users
    def append_user(self, user: Address):
        self.__users.append(user)
    def remove_user(self, user: Address):
        self.__users.remove(user)
    
    def is_password_protected(self) -> bool:
        return bool(self.password)

class Message(object):
    def __init__(self, author: Address, date: datetime.datetime, content: str, server: Server):
        self.__author, self.__date, self.__content, self.__server = author, date, content, server
    
    @property
    def author(self) -> Address:
        return self.__author
    @property
    def date(self) -> datetime.datetime:
        return self.__date
    @property
    def content(self) -> str:
        return self.__content
    @property
    def server(self) -> Server:
        return self.__server

    def __lt__(self, __o: object):
        return self.date < __o.date
    def __gt__(self, __o: object):
        return self.date > __o.date