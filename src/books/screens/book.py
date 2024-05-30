from kivy import platform
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.properties import ObjectProperty  # pylint: disable=no-name-in-module
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.stencilview import StencilView

if platform == 'android':
    from src.utils.webview import WebView, bytes_to_texture


class StencilAnchorLayout(AnchorLayout, StencilView):
    pass


class BookScreen(Screen):
    browser: "WebView | None" = ObjectProperty(None)

    def view_google(self):
        if platform == 'android':
            self.browser = WebView(
                'https://www.google.com',
                enable_javascript=True,
                enable_downloads=True,
                enable_zoom=True,
            )

            Clock.schedule_once(self.capture, 3)

    def capture(self, dt):
        if self.browser:
            self.browser.capture(self.set_image)

    @mainthread
    def set_image(self, size, data):
        self.ids['book_image'].texture = bytes_to_texture(size, data)

    def on_pause(self):
        if self.browser:
            self.browser.pause()
        return True

    def on_resume(self):
        if self.browser:
            self.browser.resume()
