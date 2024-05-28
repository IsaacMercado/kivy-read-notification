from dataclasses import dataclass, field
from plyer import keystore


@dataclass
class Login:
    email: str
    password: str
    remember: bool = False


@dataclass
class User:
    email: str
    password: str

    @classmethod
    def from_keystore(cls) -> 'User':
        email = keystore.get('email')
        password = keystore.get('password')
        return cls(email, password)

    def save(self):
        keystore.put('email', self.email)
        keystore.put('password', self.password)
