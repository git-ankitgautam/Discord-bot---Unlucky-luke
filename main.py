import discord
from config import TOKEN

class Bot_client(discord.Client):
  async def on_ready(self):
    print("Unlucky_luke ready")
    
    
    
intents_list = discord.Intents.default()
intents_list.message_content = True
    
client = Bot_client(intests = intents_list)
client.run(TOKEN)