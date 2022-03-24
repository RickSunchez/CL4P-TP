from time import sleep
import json
from bot_api import TG_bot

# start: 09.30 - 12.00 (bot is working)
# start: 15.00 - 18.00 (fb_api is working)
# start: 19.00 - __.00 (fb_api is working)

try:
    with open("credentials.json", "r") as cr:
        CREDENTIALS = json.load(cr)
except:
    print("Can't open credentials.json")
    exit()

bot = TG_bot(CREDENTIALS["telegram"]["token"])

while True:
    bot.getUpdates()
    sleep(1)