from typing import Optional

import discord
from attr import dataclass
from discord.ext import commands

from tools.event_tools import Event


@dataclass
class Field():
    name: str
    value: str | None
    inline: bool = False


class EventPreviewEmbed(discord.Embed):
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        fields: Optional[list[Field]] = None
    ) -> None:
        super().__init__(color=discord.Colour(0xff00ff), title=title, description=description,)

        if fields is None:
            return

        for field in fields:
            self.add_field(**field.__dict__)


class EventPreview(discord.ui.View):
    def __init__(self, ctx: commands.Context, event: Event):
        super().__init__()
        self.ctx = ctx
        self.event = event

    async def send(self):
        preview_embed = EventPreviewEmbed(
            "Vorschau",
            fields=[
                Field("Art:", self.event.type.value),
                Field("Zeitpunkt:", self.event.time.strftime('%d.%m %H:%M')),
                Field("Titel:", self.event.title)
            ]
        )

        msg = await self.ctx.send(
            "Stimmt das so?",
            embed=preview_embed,
            view=self,
            ephemeral=True
        )

        await self.wait()
        await msg.delete()

    @discord.ui.button(label='Ja, nur speichern.', style=discord.ButtonStyle.blurple)
    async def confirm_and_save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            'Alles klar, das Event wird gespeichert.',
            ephemeral=True
        )

        await self.event.add_to_db()

        self.stop()

    @discord.ui.button(label='Ja, sofort ankündigen.', style=discord.ButtonStyle.blurple)
    async def confirm_and_announce(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            'Alles klar, das Event wird angekündigt.',
            ephemeral=True
        )

        await self.event.add_to_db()

        self.stop()

    @discord.ui.button(label='Abbrechen.', style=discord.ButtonStyle.red)
    async def abort(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            'Alles klar, das Event wird nicht gespeichert.',
            ephemeral=True
        )

        self.stop()
