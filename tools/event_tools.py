'''This module contains the classes and functions for handling events in the reminder part
of the discord bot'''

import datetime as dt
from enum import Enum
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tools.db_tools import Base, create_all, create_engine


class EventType(Enum):
    '''Enum of the supported event types'''
    GAME = "Game"
    STREAM = "Stream"


class Event(Base):
    '''This class is used for events like streams or coop sessions'''

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[EventType]
    title: Mapped[Optional[str]]
    time: Mapped[dt.datetime]
    creator: Mapped[int]
    announced: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, type={self.type!r}, title={self.title!r}, \
            time={self.time!r}, creator={self.creator!r}, announced={self.announced!r})"


def main() -> None:
    create_all()

    with Session(create_engine()) as session:
        session.add(Event(
            type=EventType.STREAM,
            title="Schnenko Nervt!",
            time=dt.datetime.now(),
            creator=1337
        ))

        session.commit()

        stmt = select(Event).where(Event.creator == 1337)
        events = list(session.scalars(stmt))

        str(events)
