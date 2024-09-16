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
  
    elif(command.startswith("say")):
      temp = command.split(' ')
      temp.pop(0)
      torepeat = " ".join(temp)
      await message.channel.send(torepeat)

    elif(command == "helpme"):
      hembed = response_hembed()
      await message.channel.send(embed = hembed)  
    
    elif(command == "enlightenme"):
      await message.channel.send(quote["quote"])

    elif(command == 'author'):
      await message.channel.send("what do you mean author? its me")
      await message.channel.send("hmm, okay I guess, it was a case of parallel thinking, here is the 'orginial' one as per the internet")
      await message.channel.send(quote["author"])

    elif(command == "imbored"):
      joke = joke_response()
      await message.channel.send(joke[0])
      time.sleep(2)
      await message.channel.send(joke[1] + " :rofl:")

    elif(command == "wars"):
      await message.channel.send("checking up on the devlins")
      wembed = war_check()
      await message.channel.send(embed = wembed)

    elif(command == 'bs' or command == "brave survivors" or command == "bravesurvivors" or command == "brave"):
      fembed = response_embed("Brave survivors")
      await message.channel.send(embed = fembed)
    
    elif(command == 'fc' or command == "flying cadets" or command == "flyingcadets"):
      fembed = response_embed("Flying cadets")
      await message.channel.send(embed = fembed)
    
    elif(command == 'jot' or command == 'jt'or command == "jack of trades" or command == "jackoftrades"):
      fembed = response_embed("Jack of Trades")
      await message.channel.send(embed = fembed)
    
    elif(command == 'mv' or command == "merciful vanguards" or command == "mercifulvanguards" or command == "vanguards"):
      fembed = response_embed("Merciful Vanguards")
      await message.channel.send(embed = fembed)
    
    elif(command == 'mof' or command == 'mf' or command == "masters of fate" or command == "mastersoffate"):
      fembed = response_embed("Masters of Fate")
      await message.channel.send(embed = fembed)
    
    elif(command == 'rr' or command == "rustys ravegers" or command == "rusty's ravegers" or command == "rustysravegers" or command == "rusty" or command=="rustys" or command == "rusty's"):
      fembed = response_embed("Rusty's ravagers")
      await message.channel.send(embed = fembed)
    
    elif(command == 'sod' or command == 'sd' or command == "school of devlins" or command == "school" or command == "schoolofdevlins"):
      fembed = response_embed("School of Devlins")
      await message.channel.send(embed = fembed)
    
  elif msg.startswith("hi luke"):
    await message.channel.send("Hello, this is a 100 percent luke, there is no doubt to it, trust me :D")
    await message.channel.send("beware of anyone else claiming to be me, I've seen some around")
  
  else:
    t=0

bot.run(TOKEN)
