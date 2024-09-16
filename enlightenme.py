import requests
import json

def get_quote():
  zenquote = requests.get("https://zenquotes.io/api/random")
  zenquote_json = json.loads(zenquote.text)
  data = {}
  data["quote"] = zenquote_json[0]['q']
  data["author"] = zenquote_json[0]['a']
  
  return data