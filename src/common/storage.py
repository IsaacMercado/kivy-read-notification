from os.path import join

from kivy.storage.dictstore import DictStore

from src.utils.path import app_storage_path

storage = DictStore(
    join(app_storage_path(), "storage.data"),
)
