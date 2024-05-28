from dataclasses import dataclass, field
from plyer import keystore
from src.common.storage import storage


@dataclass
class Login:
    email: str
    password: str
    remember: bool = False


@dataclass
class User:
    email: str
    password: str
    remember: bool = False

    @staticmethod
    def exists() -> bool:
        return storage.exists('email')

    @classmethod
    def load(cls) -> 'User':
        email = storage.get('user')['email']
        password = keystore.get_key('manga.app.read', 'password')
        return cls(email, password)

    def save(self):
        storage.put('email', email=self.email)
        keystore.set_key('manga.app.read', 'password', self.password)

    def delete(self):
        storage.delete('email')
