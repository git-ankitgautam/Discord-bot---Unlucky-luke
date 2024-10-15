import discord
from discord.ext import commands
from discord import app_commands
from config import TOKEN
import asyncio
from faction_intros_embed import response_embed
from enlightenme import get_quote
from typing import Literal
from imbored import joke_response
from profanity_checker import profanity_check
from helpme import help_embed


class Bot_client(commands.Bot):
    async def on_ready(self):
        print("Unlucky_luke ready")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")

        except Exception as e:
            print(f"Unlucky_luke ran into an error: {e}")

    async def on_message(self, message):
        msg = message.content.lower()
        if message.author == self.user:
            return
        if msg.startswith("hi luke"):
            await message.channel.send(f"Hello {message.author.display_name}, this is a 100 percent luke, there is no doubt to it, trust me :D")
        if profanity_check(msg):
            with open("captain-america.gif", "rb") as language_gif:
                await message.reply(file=discord.File(language_gif))


intents_list = discord.Intents.default()
intents_list.message_content = True
client = Bot_client(command_prefix="!", intents = intents_list)

quote = {}

@client.tree.command(name="hello", description="say hello to Luke")
async def say_hello(interaction: discord.Interaction):
    await interaction.response.send_message("hello!, this is a 100 percent luke, there is no doubt to it, trust me :D \n beware of anyone else claiming to be me, I've seen some around :eyes:")


@client.tree.command(name="repeat", description="Have him say what you always wanted luke to say! its the same thing! especially for legal purposes!")
async def repeat_whatever_message_says(interaction: discord.Interaction, repeat:str):
    await interaction.response.send_message(repeat)


@client.tree.command(name="faction_intro", description="get a snapshot of devlin factions from luke")
async def fruit(interaction: discord.Interaction, faction_name: Literal["Brave survivors", "Flying cadets", "Jack of Trades", "Merciful Vanguards", "Rusty's ravagers", "School of Devlins"]):
    fembed = response_embed(faction_name)
    await interaction.response.send_message(embed = fembed)


@client.tree.command(name="enlightenme", description="luke sends you his words of enlightment, so you can transcend life")
async def enlightenme(interaction: discord.Interaction):
    quote = get_quote()
    await interaction.response.send_message(embed=quote)
    

@client.tree.command(name="imbored", description="luke will try to cheer you up")
async def imbored(interaction: discord.Interaction):
    joke = joke_response()
    await interaction.response.send_message(f"{joke[0]}")
    await asyncio.sleep(4)
    if joke[1]:
        await interaction.followup.send(joke[1] + " :rofl:")

@client.tree.command(name="help", description="a summary of all commands")
async def help(interaction: discord.Interaction):
    embed = help_embed()
    await interaction.response.send_message(embed = embed)

client.run(TOKEN)
