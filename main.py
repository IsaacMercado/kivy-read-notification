from os import listdir
from textwrap import fill

from kivy import platform
from kivy.app import App
from kivy.properties import ObjectProperty  # pylint: disable=no-name-in-module

if platform == 'android':
    from os import mkdir
    from os.path import exists, join

    from android.storage import app_storage_path  # pylint: disable=import-error
    from jnius import autoclass

    from webview import WebView


class BrowserApp(App):
    browser: "WebView | None" = ObjectProperty(None)

    def build(self):
        if platform == 'android':
            self._create_local_file()

    def view_google(self):
        if platform == 'android':
            self.browser = WebView(
                'https://www.google.com',
                enable_javascript=True,
                enable_downloads=True,
                enable_zoom=True,
            )

    def view_local_file(self):
        if platform == 'android':
            self.browser = WebView('file://'+self.filename)

    def view_downloads(self):
        label = self.root.ids['list_downloads']

        if self.browser:
            directory = self.browser.downloads_directory()
            label.text = fill(directory, 40) + '\n'
            l = listdir(directory)
            if l:
                for file in l:
                    label.text += f'{file}\n'
            else:
                label.text = 'No files downloaded'
        else:
            label.text = 'Open a browser first'

    def on_pause(self):
        if self.browser:
            self.browser.pause()
        return True

    def on_resume(self):
        if self.browser:
            self.browser.resume()

    def _create_local_file(self):
        Environment = autoclass('android.os.Environment')
        path = join(app_storage_path(), Environment.DIRECTORY_DOCUMENTS)

        if not exists(path):
            mkdir(path)

        self.filename = join(path, 'from_space.html')

        with open(self.filename, "w") as f:
            f.write("<html>\n")
            f.write(" <head>\n")
            f.write(" </head>\n")
            f.write(" <body>\n")
            f.write("  <h1>Greetings Earthlings<h1>\n")
            f.write(" </body>\n")
            f.write("</html>\n")


if __name__ == '__main__':
    BrowserApp().run()
