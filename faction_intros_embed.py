
import discord
from discord import colour
from faction_api_struct import api_stuff



def response_embed(name0):
    arr = {}
    arr = api_stuff(name0, arr)
    colours = {
    "DEFAULT" :	"0",
    "AQUA"	: "1752220",
    "DARK_AQUA" :"1146986",
    "GREEN" :	"3066993",
    "DARK_GREEN" :	"2067276",
    "BLUE": "3447003",
    "DARK_BLUE" :	"2123412",
    "PURPLE" :	"10181046",
    "DARK_PURPLE" :	"7419530",
    "LUMINOUS_VIVID_PINK" :	"15277667",
    "DARK_VIVID_PINK" :	"11342935",
    "GOLD" :	"15844367",
    "DARK_GOLD" :	"12745742",
    "ORANGE" :	"15105570",
    "DARK_ORANGE" : 	"11027200",
    "RED" :	"15158332",
    "DARK_RED" : 	"10038562",
    "GREY" : 	"9807270",
    "DARK_GREY" : 	"9936031",
    "DARKER_GREY" : 	"8359053",
    "LIGHT_GREY" :	"12370112",
    "NAVY" :	"3426654",
    "DARK_NAVY" :	"2899536",
    "YELLOW" : 	"16776960"}
    
    cc = {
        "Brave survivors" : "16776960",
        "Flying cadets" : "3447003",
        "Jack of Trades": "15105570",
        "Merciful Vanguards" : "15158332",
        "Masters of Fate" : "15105570",
        "Rusty's ravagers" : "10181046",
        "School of Devlins": "15844367"
    }

    embedvar = discord.Embed(title= name0, url="https://www.torn.com/factions.php?step=profile&ID={}".format(arr["fac_ids"]), description= "Basic faction data for {}".format(name0), color = int(cc[name0]))
    
    embedvar.add_field(name= "Name", value=arr["Name"]+" "+"[{}]".format(arr["fac_ids"]), inline=False)
    embedvar.add_field(name="Leader", value=arr["leader"]+" " + "[{}]".format(arr["leader_ID"]), inline=True)
    embedvar.add_field(name="Co-Leader", value=arr["coleader"]+" "+ "[{}]".format(arr["coleader_ID"]), inline=True)
    embedvar.add_field(name= "Members", value=arr["member_count"]+"/"+arr["capacity"], inline=True)
    embedvar.add_field(name="Respect", value="{:,}".format(arr["respect"]), inline=False)
    
    
    return embedvar