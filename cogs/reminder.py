import datetime as dt
import logging
from typing import Optional

import discord
from discord.ext import commands, tasks

from bot import Bot
from tools.check_tools import SpecialUser, is_special_user
from tools.converter_tools import DtString
from tools.db_tools import create_engine
from tools.embed_tools import EmbedBuilder
from tools.event_tools import Event, EventType
from tools.view_tools import EventButtonAction, ViewBuilder


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''

    await bot.add_cog(Reminder(bot))
    logging.info("Cog: Reminder loaded.")


def is_valid_game_channel():
    async def wrapper(ctx: commands.Context) -> bool:
        if not isinstance(ctx.channel, discord.TextChannel):
            return False

        if ctx.channel.category is None or ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            return False

        return True
    return commands.check(wrapper)


class Reminder(commands.Cog, name='Events'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten,
    beizutreten oder deren Status abzufragen.

    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP,
    wenn du mehr darüber wissen willst.'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.db_engine = create_engine()
        self.time_now = ''

        self.reminder_checker.start()
        logging.info('Reminder initialized.')

    async def cog_unload(self) -> None:
        self.reminder_checker.cancel()
        logging.info('Reminder unloaded.')

    async def join_event(
        self,
        event_type: str,
        ctx: commands.Context
    ) -> None:
        pass

    @commands.hybrid_group(
        name='stream',
        fallback='show',
        brief='Infos und Einstellungen zum aktuellen Stream-Reminder.'
    )
    async def _stream(self, ctx: commands.Context) -> None:
        '''Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine
        Einstellungen anpassen'''

        await ctx.defer()

        if not (events := await Event.upcoming_events()):
            await ctx.send("Es wurde noch kein Stream angekündigt, Krah Krah!")
            return

        embed = EmbedBuilder.upcoming_events(events)

        await ctx.send("Hier sind die angekündigten Streams:", embed=embed)

    @is_special_user([SpecialUser.Schnenk, SpecialUser.Hans])
    @_stream.command(name='add', brief='Fügt ein Stream Event hinzu.')
    @discord.app_commands.rename(time='zeitpunkt', title='titel')
    @discord.app_commands.describe(time='HH:MM oder TT.MM. HH:MM', title='Optionaler Titel')
    async def _add_stream(
        self,
        ctx: commands.Context,
        time: DtString,
        title: Optional[str] = ''
    ) -> None:
        await ctx.defer()

        event = Event(type=EventType.STREAM, title=title, time=time, creator=ctx.author.id)
        embed = EmbedBuilder.single_stream_announcement(event)
        view = ViewBuilder.confirm_event_preview(event)

        msg = await ctx.send("Stimmt das so?", embed=embed, view=view, ephemeral=True)

        await view.wait()

        if view.performed_action == EventButtonAction.ANNOUNCE:
            if (output_channel := self.bot.channels['stream']) is None:
                return

            await output_channel.send(embed=EmbedBuilder.single_stream_announcement(event))
            await ctx.send("Ich habe das Event angekündigt.", ephemeral=True)

        await msg.edit(view=None)

    @is_special_user([SpecialUser.Schnenk, SpecialUser.Hans])
    @commands.hybrid_group(name='announce', fallback='list', brief='Zeigt unangekündigte Events.')
    async def _announce_event(self, ctx: commands.Context) -> None:
        await ctx.defer()

        events = await Event.events_to_anounce()

        await ctx.send(embed=EmbedBuilder.events_to_be_announced(events), ephemeral=True)

    @is_special_user([SpecialUser.Schnenk, SpecialUser.Hans])
    @_announce_event.command(name='next', brief='Kündigt Stream Events an.')
    async def _announce_next_event(
        self,
        ctx: commands.Context,
    ) -> None:
        await ctx.defer()

        if (output_channel := self.bot.channels['stream']) is None:
            return

        if (event := await Event.next_event_to_anounce()) is None:
            return

        await output_channel.send(embed=EmbedBuilder.single_stream_announcement(event))

        await ctx.send("Ich habe das Event angekündigt.", ephemeral=True)

    @commands.hybrid_group(
        name='game',
        fallback='show',
        aliases=['g'],
        brief='Infos und Einstellungen zum aktuellen Coop-Reminder.'
    )
    async def _game(self, ctx: commands.Context) -> None:
        '''Hier kannst du alles über einen aktuellen Coop-Reminder herausfinden oder
        seine Einstellungen anpassen'''
        await ctx.send("Dieses Kommando ist aktuell außer Betrieb, Krah Krah!")

    @_game.command(name='add', aliases=['-a', '+'], brief='Fügt ein Coop Event hinzu.')
    @discord.app_commands.rename(time='zeitpunkt')
    @discord.app_commands.describe(time='HH:MM oder TT.MM. HH:MM')
    async def _add_game(self, ctx: commands.Context, time: str) -> None:
        await ctx.send("Dieses Kommando ist aktuell außer Betrieb, Krah Krah!")

    @commands.hybrid_command(
        name='join',
        aliases=['j'],
        brief='Tritt einem Event bei.'
    )
    async def _join(self, ctx: commands.Context) -> None:
        '''Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen,
        wenn das Event beginnt oder siche etwas ändern sollte.'''

        if ctx.channel == self.bot.channels['stream']:
            await self.join_event('stream', ctx)
        else:
            await self.join_event('game', ctx)

    @tasks.loop(seconds=5.0)
    async def reminder_checker(self):
        dt_ftm = "%d_%m_%H_%M"

        if self.time_now == dt.datetime.now().strftime(dt_ftm):
            return

        self.time_now = dt.datetime.now().strftime(dt_ftm)

        events = await Event.upcoming_events()

        for event in events:
            if event.time.strftime(dt_ftm) != self.time_now:
                continue

            logging.info("Ein Event beginnt: %s!", event.type)

            if not isinstance(
                output_channel := self.bot.channels[str(event.type)], discord.TextChannel
            ):
                logging.error('Event channel for %s no text channel!')
                return

            match event.type:
                case EventType.STREAM:
                    await output_channel.send(
                        f"Oh, ist es denn schon {event.time.strftime('%H:%M')} Uhr? "
                        "Dann ab auf https://www.twitch.tv/schnenko/ ... "
                        "der Stream fängt an, Krah Krah! "
                    )
                case 'game':
                    await output_channel.send(
                        f"Oh, ist es denn schon {event.time.strftime('%H:%M')} Uhr? "
                        f"Dann ab in den Voice-Chat, {event.title} fängt an, Krah Krah! "
                    )

            await event.mark_as_started()

    @reminder_checker.before_loop
    async def before_reminder_loop(self):
        logging.debug('Waiting for reminder time checker..')
        await self.bot.wait_until_ready()
        logging.info('Reminder time checker started!')
