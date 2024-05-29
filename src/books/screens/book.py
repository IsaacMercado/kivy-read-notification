from kivy import platform
from kivy.app import App
from kivy.clock import Clock
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

            Clock.schedule_once(self.capture, 3)

    def capture(self, dt):
        if self.browser:
            from kivy.clock import mainthread
            from plyer import storagepath

            @mainthread
            def save_buffer(data):
                path = storagepath.get_downloads_dir()
                filename = f'{path}/screenshot_copy.buffer'
                print(f'Saving screenshot to {filename}')
                with open(filename, 'wb') as file:
                    file.write(data)

            print(
                self.browser.capture(
                    lambda size, data: save_buffer(data) or print(size)
                )
            )

    def on_pause(self):
        if self.browser:
            self.browser.pause()
        return True

    def on_resume(self):
        if self.browser:
            self.browser.resume()
