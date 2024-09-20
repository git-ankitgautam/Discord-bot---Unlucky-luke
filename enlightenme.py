import requests
import json
import discord

def get_quote():
	zenquote = requests.get("https://zenquotes.io/api/random")
	zenquote_json = json.loads(zenquote.text)
	data = {}
	data["quote"] = zenquote_json[0]['q']
	data["author"] = zenquote_json[0]['a']

	embedvar = discord.Embed()

	embedvar.add_field(name="",value=data["quote"], inline=False)
	embedvar.add_field(name="",value=f"-{data["author"]}", inline=False)

	return embedvar