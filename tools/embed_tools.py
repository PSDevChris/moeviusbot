import discord

from tools.event_tools import Event

DEFAULT_COLOR = 0xff00ff


class EmbedBuilder():
    @staticmethod
    def single_stream_announcement(event: Event) -> discord.Embed:
        return discord.Embed(
            title="**Stream-Ankündigung**",
            url="https://www.twitch.tv/schnenko",
            description=f"{event.description}\nGebt mir ein Join, Krah Krah!",
            colour=DEFAULT_COLOR
        ).add_field(
            name="Wann?",
            value=event.fmt_dt
        ).add_field(
            name="Was?",
            value=event.title
        ).set_thumbnail(
            url="https://static-cdn.jtvnw.net/jtv_user_pictures/2ed0d78d-f66a-409d-829a-b98c512d8534-profile_image-70x70.png"
        ).set_footer(
            text=f"Event ID: {event.id}"
        )

    @staticmethod
    def events_to_be_announced(events: list[Event]) -> discord.Embed:
        if events is None or not events:
            raise ValueError

        embed = discord.Embed(
            title="**Unangekündigte Events**",
            description="""Die folgenden Events sind aktuell angekündigt.
                        Verwende den Button mit der richtigen ID oder /join <id> um 
                        deinen Namen auf die Gästelistze zu setzen.""",
            color=DEFAULT_COLOR
        )

        for event in events:
            embed.add_field(**event.to_field())

        return embed

    @staticmethod
    def upcoming_events(events: list[Event]) -> discord.Embed:
        if events is None or not events:
            raise ValueError

        embed = discord.Embed(
            title="**Angekündigte Events**",
            description="Diese Events sind aktuell angekündigt.",
            color=DEFAULT_COLOR
        ).set_thumbnail(
            url="https://static-cdn.jtvnw.net/jtv_user_pictures/2ed0d78d-f66a-409d-829a-b98c512d8534-profile_image-70x70.png"
        )

        for event in events:
            embed.add_field(**event.to_field())

        return embed

    @staticmethod
    def stream_running(event: Event) -> discord.Embed:
        return discord.Embed(
            title="**Schnenko nervt!**",
            url="https://www.twitch.tv/schnenko",
            description=f"**{event.title}**",
            colour=DEFAULT_COLOR
        ).add_field(
            name="Beschreibung:",
            value=event.description
        ).set_thumbnail(
            url="https://static-cdn.jtvnw.net/jtv_user_pictures/2ed0d78d-f66a-409d-829a-b98c512d8534-profile_image-70x70.png"
        )
