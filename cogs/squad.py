import logging

import discord
from discord.ext import commands

from bot import Bot


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''

    await bot.add_cog(Squad(bot))
    logging.info("Cog: Squad loaded.")


def is_valid_game_channel():
    async def wrapper(ctx: commands.Context) -> bool:
        if not isinstance(ctx.channel, discord.TextChannel):
            return False

        if ctx.channel.category is None or ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            return False

        return True
    return commands.check(wrapper)


class Squad(commands.Cog, name='Squad'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten,
    beizutreten oder deren Status abzufragen.

    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP,
    wenn du mehr darüber wissen willst.'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None:
        logging.info('Squad unloaded.')

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
            f'<@{member}>'
            for member in self.bot.squads[ctx.channel.name].values()
            if member != ctx.author.id
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
