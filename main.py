import discord
from config import TOKEN

class Bot_client(discord.Client):
    async def on_ready(self):
        print("Unlucky_luke ready")

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
    
client = Bot_client(intents = intents_list)
client.run(TOKEN)