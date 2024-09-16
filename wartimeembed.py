import json
from os import name
import requests
import discord
from datetime import datetime
from config import API_KEY

with open("Factionsdata.txt") as file:
    facdata = file.read()

fdata = json.loads(facdata)

def wardataembed(factionid):
    factionid = str(47293)

    Asource = requests.get("https://api.torn.com/faction/"+factionid+"?selections=&key=" + API_KEY)
    adata = Asource.json()
    raid  = adata["raid-wars"][0]
    if(raid != {}):
        fname = adata["name"]
        arespect = adata["respect"]
        raid_data = adata["raid_wars"][0]
        Ascore = int(raid_data["raider_score"])
        Oscore = int(raid_data["defender_score"])
        raid_start_time = int(raid_data["start_time"])
        date_time = datetime.fromtimestamp(raid_start_time)
        start_time = date_time.strftime("%m-%d-%Y, %H:%M:%S")
        start_time = str(start_time)

        Oppfactionid = str(raid_data["defending_faction"])
        Osource = requests.get("https://api.torn.com/faction/"+Oppfactionid+"?selections=&key=" + API_KEY)
        odata  = Osource.json()
        ofname = odata["name"]
        orespect = odata["respect"]

        if(Ascore > Oscore):
            warstatus = "winning"
            difference = Ascore - Oscore
            ongoingresult = "ahead"
        elif(Ascore == Oscore):
            warstatus = "at equal scores"
            difference =0
            ongoingresult = "ahead"
        else:
            warstatus = "losing"
            difference = Oscore-Ascore
            ongoingresult = "behind"
        

        embed_Var = discord.Embed(title = "War!", url ="https://www.torn.com/factions.php?step=profile&ID={}".format(factionid), color = 15158332)
        embed_Var.add_field(name="{}".format(fname),value = arespect)
        embed_Var.add_field(name = "V/S", value= "is at war with")
        embed_Var.add_field(name = ofname, value = orespect)
        embed_Var.add_field(name = "Our score", value = Ascore)
        embed_Var.add_field(name = "Their Score", value = Oscore)
        embed_Var.add_field(name = "we are " + warstatus, value="currently {} points".format(difference) + ongoingresult , inline = False)

        embed_Var.set_footer(text = "Started at " + start_time)

    return embed_Var
