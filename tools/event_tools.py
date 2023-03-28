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
        self.session = Session(create_engine(), autoflush=True, expire_on_commit=False)

    def __repr__(self) -> str:
        return f"""User(id={self.id!r}, type={self.type!r}, title={self.title!r},
            description={self.description!r}, time={self.time!r}, creator={self.creator!r},
            announced={self.announced!r}, started={self.started!r})"""

    def __str__(self) -> str:
        return f"#{self.id:04}-{self.type}: {self.time} {self.title}"

    async def add_to_db(self) -> None:
        self.session.add(self)
        self.session.commit()

        logging.info('Event saved: %s', self)

    async def mark_as_announced(self) -> None:
        with Session(create_engine()) as session, session.begin():
            if (event := session.get(Event, self.id)) is None:
                raise ValueError
            event.announced = True
            logging.info('Event updated (announced): %s', self)

    async def mark_as_started(self) -> None:
        with Session(create_engine()) as session, session.begin():
            if (event := session.get(Event, self.id)) is None:
                raise ValueError
            event.started = True
            logging.info('Event updated (started): %s', self)

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
        with Session(create_engine()) as session:
            return list(session.scalars(
                select(cls).where(
                    cls.announced.is_(False)
                )
            ))

    @classmethod
    async def next_event_to_anounce(cls) -> Event | None:
        with Session(create_engine()) as session:
            return session.scalars(
                select(cls).where(
                    cls.announced.is_(False)
                ).order_by(
                    asc(cls.time)
                )
            ).first()

    @classmethod
    async def upcoming_events(cls) -> list[Event]:
        with Session(create_engine()) as session:
            return list(session.execute(
                select(cls).where(
                    cls.started.is_(False)
                ).where(
                    cls.announced.is_(True)
                ).order_by(
                    asc(cls.time)
                )
            ).scalars())
