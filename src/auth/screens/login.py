from kivy.app import App
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from src.auth.models import User


class TextInputValidation(TextInput):
    max_length = NumericProperty(255)

    def insert_text(self, substring, from_undo=False):
        if len(self.text) > self.max_length and self.max_length > 0:
            substring = ""
        super().insert_text(substring, from_undo)

from kivy.clock import Clock
class LoginScreen(Screen):
    def on_pre_enter(self, *args):
        if User.exists():
            Clock.schedule_once(self.go_to_book_list)

    def go_to_book_list(self, *args):
        self.manager.current = 'book_list'

    def login(self, email, password, remember):
        App.get_running_app().client_manager.login(
            email=email,
            password=password,
            remember=remember,
        )
        User(email, password, remember).save()
        self.manager.current = 'book_list'
