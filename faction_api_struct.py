import requests
import json
from config import API_KEY

with open("Factionsdata.txt") as file:
    facdata = file.read()

fdata = json.loads(facdata)
arr = list()


def api_stuff(fname,response0):
    factionid =  str(fdata[fname]["ID"])
    source = requests.get("https://api.torn.com/faction/"+ factionid +"?selections=basic&key="+ API_KEY)
    api_data = source.json()

    name = str(api_data["name"])
    leader = str(api_data["leader"])
    leader_name = str(api_data["members"][leader]['name'])
    coleader = str(api_data["co-leader"])
    if(coleader == '0'):
        coleader_name = "None"
    else:
        coleader_name = str(api_data["members"][coleader]['name'])
        

    respect = str(api_data["respect"])
    mem_capacity = str(api_data["capacity"])
    mem_count = list(api_data["members"].keys())
    mem_count = len(mem_count)

    response0["Name"] = name
    response0["leader"] = leader_name
    response0["leader_ID"] = leader
    response0["coleader_ID"] = coleader
    response0["coleader"] = coleader_name
    response0["respect"] = int(respect)
    response0["fac_ids"] = factionid
    response0["capacity"] = mem_capacity
    response0["member_count"] = str(mem_count)
    
    return response0

