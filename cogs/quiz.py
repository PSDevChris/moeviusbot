import json
import random
import discord
from discord.ext import commands

from myfunc import log, load_file, gcts

def setup(bot):
    bot.add_cog(Quiz(bot))
    log("Cog: Quiz geladen.")

# Check for user is Super User
def is_super_user():
    settings = load_file('settings')

    async def wrapper(ctx):
        return ctx.author.name in settings['super-users']
    return commands.check(wrapper)

class Quiz(commands.Cog, name='Quiz'):
    def __init__(self, bot):
        self.bot = bot

        self.player = None
        self.channel = None
        self.game_stage = 0
        self.question = None
        self.quiz = None

        self.stages = [50, 100, 200, 300, 500,
                1000, 2000, 4000, 8000, 16000,
                32000, 64000, 125000, 250000, 500000, 1000000]

        log("Game-Stages geladen.")

    async def get_random_question(self):
        while True:
            question = random.choice(self.quiz)

            if (self.stages[self.game_stage] >= question['range'][0] and
                self.stages[self.game_stage] <= question['range'][1]):
                random.shuffle(question['answers'])

                self.question = {"question": question['question'],
                            "category": question['category'],
                            "answers": dict(zip(['A', 'B', 'C', 'D'], question['answers']))
                        }

                return

    async def get_question_output(self):
        embed = discord.Embed(
                title=self.question['question'],
                colour=discord.Colour(0xff00ff),
                description="\n".join([
                        *map(lambda a: f"{a[0]}: {a[1]['text']}",
                        self.question['answers'].items())
                    ])
            )
        return({
                "content": f"**Frage {self.game_stage + 1} - "
                    + f"{self.stages[self.game_stage]}🕊**\n"
                    + f"Kategorie: {self.question['category']}",
                "embed": embed
            })

    async def stop_quiz(self):
        self.player = None
        self.channel = None
        self.game_stage = 0

    async def update_ranking(self, amount):
        ranking = {}
        player_id = str(self.player.id)

        try:
            with open('quiz_ranking.json', 'r') as file:
                ranking = json.load(file)
        finally:
            with open('quiz_ranking.json', 'w') as file:
                try:
                    ranking[player_id]['name'] = self.player.display_name
                    ranking[player_id]['points'] += amount
                    ranking[player_id]['tries'] += 1
                except KeyError:
                    ranking[player_id] = {
                        "name": self.player.display_name,
                        "points": amount,
                        "tries": 1
                    }

                json.dump(ranking, file)

    # Commands
    @commands.group(
        name='quiz',
        brief='Startet eine Quiz Runde'
    )
    async def _quiz(self, ctx):
        if ctx.invoked_subcommand is None:
            if self.player is not None:
                await ctx.send(f"Aktuell läuft bereits ein Spiel mit {self.player.display_name}. "
                    + "Ein Super-User kann das laufende Spiel mit !quiz stop beenden.")
            else:
                self.player = ctx.author
                self.channel = ctx.channel
                self.game_stage = 0

                with open('quiz.json', 'r') as file:
                    self.quiz = json.load(file)

                await ctx.send("Hallo und herzlich Willkommen zu Wer Wird Mövionär! "
                    + f"Heute mit dabei: {self.player.display_name}. Los geht's, Krah Krah!")
                await self.get_random_question()
                output = await self.get_question_output()
                await ctx.send(content=output['content'], embed=output['embed'])

    @is_super_user()
    @_quiz.command(
        name='stop',
        aliases=['-s'],
        brief='Beendet das laufende Quiz.'
    )
    async def _stop(self, ctx):
        if self.player is not None:
            await ctx.send("Das laufende Quiz wurde abgebrochen. "
                + f"{self.player.display_name} geht leider leer aus, Krah Krah!")
            await self.stop_quiz()
        else:
            await ctx.send("Bist du sicher? Aktuell läuft gar kein Quiz, Krah Krah!")

    @_quiz.command(
        name='report',
        aliases=['-r'],
        brief='Meldet eine Frage als unpassend/falsch/wasauchimmer.',
        usage='report <Grund>'
    )
    async def _report(self, ctx, *args):
        with open('logs/quiz_report.log', 'a+') as file:
            file.write(f"[{gcts()}] {ctx.author.name}: Grund: {' '.join(args)} - "
            + f"Frage: {self.question['question']}\n")

        await ctx.send("Deine Meldung wurde abgeschickt.")

        if self.player is not None:
            await self.get_random_question()
            output = await self.get_question_output()
            await self.channel.send(content=output['content'], embed=output['embed'])

    @_quiz.command(
        name='rank',
        brief='Zeigt das Leaderboard an.'
    )
    async def _rank(self, ctx):
        with open('quiz_ranking.json', 'r') as file:
            ranking = json.load(file)
            sorted_ranking = dict(sorted(
                ranking.items(), key=lambda item: item[1]['points'], reverse=True
            ))

            maxlength = {"name": 0, "points": 0}
            for item in sorted_ranking.items():
                name = len(self.bot.get_user(int(item[0])).display_name)
                points = len(format(item[1]['points'],',d'))

                if maxlength['name'] < name:
                    maxlength['name'] = name

                if maxlength['points'] < points:
                    maxlength['points'] = points

            embed = discord.Embed(
                title="Punktetabelle Quiz",
                colour=discord.Colour(0xff00ff),
                description="```" + "\n".join([
                    *map(lambda a: (
                        f"{self.bot.get_user(int(a[0])).display_name}"
                            .ljust(maxlength['name'] + 4, ' ')
                        + f"{format(a[1]['points'],',d').replace(',','.')}🕊 "
                            .rjust(maxlength['points'] + 4, ' ')
                        + f"{a[1]['tries']} Versuch"
                            .rjust(14, ' ')
                        + f"{'' if a[1]['tries'] == 1 else 'e'}"
                    ), sorted_ranking.items())
                ]) + "```"
            )

            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.player == message.author and message.channel == self.channel:
            user_answer = message.content.title()

            if user_answer in ['A', 'B', 'C', 'D']:
                if self.question['answers'][user_answer]['correct']:
                    await self.channel.send("✅ Richtig!\n")

                    if self.game_stage == 15:
                        await self.channel.send(f"Du hast {self.stages[15]}🕊 gewonnen!!!")

                        await self.update_ranking(self.stages[15])
                        await self.stop_quiz()
                    else:
                        if self.game_stage == 4:
                            await self.channel.send(f"❗️ Checkpoint erreicht: {self.stages[4]}🕊.")
                        elif self.game_stage == 9:
                            await self.channel.send(f"❗️ Checkpoint erreicht: {self.stages[9]}🕊.")

                        self.game_stage += 1

                        await self.get_random_question()
                        output = await self.get_question_output()
                        await self.channel.send(content=output['content'], embed=output['embed'])
                else:
                    await self.channel.send("❌ Falsch!")

                    for answer in self.question['answers'].items():
                        if answer[1]['correct']:
                            await self.channel.send(f"Die richtige Antwort ist {answer[0]}: "
                                + f"{answer[1]['text']}")
                    if self.game_stage <= 4:
                        await self.channel.send("Du verlässt das Spiel ohne Gewinn.")
                        await self.update_ranking(0)
                    elif self.game_stage > 9:
                        await self.channel.send(f"Du verlässt das Spiel mit {self.stages[9]}🕊.")
                        await self.update_ranking(self.stages[9])
                    elif self.game_stage > 4:
                        await self.channel.send(f"Du verlässt das Spiel mit {self.stages[4]}🕊.")
                        await self.update_ranking(self.stages[4])
                    await self.stop_quiz()
            elif user_answer == "Q":
                if self.game_stage == 0:
                    await self.channel.send("Du verlässt das Spiel ohne Gewinn.")
                    await self.update_ranking(0)
                else:
                    await self.channel.send("Du verlässt das Spiel freiwillig mit "
                        + f"{self.stages[self.game_stage - 1]}🕊.")
                    await self.update_ranking(self.stages[self.game_stage - 1])
                for answer in self.question['answers'].items():
                    if answer[1]['correct']:
                        await self.channel.send(f"Die richtige Antwort ist {answer[0]}: "
                        + f"{answer[1]['text']}")
                await self.stop_quiz()
