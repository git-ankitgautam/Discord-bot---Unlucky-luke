import discord
from discord.ext import commands
from discord import app_commands
from config import TOKEN,TESTING_SERVER_ID
import enum
from faction_intros_embed import response_embed
from enlightenme import get_quote
from typing import Literal
import time
from imbored import joke_response

class Bot_client(commands.Bot):
    async def on_ready(self):
        print("Unlucky_luke ready")
        try:
            testing_Server_object = discord.Object(id=int(TESTING_SERVER_ID))
            synced = await self.tree.sync(guild=testing_Server_object)
            print(f"Synced {len(synced)} commands to {testing_Server_object.id}")

        except Exception as e:
            print(f"Unlucky_luke ran into an error: {e}")

    async def on_message(self, message):
        msg = message.content.lower()
        print(f"message from: {message.author} : {msg}")
        if message.author == self.user:
            return
        if message.content.startswith("hey luke"):
            await message.channel.send(f"Hello {message.author.display_name}, this is a 100 percent luke, there is no doubt to it, trust me :D")
        if "shit" in message.content:
            await message.channel.send("LANGUAGE!")

intents_list = discord.Intents.default()
intents_list.message_content = True
testing_Server_object = discord.Object(id=int(TESTING_SERVER_ID))
client = Bot_client(command_prefix="!", intents = intents_list)

quote = {}

@client.tree.command(name="hello", description="say hello to Luke", guild=testing_Server_object)
async def say_hello(interaction: discord.Interaction):
    await interaction.response.send_message("hello!, this is a 100 percent luke, there is no doubt to it, trust me :D \n beware of anyone else claiming to be me, I've seen some around :eyes:")


@client.tree.command(name="repeat", description="Have him say what you always wanted luke to say! its the same thing! especially for legal purposes!", guild=testing_Server_object)
async def repeat_whatever_message_says(interaction: discord.Interaction, repeat:str):
    await interaction.response.send_message(repeat)


@client.tree.command(name="faction_intro", description="get a snapshot of devlin factions from luke", guild=testing_Server_object)
async def fruit(interaction: discord.Interaction, faction_name: Literal["Brave survivors", "Flying cadets", "Jack of Trades", "Merciful Vanguards", "Rusty's ravagers", "School of Devlins"]):
    fembed = response_embed(faction_name)
    await interaction.response.send_message(embed = fembed)


@client.tree.command(name="enlightenme", description="luke sends you his words of enlightment, so you can transcend life", guild=testing_Server_object)
async def enlightenme(interaction: discord.Interaction):
    quote = get_quote()
    await interaction.response.send_message(quote["quote"])

@client.tree.command(name="author", description="if you wanna know the 'real' author, help yourself", guild=testing_Server_object)
async def author(interaction: discord.Interaction):
    await interaction.response.send_message("hmm, okay I guess, it was a case of parallel thinking, here is the 'orginial' one as per the internet")
    await interaction.followup.send(quote["author"])
    

@client.tree.command(name="imbored", description="luke will try to cheer you up", guild=testing_Server_object)
async def imbored(interaction: discord.Interaction):
    joke = joke_response()
    await interaction.response.send_message(f"{joke[0]}")
    time.sleep(4)
    await interaction.followup.send(joke[1] + " :rofl:")



client.run(TOKEN)
