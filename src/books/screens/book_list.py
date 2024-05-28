from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
from kivy.app import App


class BookListScreen(Screen):
    books = ListProperty([])

    def on_pre_enter(self):
        self.books.extend(
            {"text": chapter.title} 
            for chapter in App.get_running_app().client_manager.get_chapters_from_url(
                'https://visortmo.com/library/manga/10465/Solanin',
            )
        )
