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
    embed.add_field(
        name="/set_entry_channel #channel",
        value="Set the channel where join messages are posted.",
        inline=False,
    )
    embed.add_field(
        name="/welcome_dm true|false",
        value="Enable or disable welcome DMs for new members.",
        inline=False,
    )
    embed.add_field(
        name="/set_welcome_templates",
        value="Update join/DM templates. Placeholders: {user_mention}, {user_name}, {server}",
        inline=False,
    )
    embed.add_field(
        name="/mod_settings",
        value="Set warning threshold, timeout duration, and warning expiry.",
        inline=False,
    )
    embed.add_field(
        name="/set_exemption",
        value="Set who is exempt from profanity warnings.",
        inline=False,
    )
    embed.add_field(
        name="/warnings @user",
        value="Show active warnings for a member.",
        inline=False,
    )
    embed.add_field(
        name="/clear_warnings @user",
        value="Clear all warnings for a member.",
        inline=False,
    )

    embed.set_footer(text="made by -Kryptonian[2361119]")
    return embed
