from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR / 'potager.db'}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
