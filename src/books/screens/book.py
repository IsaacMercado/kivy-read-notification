from kivy import platform
from kivy.app import App
from kivy.properties import ObjectProperty  # pylint: disable=no-name-in-module
from kivy.uix.screenmanager import Screen

if platform == 'android':
    from src.utils.webview import WebView


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

    def on_pause(self):
        if self.browser:
            self.browser.pause()
        return True

    def on_resume(self):
        if self.browser:
            self.browser.resume()
