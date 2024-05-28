from os.path import join

from peewee import Model as PeeweeModel
from peewee import SqliteDatabase

from src.utils.path import app_storage_path

database = SqliteDatabase(
    join(app_storage_path(), "database.db"),
)


class Model(PeeweeModel):
    class Meta:
        database = database
