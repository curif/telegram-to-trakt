
from telethon import TelegramClient
import json
import os

config = {}

# Configure
if not os.path.exists("config/config.json"):
   raise Exception("Error config.json not found")
with open("config/config.json", 'r') as file:
   config  = json.load(file)

# Create the client and connect
print("connect to telegram API")
client = TelegramClient(
        "./config/{}.session".format(config["telegram"]["username"]), 
        config["telegram"]["api_id"], 
        config["telegram"]["api_hash"]
        )
client.start(phone=config["telegram"]["phone"])

print("session created")


