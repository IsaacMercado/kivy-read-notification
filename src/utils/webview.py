from typing import Callable

from android.runnable import run_on_ui_thread
from jnius import PythonJavaClass, autoclass, cast, java_method
from kivy.uix.modalview import ModalView
from kivy.graphics.texture import Texture

WebViewAndroid = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
LinearLayout = autoclass('android.widget.LinearLayout')
KeyEvent = autoclass('android.view.KeyEvent')
ViewGroup = autoclass('android.view.ViewGroup')
DownloadManager = autoclass('android.app.DownloadManager')
DownloadManagerRequest = autoclass('android.app.DownloadManager$Request')
Uri = autoclass('android.net.Uri')
Environment = autoclass('android.os.Environment')
Context = autoclass('android.content.Context')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
CookieManager = autoclass('android.webkit.CookieManager')


class DownloadListener(PythonJavaClass):
    # https://stackoverflow.com/questions/10069050/download-file-inside-webview
    __javacontext__ = 'app'
    __javainterfaces__ = ['android/webkit/DownloadListener']

    @java_method('(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)V')
    def onDownloadStart(
        self,
        url: str,
        userAgent: str,
        contentDisposition: str,
        mimetype: str,
        contentLength: int,
    ):
        mActivity = PythonActivity.mActivity
        context = mActivity.getApplicationContext()
        visibility = DownloadManagerRequest.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
        dir_type = Environment.DIRECTORY_DOWNLOADS
        uri = Uri.parse(url)
        filepath = uri.getLastPathSegment()
        request = DownloadManagerRequest(uri)
        request.setNotificationVisibility(visibility)
        request.setDestinationInExternalFilesDir(context, dir_type, filepath)
        dm = cast(
            DownloadManager,
            mActivity.getSystemService(Context.DOWNLOAD_SERVICE),
        )
        dm.enqueue(request)


class KeyListener(PythonJavaClass):
    __javacontext__ = 'app'
    __javainterfaces__ = ['android/view/View$OnKeyListener']

    def __init__(self, listener):
        super().__init__()
        self.listener = listener

    @java_method('(Landroid/view/View;ILandroid/view/KeyEvent;)Z')
    def onKey(self, v, key_code, event):
        if (
            event.getAction() == KeyEvent.ACTION_DOWN
            and key_code == KeyEvent.KEYCODE_BACK
        ):
            return self.listener()


class JavaScriptCallback(PythonJavaClass):
    # https://developer.android.com/reference/android/webkit/ValueCallback
    __javacontext__ = 'app'
    __javainterfaces__ = ['android/webkit/ValueCallback']

    def __init__(self, callback: Callable[[str], None]):
        super().__init__()
        self.callback = callback

    @java_method('(Ljava/lang/String;)V')
    def onReceiveValue(self, value: str):
        self.callback(value)


def bytes_to_texture(size: tuple[int], data: bytes) -> Texture:
    # https://kivy.org/doc/stable/api-kivy.graphics.texture.html
    texture = Texture.create(size=size)
    texture.blit_buffer(data, colorfmt='rgba', bufferfmt='ubyte')
    texture.flip_vertical()
    return texture

class WebView(ModalView):
    # https://developer.android.com/reference/android/webkit/WebView

    def __init__(
        self,
        url: str,
        enable_javascript: bool = False,
        enable_downloads: bool = False,
        enable_zoom: bool = False,
        cookies: dict = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.url = url
        self.enable_javascript = enable_javascript
        self.enable_downloads = enable_downloads
        self.enable_zoom = enable_zoom
        self.webview = None
        self.enable_dismiss = True
        self.cookies = cookies
        self.open()

    @run_on_ui_thread
    def capture(self, callback: Callable[[tuple[int], bytes], None]):
        if self.webview:
            Bitmap = autoclass("android.graphics.Bitmap")
            Bitmap.Config = autoclass("android.graphics.Bitmap$Config")
            Bitmap.CompressFormat = autoclass(
                "android.graphics.Bitmap"
                "$CompressFormat"
            )
            Canvas = autoclass("android.graphics.Canvas")
            ByteBuffer = autoclass("java.nio.ByteBuffer")

            webview = self.webview
            scale = webview.getScale()
            height = webview.getContentHeight() * scale + 0.5

            bitmap = Bitmap.createBitmap(
                webview.getWidth(),
                height,
                Bitmap.Config.ARGB_8888,
            )
            canvas = Canvas(bitmap)
            webview.draw(canvas)

            buffer = ByteBuffer.allocate(
                bitmap.getByteCount()
            )
            bitmap.copyPixelsToBuffer(buffer)
            data = (
                bitmap.getWidth(),
                bitmap.getHeight(),
            ), bytes(buffer.array())

            callback(*data)

    @run_on_ui_thread
    def on_open(self):
        mActivity = PythonActivity.mActivity
        webview = WebViewAndroid(mActivity)
        webview.setWebViewClient(WebViewClient())
        webview.getSettings().setJavaScriptEnabled(self.enable_javascript)
        webview.getSettings().setBuiltInZoomControls(self.enable_zoom)
        webview.getSettings().setDisplayZoomControls(False)
        webview.getSettings().setAllowFileAccess(True)  # default False api>29
        layout = LinearLayout(mActivity)
        layout.setOrientation(LinearLayout.VERTICAL)
        layout.addView(webview, self.width, self.height)
        mActivity.addContentView(layout, LayoutParams(-1, -1))
        webview.setOnKeyListener(KeyListener(self._back_pressed))

        if self.enable_downloads:
            webview.setDownloadListener(DownloadListener())

        self.webview = webview
        self.layout = layout

        if self.cookies:
            for key, value in self.cookies.items():
                CookieManager.getInstance().setCookie(
                    self.url, f'{key}={value}')

        try:
            webview.loadUrl(self.url)
        except Exception as e:
            print('Webview.on_open(): ' + str(e))
            self.dismiss()

    @run_on_ui_thread
    def on_dismiss(self):
        if self.enable_dismiss:
            self.enable_dismiss = False
            parent = cast(ViewGroup, self.layout.getParent())
            if parent is not None:
                parent.removeView(self.layout)
            self.webview.clearHistory()
            self.webview.clearCache(True)
            self.webview.clearFormData()
            self.webview.destroy()
            self.layout = None
            self.webview = None

    @run_on_ui_thread
    def on_size(self, instance, size):
        if self.webview:
            params = self.webview.getLayoutParams()
            params.width = self.width
            params.height = self.height
            self.webview.setLayoutParams(params)

    def evaluate_javascript(self, js: str, callback: Callable[[str], None] = None):
        if self.enable_javascript and self.webview:
            if callback is None:
                def callback(x): return x
            self.webview.evaluateJavascript(js, JavaScriptCallback(callback))

    def pause(self):
        if self.webview:
            self.webview.pauseTimers()
            self.webview.onPause()

    def resume(self):
        if self.webview:
            self.webview.onResume()
            self.webview.resumeTimers()

    def downloads_directory(self):
        # e.g. Android/data/org.test.myapp/files/Download
        dir_type = Environment.DIRECTORY_DOWNLOADS
        context = PythonActivity.mActivity.getApplicationContext()
        directory = context.getExternalFilesDir(dir_type)
        return str(directory.getPath())

    def _back_pressed(self):
        if self.webview.canGoBack():
            self.webview.goBack()
        else:
            self.dismiss()
        return True
