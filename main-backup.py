import asyncio
import discord
import os
import time
from discord import channel
from discord import message
from discord.embeds import Embed
from discord.ext import tasks
from enlightenme import get_quote
from faction_intros_embed import response_embed
from helpme import response_hembed
from imbored import joke_response
from wars_check import war_check
from config import TOKEN


async def my_background_task(messageId):
    await bot.wait_until_ready()
    while not bot.is_closed():
      message = await bot.fetch_message(messageId)
      newEmbed = track()
      await message.edit(embed = newEmbed)
      await asyncio.sleep(30)


bot = discord.Client()

prefix ="hey luke"

quote = {} 
quote = get_quote()

@bot.event
async def on_ready():
    print("Unlucky_luke ready")

@bot.event
async def on_message(message):
  msg = message.content.lower()
  if msg.startswith("hey luke"):
    command0 = msg.split(' ')
    command0.pop(0)
    command0.pop(0)
    command = " ".join(command0)

    if(message.author == bot.user):
      return
  
    elif(command == "helpme"):
      hembed = response_hembed()
      await message.channel.send(embed = hembed)  

    elif(command == "wars"):
      await message.channel.send("checking up on the devlins")
      wembed = war_check()
      await message.channel.send(embed = wembed)
  
  else:
    t=0

bot.run(TOKEN)
