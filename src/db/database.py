from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


class Database:
    def __init__(self, path: str):
        self.engine = create_engine(path, connect_args={"check_same_thread": False})

        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def session(self):
        return self.Session()

    def close(self):
        self.engine.dispose()