import discord


def help_embed():
    embed = discord.Embed(title="Help")
    embed.add_field(name="hi luke", value="Say hello to luke", inline=False)
    embed.add_field(
        name="/faction_intro -faction name-",
        value="Get data about devlin factions. Use exact name from choices.",
        inline=False,
    )
    embed.add_field(
        name="/enlightenme",
        value="Luke sends you words of enlightenment.",
        inline=False,
    )
    embed.add_field(
        name="/imbored",
        value="Luke tries to cheer you up with a joke.",
        inline=False,
    )
    embed.add_field(
        name="/repeat -sentence-",
        value="Make luke say what you always wanted him to.",
        inline=False,
    )

    embed.set_footer(text="made by -Kryptonian[2361119]")
    return embed
