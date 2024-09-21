from os import name
import discord
from discord.embeds import Embed


import discord

def help_embed():
    embed = discord.Embed(title = "Help")
    embed.add_field(name = "hi luke", value="Say hello to luke")
    embed.add_field(name= "/faction_intro -faction name-", value="Get the data about devlins factions, just replace -faction name-, just make sure the spelling is write, you can use initials too")
    embed.add_field(name= "/enlightenme", value="luke sends you his words of enlightment, so you can transcend life")
    embed.add_field(name= "/imbored", value="luke will try to cheer you up")
    embed.add_field(name="/repeat -sentence-", value="make luke say what you always wanted him to")

    embed.set_footer(text = "made by -Kryptonian[2361119]")

    return embed
