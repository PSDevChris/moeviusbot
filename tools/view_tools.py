from enum import Enum
from typing import Optional

import discord

from tools.event_tools import Event


class EventButtonAction(Enum):
    SAVE = "Ja, nur speichern."
    ANNOUNCE = "Ja, sofort ankündigen."
    ABORT = "Abbrechen."


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
