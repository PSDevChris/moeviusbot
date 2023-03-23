import sqlalchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    '''This is the base class for classes that are represented as tables in the DB.'''


def create_all() -> None:
    '''This function creates all required tables in the DB.'''

    engine = create_engine()
    Base.metadata.create_all(engine)


def create_engine(db_url: str = "sqlite:///storage.db", echo: bool = True) -> sqlalchemy.Engine:
    '''This function creates and returns a DB engine.'''

    return sqlalchemy.create_engine(db_url, echo=echo)
