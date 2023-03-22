import sqlalchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def create_all() -> None:
    engine = create_engine()
    Base.metadata.create_all(engine)


def create_engine() -> sqlalchemy.Engine:
    return sqlalchemy.create_engine("sqlite:///storage.db", echo=True)
