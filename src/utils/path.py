from kivy import platform
from plyer import storagepath


def app_storage_path() -> str:
    if platform == 'android':
        from android.storage import \
            app_storage_path as \
            android_app_storage_path  # pylint: disable=import-error
        return android_app_storage_path()
    return storagepath.get_application_dir()
