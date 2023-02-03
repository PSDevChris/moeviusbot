import logging
import random
import datetime as dt
from discord.ext import commands, tasks
from event import Event
from bot import Bot


async def setup(bot: Bot) -> None:
    await bot.add_cog(Reminder(bot))
    logging.info("Cog: Reminder loaded.")


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
        args,
        ult=False
    ) -> None:
        # Check for super-user
        if (
            event_type == 'stream'
            and ctx.author.name not in self.bot.settings['super-users']
            and not ult
        ):
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')
            logging.warning(
                '%s wollte den Stream-Reminder einstellen.',
                ctx.author.name
            )
            return

        # No argument => Reset stream
        if len(args) == 0:
            self.events[event_type].reset()

            # Feedback
            # TODO: Wenn ein Reminder resettet wird, lass es alle im richtigen Channel wissen
            await ctx.send(
                "Danke, "
                + ctx.author.display_name
                + ", ich habe den Reminder zurückgesetzt, Krah Krah!"
            )

            logging.info(
                "Event resettet: %s - %s",
                ctx.author.name,
                event_type
            )

        # One or more arguments => Set or update stream
        else:
            # TODO: Wenn es ein Update gibt, informiere die Teilnehmer
            # First argument: Time
            event_time = args[0]

            # Second argument: Game
            game = ''

            # Check for second argument
            if len(args) == 1:
                # In case of a game, check for the channel
                if event_type == 'game':
                    # Is the channel a game channel?
                    if ctx.channel.name in self.bot.channels:
                        # Save the channel for later posts
                        self.bot.channels['game'] = ctx.channel
                        game = ctx.channel.name.replace('-', ' ').title()
                    else:
                        await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
                        logging.warning(
                            '%s wollte einen Game-Reminder im Channel %s erstellen.',
                            ctx.author.name,
                            ctx.channel.name
                        )
                        return
            # More than one argument
            else:
                game = ' '.join(args[1:])
                if event_type == 'game':
                    self.bot.channels['game'] = self.bot.guild.get_channel(
                        379345471719604236)

            # Update event
            logging.info(
                "%s hat das Event %s geupdatet.", ctx.author.name, event_type
            )
            self.events[event_type].update_event(
                '25:00' if ult else event_time, game
            )

            # Add creator to the watchlist
            logging.debug(
                "%s wurde zum Event %s hinzugefügt.", ctx.author.name, event_type
            )
            self.events[event_type].add_member(ctx.author)

            # Direct feedback for the creator
            # Stream
            if event_type == 'stream':
                if ctx.channel != self.bot.channels['stream']:
                    await ctx.send(
                        f"Ich habe einen Stream-Reminder für {event_time} "
                        "Uhr eingerichtet, Krah Krah!"
                    )

                if ult:
                    adj = random.choice([
                        'geile',
                        'saftige',
                        'knackige',
                        'wohlgeformte',
                        'kleine aber feine',
                        'prall gefüllte'
                    ])
                    obj = random.choice([
                        'Möhren',
                        'Pflaumen',
                        'Melonen',
                        'Oliven',
                        'Nüsse',
                        'Schinken'
                    ])
                    vrb = random.choice([
                        'mit Öl bepinselt und massiert',
                        'vernascht',
                        'gebürstet',
                        'gefüllt',
                        'gebuttert',
                        'geknetet'
                    ])
                    guest = f'<@{ctx.author.id}>'
                    game = f". Heute werden {adj} {obj} {vrb}, mit dabei als " \
                        f"Special-Guest: {guest}"

                # Announce the event in the right channel
                if game == 'bot':
                    await self.bot.get_channel(580143021790855178).send(
                        "Macht euch bereit für einen Stream, "
                        + f"um {event_time} Uhr wird am Bot gebastelt, Krah Krah!"
                    )
                else:
                    await self.bot.channels['stream'].send(
                        '**Kochstudio!**\n' if ult else ''
                        + '**Macht euch bereit für einen Stream!**\n'
                        + f'Wann? {event_time} Uhr\n'
                        + f'Was? {game}\n'
                        + 'Gebt mir ein !join, Krah Krah!'
                    )
            # Game
            else:
                await ctx.send(
                    '**Macht euch bereit für ein Ründchen Coop!**\n'
                    + f'Wann? {event_time} Uhr\n'
                    + f'Was? {game}\n'
                    + 'Gebt mir ein !join, Krah Krah!'
                )
                if ctx.channel.name in self.bot.squads.keys():
                    members = [
                        f'<@{member}> '
                        for member in self.bot.squads[ctx.channel.name].values()
                        if member != ctx.author.id
                    ]
                    if members:
                        await ctx.send(
                            "Das gilt insbesondere für das Squad, Krah Krah!\n"
                            + " ".join(members)
                        )

            logging.info(
                "Event-Info wurde mitgeteilt, das Squad wurde benachrichtigt."
            )

    # Process the Request for Event-Info
    async def process_event_info(
        self,
        event_type: str,
        ctx: commands.Context
    ) -> None:
        if self.events[event_type].event_time == '':
            if event_type == 'stream':
                await ctx.send("Es wurde noch kein Stream angekündigt, Krah Krah!")
            else:
                await ctx.send("Es wurde noch keine Coop-Runde angekündigt, Krah Krah!")
            logging.warning(
                "%s hat nach einem Event %s gefragt, das es nicht gibt.",
                ctx.author.name,
                event_type
            )

        # There is an event
        else:
            # Get the right words
            if event_type == 'stream':
                begin_string = "Der nächste Stream"
            else:
                begin_string = "Die nächste Coop-Runde"

            # Check for game
            if self.events[event_type].event_game == '':
                game_str = ""
            else:
                game_str = f"Gespielt wird: {self.events[event_type].event_game}. "

            # Get the members
            members = ", ".join(self.events[event_type].event_members.values())

            # Post the info
            await ctx.send(
                f"{begin_string} beginnt um {self.events[event_type].event_time} Uhr. "
                + f"{game_str}Mit dabei sind bisher: {members}, Krah Krah!"
            )
            logging.info(
                "%s hat nach einem Event %s gefragt. Die Infos dazu wurden rausgehauen.",
                ctx.author.name,
                event_type
            )

    # Join an event
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
        else:
            if ctx.author.display_name in self.events[event_type].event_members.values():
                await ctx.send(
                    "Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!"
                )
                logging.warning(
                    "%s steht bereits auf der Teilnehmerliste von Event %s.",
                    ctx.author.name,
                    event_type
                )
            else:
                self.events[event_type].add_member(ctx.author)
                await ctx.send(
                    "Alles klar, ich packe dich auf die Teilnehmerliste, Krah Krah!"
                )
                logging.info(
                    "%s wurde auf die Teilnehmerliste von Event %s hinzugefügt.",
                    ctx.author.name,
                    event_type
                )

    # Commands
    @commands.command(
        name='stream',
        aliases=['s'],
        brief='Infos und Einstellungen zum aktuellen Stream-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _stream(self, ctx: commands.Context, *args) -> None:
        '''Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine
        Einstellungen anpassen

        ?stream             Sagt dir, ob ein Stream angekündigt wurde. Falls ja, erfährst du,
                            wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer
                            sich bisher zum Stream angemeldet hat. Mehr dazu findest du in der
                            Hilfe zum join-Kommando.

        !stream             resettet den aktuellen Reminder.
        !stream hh:mm       stellt einen Reminder für die gewählte Uhrzeit ein.
        !stream hh:mm       game stellt außerdem ein, welches Spiel gespielt wird.'''

        # Stream command
        if ctx.prefix == '!':
            await self.process_event_command('stream', ctx, args)

        # Stream info
        elif ctx.prefix == '?':
            await self.process_event_info('stream', ctx)

    @commands.command(
        name='game',
        aliases=['g'],
        brief='Infos und Einstellungen zum aktuellen Coop-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _game(self, ctx: commands.Context, *args) -> None:
        '''Hier kannst du alles über einen aktuellen Coop-Reminder herausfinden oder
        seine Einstellungen anpassen

        ?game               Sagt dir, ob eine Coop-Runde angekündigt wurde. Falls ja, erfährst du,
                            wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer
                            sich bisher zum Coop angemeldet hat. Mehr dazu findest du in der
                            Hilfe zum join-Kommando.

        !game               resettet den aktuellen Reminder.
        !game               hh:mm stellt einen Reminder für die gewählte Uhrzeit im Channel ein.
        !game hh:mm game    stellt wahlweise ein Spiel ein, welches keinen eigenen Channel hat.'''

        # Game command
        if ctx.prefix == '!':
            await self.process_event_command('game', ctx, args)

        # Game info
        elif ctx.prefix == '?':
            await self.process_event_info('game', ctx)

    @commands.command(
        name='join',
        aliases=['j'],
        brief='Tritt einem Event bei.'
    )
    async def _join(self, ctx: commands.Context) -> None:
        '''Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen,
        wenn das Event beginnt oder siche etwas ändern sollte.'''

        if ctx.channel in self.bot.channels.values():
            if ctx.channel == self.bot.channels['stream']:
                await self.join_event('stream', ctx)
            else:
                await self.join_event('game', ctx)

    @commands.command(
        name='hey',
        aliases=['h'],
        brief='Informiere das Squad über ein bevorstehendes Event.'
    )
    async def _hey(self, ctx: commands.Context) -> None:
        if ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s hat das Squad außerhalb eines Spiele-Channels gerufen.",
                ctx.author.name
            )
            return

        if len(self.bot.squads[ctx.channel.name]) == 0:
            await ctx.send('Hey, hier gibt es kein Squad, Krah Krah!')
            logging.warning(
                "%s hat ein leeres Squad in %s gerufen.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        members = []
        for member in self.bot.squads[ctx.channel.name].values():
            if (member != ctx.author.id
                    and str(member) not in self.events['game'].event_members.keys()
                    ):
                members.append(f'<@{member}>')

        if len(members) == 0:
            await ctx.send("Hey, es wissen schon alle bescheid, Krah Krah!")
            logging.warning(
                "%s hat das Squad in %s gerufen aber es sind schon alle gejoint.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        await ctx.send(f"Hey Squad! Ja, genau ihr seid gemeint, Krah Krah!\n{' '.join(members)}")
        logging.info(
            "%s hat das Squad in %s gerufen.",
            ctx.author.name,
            ctx.channel.name
        )

    @commands.command(
        name='squad',
        aliases=['sq'],
        brief='Manage dein Squad mit ein paar simplen Kommandos.'
    )
    async def _squad(self, ctx: commands.Context, *args) -> None:
        '''Du willst dein Squad managen? Okay, so gehts!
        Achtung: Jeder Game-Channel hat ein eigenes Squad. Du musst also im richtigen Channel sein.

        !squad                  zeigt dir an, wer aktuell im Squad ist.
        !squad add User1 ...    fügt User hinzu. Du kannst auch mehrere User gleichzeitig
                                hinzufügen. "add me" fügt dich hinzu.
        !squad rem User1 ...    entfernt den oder die User wieder.'''

        if ctx.channel.category is None:
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s denkt, %s sei ein Spiele-Channel.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        if ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s denkt, %s sei ein Spiele-Channel.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        if len(args) == 1:
            return

        if len(args) == 0:
            if len(self.bot.squads[ctx.channel.name]) > 0:
                game = ctx.channel.name.replace('-', ' ').title()
                members = ", ".join(self.bot.squads[ctx.channel.name].keys())
                await ctx.send(
                    f"Das sind die Mitglieder im {game}-Squad, Krah Krah!\n{members}"
                )
                logging.info(
                    "%s hat das Squad in %s angezeigt: %s.",
                    ctx.author.name,
                    ctx.channel.name,
                    members
                )
            else:
                await ctx.send("Es gibt hier noch kein Squad, Krah Krah!")
                logging.warning(
                    "%s hat das Squad in %s gerufen aber es gibt keins.",
                    ctx.author.name,
                    ctx.channel.name
                )

            return

        match args[0]:
            case "add" | "a" | "+":
                for arg in args[1:]:
                    if arg == 'me':
                        member = ctx.author
                    else:
                        member = self.bot.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name
                        )
                        continue

                    if member.name in self.bot.squads[ctx.channel.name].keys():
                        await ctx.send(
                            f"{member.name} scheint schon im Squad zu sein, Krah Krah!"
                        )
                        logging.warning(
                            "%s wollte %s mehrfach zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            member.name,
                            ctx.channel.name
                        )
                        continue

                    self.bot.squads[ctx.channel.name][member.name] = member.id
                    await ctx.send(
                        f"{member.name} wurde zum Squad hinzugefügt, Krah Krah!"
                    )
                    logging.info(
                        "%s hat %s zum %s-Squad hinzugefügt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name
                    )

            case "rem" | "r" | "-":
                for arg in args[1:]:
                    if arg == 'me':
                        member = ctx.author
                    else:
                        member = self.bot.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name
                        )
                        continue

                    if member.name not in self.bot.squads[ctx.channel.name].keys():
                        await ctx.send(
                            "Das macht gar keinen Sinn. "
                            f"{member.name} ist gar nicht im Squad, Krah Krah!"
                        )
                        logging.warning(
                            "%s wollte %s aus dem %s-Squad entfernen, "
                            "aber er war nicht Mitglied.",
                            ctx.author.name,
                            member.name,
                            ctx.channel.name
                        )
                        continue

                    self.bot.squads[ctx.channel.name].pop(member.name)
                    await ctx.send(
                        f"{member.name} wurde aus dem Squad entfernt, Krah Krah!"
                    )
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
            if event.event_time == self.time_now:
                logging.info("Ein Event beginnt: %s!", event.event_type)

                members = " ".join(
                    [f"<@{id}>" for id in event.event_members.keys()]
                )

                if event.event_type == 'stream':
                    if event.event_game == 'bot':
                        await self.bot.get_channel(580143021790855178).send(
                            f"Oh, ist es denn schon {event.event_time} Uhr? "
                            "Dann ab auf https://www.twitch.tv/hanseichlp ... "
                            "es wird endlich wieder am Bot gebastelt, Krah Krah!"
                            f"Heute mit von der Partie: {members}", tts=False
                        )
                    else:
                        await self.bot.channels['stream'].send(
                            f"Oh, ist es denn schon {event.event_time} Uhr? "
                            "Dann ab auf https://www.twitch.tv/schnenko/ ... "
                            "der Stream fängt an, Krah Krah! "
                            f"Heute mit von der Partie: {members}", tts=False
                        )
                else:
                    await self.bot.channels['game'].send(
                        f"Oh, ist es denn schon {event.event_time} Uhr? Dann ab in den Voice-Chat, "
                        f"{event.event_game} fängt an, Krah Krah! "
                        f"Heute mit von der Partie: {members}", tts=False
                    )

                event.reset()
                logging.info('Event-Post abgesetzt, Timer resettet.')

    @reminder_checker.before_loop
    async def before_reminder_loop(self):
        logging.debug('Waiting for reminder time checker..')
        await self.bot.wait_until_ready()
        logging.info('Reminder time checker started!')