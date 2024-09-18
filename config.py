from os import environ
from dotenv import load_dotenv
load_dotenv()
TOKEN = environ["TOKEN"]
API_KEY = environ["API_KEY"]
TESTING_SERVER_ID = environ["testing_server_id"]