from enum import Enum
from typing import Optional

import discord

from tools.event_tools import Event, Member


class EventButtonAction(Enum):
    SAVE = "Ja, nur speichern."
    ANNOUNCE = "Ja, sofort ankündigen."
    ABORT = "Abbrechen."
    JOIN = "!join"


class EventButton(discord.ui.Button):
    def __init__(self, action: EventButtonAction, event: Event):
        self.action = action
        self.event = event

        if self.action == EventButtonAction.ABORT:
            style = discord.ButtonStyle.red
        else:
            style = discord.ButtonStyle.blurple

        super().__init__(style=style, label=self.action.value)

    async def callback(self, interaction: discord.Interaction):
        if self.view is None:
            return

        match self.action:
            case EventButtonAction.SAVE:
                await interaction.response.send_message(
                    'Alles klar, das Event wird gespeichert.',
                    ephemeral=True
                )

                await self.event.add_to_db()

            case EventButtonAction.ANNOUNCE:
                await interaction.response.send_message(
                    'Alles klar, das Event wird angekündigt.',
                    ephemeral=True
                )

                await self.event.add_to_db()

            case EventButtonAction.ABORT:
                await interaction.response.send_message(
                    'Alles klar, das Event wird nicht gespeichert.',
                    ephemeral=True
                )

            case EventButtonAction.JOIN:
                await interaction.response.send_message(
                    'Alles klar, du wirst zum Event hinzugefügt.',
                    ephemeral=True
                )
                await Member(member_id=interaction.user.id, event_id=self.event.id).add_to_db()

        self.view.performed_action = self.action

        self.view.stop()


class ConfirmEventPreview(discord.ui.View):
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.performed_action: EventButtonAction | None = None


class ViewBuilder():
    @classmethod
    def confirm_event_preview(cls, event: Event) -> ConfirmEventPreview:
        return ConfirmEventPreview().add_item(
            EventButton(EventButtonAction.SAVE, event)
        ).add_item(
            EventButton(EventButtonAction.ANNOUNCE, event)
        ).add_item(
            EventButton(EventButtonAction.ABORT, event)
        )

    @classmethod
    def join_single_event(cls, event: Event) -> discord.ui.View:
        return discord.ui.View(timeout=None).add_item(
            EventButton(EventButtonAction.JOIN, event)
        )
