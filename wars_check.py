from wartimeembed import wardataembed
from config import API_KEY
import requests
import json
import datetime
import discord

with open("Factionsdata.txt") as file:
    facdata = file.read()

fdata = json.loads(facdata)

def war_check():
    factionsnamelist = list(fdata.keys())
    factionids = list()
    for y in range(7):
        factionids.append(fdata[factionsnamelist[y]]['ID'])

    for x in range(7):
        factionid = factionids[x]
        source = requests.get("https://api.torn.com/faction/"+factionid+"?selections=&key=" + API_KEY)
        data  = source.json()
        result = list()
        raid = data['raid_wars']
        tt_wars = data["territory_wars"]
        if(raid == {} and tt_wars == {}):
            result.append('peace')
        
        else:
            result.append('war')

        result[0] = "war"
        result[0]  = "war"
    if 'war' in result:
        ping = int(result.index('war'))
        fid = fdata[factionsnamelist[ping]]['ID']
        embed_Var = wardataembed(fid)
    
    else:
        embed_Var = discord.Embed(title ="Peaceful times")
        embed_Var.add_field(name = "everything is peaceful", value="None of the devlins factions is at war")
    
    return embed_Var
