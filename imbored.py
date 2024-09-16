import requests
import json
import random

def dad_jokes():
    url = "https://icanhazdadjoke.com/"

    headers = {"Accept": "application/json"}

    source = requests.request("GET", url, headers=headers)
    response0 = source.json()
    response = response0["joke"]
    print(response)
    if '?' in response:
        response = response.split('?')
        response[0] = response[0] + "?"
    return response

def simple_2jokes():
    url = "https://official-joke-api.appspot.com/jokes/random"

    source = requests.get(url)
    response0 = source.json()

    response_s = response0["setup"]
    response_p = response0["punchline"]
    reply =[]
    reply.append(response_s)
    reply.append(response_p)
    
    return reply



def joke_response():
    rand = random.randint(1,2)
    if(rand == 1):
        joke = dad_jokes()
        
    elif(rand ==2):
        joke= simple_2jokes() 
    
    return joke
