from os import name
import discord
from discord.embeds import Embed


import discord

def response_hembed():
    embed = discord.Embed(title = "Help", description = "luke only listens in lowercase, just so you know :P")
    embed.add_field(name = "Prefix", value="hey luke", inline = False)
    embed.add_field(name = "Hi luke", value="Say hello to luke")
    embed.add_field(name= "hey luke -faction name-", value="Get the data about devlins factions, just replace -faction name-, just make sure the spelling is write, you can use initials too")
    embed.add_field(name= "hey luke wars", value = "Luke give an update of wars going on (if any) in our factions")
    embed.add_field(name= "hey luke enlightenme", value="luke sends you his words of enlightment, so you can transcend life")
    embed.add_field(name= "hey luke author", value="First of all, luke doesn't plagiarize from anywhere, but still if you wanna know the 'real' author, help yourself")
    embed.add_field(name= "hey luke imbored", value="luke will try to cheer you up")
    embed.add_field(name="hey luke say -sentence-", value="make luke say what you always wanted him to")

    embed.set_footer(text = "made by -Kryptonian[2361119]")

    return embed
