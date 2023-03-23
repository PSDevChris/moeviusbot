import datetime as dt
import logging

import discord
from discord.ext import commands, tasks

from bot import Bot
from event import Event


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
        self.events = {
            'stream': Event('stream'),
            'game': Event('game')
        }
        self.time_now = ''
        self.reminder_checker.start()
        logging.info('Reminder initialized.')

    async def cog_unload(self) -> None:
        self.reminder_checker.cancel()
        logging.info('Reminder unloaded.')

    async def process_event_command(
        self,
        event_type: str,
        ctx: commands.Context,
        event_time: str,
        event_game: str
    ) -> None:
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if event_type == 'game':
            if ctx.channel.name not in self.bot.channels:
                await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
                logging.warning(
                    '%s wollte einen Game-Reminder im Channel %s erstellen.',
                    ctx.author.name,
                    ctx.channel.name
                )
                return

            self.bot.channels['game'] = ctx.channel
            event_game = ctx.channel.name.replace('-', ' ').title()

        logging.info(
            "%s hat das Event %s geupdatet.",
            ctx.author.name,
            event_type
        )
        self.events[event_type].update_event(event_time, event_game)

        logging.debug(
            "%s wurde zum Event %s hinzugefügt.",
            ctx.author.name,
            event_type
        )
        self.events[event_type].add_member(ctx.author)

        if event_type == 'stream' and ctx.channel != self.bot.channels['stream']:
            await ctx.send(
                f"Ich habe einen Stream-Reminder für {event_time} "
                "Uhr eingerichtet, Krah Krah!"
            )

        if (output_channel := self.bot.channels[event_type]) is None:
            return

        await output_channel.send(
            '**Macht euch bereit für einen Stream!**\n'
            if event_type == 'stream' else '**Macht euch bereit für ein Ründchen Coop!**\n'
            f'Wann? {event_time} Uhr\n'
            f'Was? {event_game}\n'
            'Gebt mir ein !join, Krah Krah!'
        )

        logging.info('Event-Info was posted.')

        if event_type != 'game' or ctx.channel.name not in self.bot.squads:
            return

        if not (members := [
            f'<@{member}> '
            for member in self.bot.squads[ctx.channel.name].values()
            if member != ctx.author.id
        ]):
            return

        await ctx.send(f'Das gilt insbesondere für das Squad, Krah Krah!\n{" ".join(members)}')
        logging.info('Squad was informedd.')

    async def process_event_info(
        self,
        event_type: str,
        ctx: commands.Context
    ) -> None:
        if self.events[event_type].event_time == '':
            type_string = ' Stream' if event_type == 'stream' else 'e Coop-Runde'
            await ctx.send(f"Es wurde noch kein{type_string} angekündigt, Krah Krah!")

            logging.warning(
                "%s hat nach einem Event %s gefragt, das es nicht gibt.",
                ctx.author.name,
                event_type
            )

            return

        begin_str = "Der nächste Stream" if event_type == 'stream' else "Die nächste Coop-Runde"

        if self.events[event_type].event_game == '':
            game_str = ""
        else:
            game_str = f"Gespielt wird: {self.events[event_type].event_game}. "

        members = ", ".join(self.events[event_type].event_members.values())

        await ctx.send(
            f"{begin_str} beginnt um {self.events[event_type].event_time} Uhr. "
            f"{game_str}Mit dabei sind bisher: {members}, Krah Krah!"
        )
        logging.info(
            "%s hat nach einem Event %s gefragt. Die Infos dazu wurden rausgehauen.",
            ctx.author.name,
            event_type
        )

    async def join_event(
        self,
        event_type: str,
        ctx: commands.Context
    ) -> None:
        if self.events[event_type].event_time == '':
            await ctx.send("Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
            logging.warning(
                "%s wollte einem Event %s beitreten, dass es nicht gibt.",
                ctx.author.name,
                event_type
            )
            return

        if ctx.author.display_name in self.events[event_type].event_members.values():
            await ctx.send("Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!")

            logging.warning(
                "%s steht bereits auf der Teilnehmerliste von Event %s.",
                ctx.author.name,
                event_type
            )
            return

        self.events[event_type].add_member(ctx.author)

        await ctx.send("Alles klar, ich packe dich auf die Teilnehmerliste, Krah Krah!")
        logging.info(
            "%s wurde auf die Teilnehmerliste von Event %s hinzugefügt.",
            ctx.author.name,
            event_type
        )

    @commands.hybrid_group(
        name='stream',
        fallback='show',
        brief='Infos und Einstellungen zum aktuellen Stream-Reminder.'
    )
    async def _stream(self, ctx: commands.Context) -> None:
        '''Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine
        Einstellungen anpassen'''

        await self.process_event_info('stream', ctx)

    @_stream.command(
        name='add',
        brief='Fügt ein Stream Event hinzu.'
    )
    async def _add_stream(self, ctx: commands.Context, time: str, game: str) -> None:
        ''''''

        await self.process_event_command('stream', ctx, time, game)

    @_stream.command(
        name='reset',
        brief='Resettet ein Stream Event.'
    )
    async def _reset_stream(self, ctx: commands.Context) -> None:
        ''''''

        self.events['stream'].reset()
        await ctx.send('Event wurde zurückgesetzt, Krah Krah!')

    @commands.hybrid_group(
        name='game',
        fallback='show',
        aliases=['g'],
        brief='Infos und Einstellungen zum aktuellen Coop-Reminder.'
    )
    async def _game(self, ctx: commands.Context) -> None:
        '''Hier kannst du alles über einen aktuellen Coop-Reminder herausfinden oder
        seine Einstellungen anpassen'''

        await self.process_event_info('game', ctx)

    @_game.command(
        name='add',
        aliases=['-a', '+'],
        brief='Fügt ein Stream Event hinzu.'
    )
    async def _add_game(self, ctx: commands.Context, time: str, game: str) -> None:
        ''''''

        await self.process_event_command('game', ctx, time, game)

    @_game.command(
        name='reset',
        aliases=['-r'],
        brief='Fügt ein Stream Event hinzu.'
    )
    async def _reset_game(self, ctx: commands.Context) -> None:
        ''''''

        self.events['game'].reset()
        await ctx.send('Event wurde zurückgesetzt, Krah Krah!')

    @commands.hybrid_command(
        name='join',
        aliases=['j'],
        brief='Tritt einem Event bei.'
    )
    async def _join(self, ctx: commands.Context) -> None:
        '''Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen,
        wenn das Event beginnt oder siche etwas ändern sollte.'''

        if ctx.channel not in self.bot.channels.values():
            return

        if ctx.channel == self.bot.channels['stream']:
            await self.join_event('stream', ctx)
        else:
            await self.join_event('game', ctx)

    @is_valid_game_channel()
    @commands.hybrid_command(
        name='hey',
        aliases=['h'],
        brief='Informiere das Squad über ein bevorstehendes Event.'
    )
    async def _hey(self, ctx: commands.Context) -> None:
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if not self.bot.squads[ctx.channel.name]:
            await ctx.send('Hey, hier gibt es kein Squad, Krah Krah!')
            logging.warning(
                "%s hat ein leeres Squad in %s gerufen.", ctx.author.name, ctx.channel.name
            )
            return

        if not (members := [
            f'<@{member}>' for member in self.bot.squads[ctx.channel.name].values()
            if (
                member != ctx.author.id
                and str(member) not in self.events['game'].event_members.keys()
            )
        ]):
            await ctx.send("Hey, es wissen schon alle bescheid, Krah Krah!")
            logging.warning(
                "%s hat das Squad in %s gerufen aber es sind schon alle gejoint.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        await ctx.send(f"Hey Squad! Ja, genau ihr seid gemeint, Krah Krah!\n{' '.join(members)}")
        logging.info("%s hat das Squad in %s gerufen.", ctx.author.name, ctx.channel.name)

    @is_valid_game_channel()
    @commands.group(
        name='squad',
        aliases=['sq'],
        brief='Manage dein Squad.'
    )
    async def _squad(self, ctx: commands.Context) -> None:
        '''Du willst dein Squad managen? Okay, so gehts!
        Achtung: Jeder Game-Channel hat ein eigenes Squad. Du musst also im richtigen Channel sein.

        !squad                  zeigt dir an, wer aktuell im Squad ist.
        !squad add User1 ...    fügt User hinzu. Du kannst auch mehrere User gleichzeitig
                                hinzufügen. "add me" fügt dich hinzu.
        !squad rem User1 ...    entfernt den oder die User wieder.'''

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if not self.bot.squads[ctx.channel.name]:
            await ctx.send("Es gibt hier noch kein Squad, Krah Krah!")
            logging.warning(
                "%s hat das Squad in %s gerufen aber es gibt keins.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        game = ctx.channel.name.replace('-', ' ').title()
        members = ", ".join(self.bot.squads[ctx.channel.name].keys())

        await ctx.send(f"Das sind die Mitglieder im {game}-Squad, Krah Krah!\n{members}")

        logging.info(
            "%s hat das Squad in %s angezeigt: %s.",
            ctx.author.name,
            ctx.channel.name,
            members
        )

    @is_valid_game_channel()
    @_squad.command(
        name='add',
        aliases=['-a', '+'],
        brief='Fügt User zum Squad hinzu.'
    )
    async def _squad_add(self, ctx: commands.Context, member: discord.Member) -> None:
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if member.name in self.bot.squads[ctx.channel.name]:
            await ctx.send(f"{member.name} scheint schon im Squad zu sein, Krah Krah!")
            logging.warning(
                "%s wollte %s mehrfach zum %s-Squad hinzuzufügen.",
                ctx.author.name,
                member.name,
                ctx.channel.name
            )
            return

        self.bot.squads[ctx.channel.name][member.name] = member.id
        await ctx.send(f"{member.name} wurde zum Squad hinzugefügt, Krah Krah!")
        logging.info(
            "%s hat %s zum %s-Squad hinzugefügt.",
            ctx.author.name,
            member.name,
            ctx.channel.name
        )

    @is_valid_game_channel()
    @_squad.command(
        name='rem',
        aliases=['-r', '-'],
        brief='Entfernt User aus dem Squad.'
    )
    async def _squad_rem(self, ctx: commands.Context, member: discord.Member) -> None:
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if member.name in self.bot.squads[ctx.channel.name]:
            await ctx.send(
                "Das macht gar keinen Sinn. {member.name} ist gar nicht im Squad, Krah Krah!"
            )
            logging.warning(
                "%s wollte %s aus dem %s-Squad entfernen, "
                "aber er war nicht Mitglied.",
                ctx.author.name,
                member.name,
                ctx.channel.name
            )
            return

        self.bot.squads[ctx.channel.name].pop(member.name)
        await ctx.send(f"{member.name} wurde aus dem Squad entfernt, Krah Krah!")
        logging.info(
            "%s hat %s aus dem %s-Squad entfernt.",
            ctx.author.name,
            member.name,
            ctx.channel.name
        )

    @tasks.loop(seconds=5.0)
    async def reminder_checker(self):
        if self.time_now == dt.datetime.now().strftime('%H:%M'):
            return

        self.time_now = dt.datetime.now().strftime('%H:%M')

        for event in self.events.values():
            if event.event_time != self.time_now:
                continue

            logging.info("Ein Event beginnt: %s!", event.event_type)

            if not isinstance(
                output_channel := self.bot.channels[event.event_type], discord.TextChannel
            ):
                logging.error('Event channel for %s no text channel!')
                return

            members = " ".join(f"<@{id}>" for id in event.event_members)

            match event.event_type:
                case 'stream':
                    await output_channel.send(
                        f"Oh, ist es denn schon {event.event_time} Uhr? "
                        "Dann ab auf https://www.twitch.tv/schnenko/ ... "
                        "der Stream fängt an, Krah Krah! "
                        f"Heute mit von der Partie: {members}"
                    )
                case 'game':
                    await output_channel.send(
                        f"Oh, ist es denn schon {event.event_time} Uhr? "
                        f"Dann ab in den Voice-Chat, {event.event_game} fängt an, Krah Krah! "
                        f"Heute mit von der Partie: {members}"
                    )

            event.reset()
            logging.info('Event-Post abgesetzt, Timer resettet.')

    @reminder_checker.before_loop
    async def before_reminder_loop(self):
        logging.debug('Waiting for reminder time checker..')
        await self.bot.wait_until_ready()
        logging.info('Reminder time checker started!')
