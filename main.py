import httpx
from kivy.app import App

from src.auth.screens import *
from src.books.screens import *
from src.utils.manager import Manager


class BrowserApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_manager = Manager(
            httpx.Client(
                base_url='https://visortmo.com',
            ),
        )

    def on_pause(self):
        for screen in self.root.screens:
            if hasattr(screen, 'on_pause'):
                if not screen.on_pause():
                    return False
        return True

    def on_resume(self):
        for screen in self.root.screens:
            if hasattr(screen, 'on_resume'):
                screen.on_resume()


if __name__ == '__main__':
    BrowserApp().run()
