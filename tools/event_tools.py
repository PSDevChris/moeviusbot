'''This module contains the classes and functions for handling events in the reminder part
of the discord bot'''

import datetime as dt
from enum import Enum
from typing import Any, Optional

from sqlalchemy.orm import Mapped, Session, mapped_column

from tools.db_tools import Base, create_engine


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
    started: Mapped[bool] = mapped_column(default=False)

    def __init__(self, **kw: Any):
        super().__init__(**kw)

        self.engine = create_engine()

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, type={self.type!r}, title={self.title!r}, \
            time={self.time!r}, creator={self.creator!r}, announced={self.announced!r}, \
            started={self.started})"

    async def add_to_db(self) -> None:
        with Session(self.engine) as session:
            session.add(self)
            session.commit()
