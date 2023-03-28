'''This module contains the classes and functions for handling events in the reminder part
of the discord bot'''

from __future__ import annotations

import datetime as dt
import logging
from enum import Enum
from typing import Any, Optional

from sqlalchemy import asc, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tools.db_tools import Base, create_engine
from tools.dt_tools import get_local_timezone

DEFAULT_TIME_FMT = '%d.%m um %H:%M Uhr'


class EventType(Enum):
    '''Enum of the supported event types'''
    GAME = "Game"
    STREAM = "Stream"

    def __str__(self) -> str:
        return self.value


class Event(Base):
    '''This class is used for events like streams or coop sessions'''

    __tablename__ = "event"

    engine = create_engine()

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[EventType]
    title: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    time: Mapped[dt.datetime]
    creator: Mapped[int]
    announced: Mapped[bool] = mapped_column(default=False)
    started: Mapped[bool] = mapped_column(default=False)

    def __init__(self, **kw: Any):
        super().__init__(**kw)

    def __repr__(self) -> str:
        return f"""User(id={self.id!r}, type={self.type!r}, title={self.title!r},
            description={self.description!r}, time={self.time!r}, creator={self.creator!r},
            announced={self.announced!r}, started={self.started!r})"""

    def __str__(self) -> str:
        return f"#{self.id:04}-{self.type}: {self.time} {self.title}"

    async def add_to_db(self) -> None:
        with Session(self.engine) as session:
            session.add(self)
            session.commit()

        logging.info('Event saved: %s', self)

    async def mark_as_started(self) -> None:
        with Session(self.engine) as session:
            self.started = True
            session.flush()

        logging.info('Event updated: %s', self)

    def to_field(self, inline: bool = False) -> dict:
        return {
            "name": str(self.type),
            "value": f"**#{self.id:04}**: {self.fmt_dt}\n{self.title}\n{self.description}",
            "inline": inline
        }

    @property
    def fmt_dt(self) -> str:
        return self.time.strftime(DEFAULT_TIME_FMT)

    @classmethod
    async def events_to_anounce(cls) -> list[Event]:
        with Session(cls.engine) as session:
            return list(session.scalars(
                select(cls).where(
                    cls.announced.is_(False)
                )
            ))

    @classmethod
    async def next_event_to_anounce(cls) -> Event | None:
        with Session(cls.engine) as session:
            return session.scalars(
                select(cls).where(
                    cls.announced.is_(False)
                ).order_by(
                    asc(cls.time)
                )
            ).first()

    @classmethod
    async def upcoming_events(cls) -> list[Event]:
        with Session(cls.engine) as session:
            return list(session.scalars(
                select(cls).where(
                    cls.time > dt.datetime.now(tz=get_local_timezone())
                ).where(
                    cls.announced.is_(True)
                ).order_by(
                    asc(cls.time)
                )
            ))


# asyncio.run(Event(type=EventType.STREAM, title='A', time=dt.datetime(
#     2023, 3, 29, 20, 15, tzinfo=get_local_timezone()), creator=1).add_to_db())

# asyncio.run(Event(type=EventType.STREAM, title='B', time=dt.datetime(
#     2023, 3, 27, 20, 15, tzinfo=get_local_timezone()), creator=2).add_to_db())
