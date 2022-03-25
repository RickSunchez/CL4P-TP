from time import sleep
import json
from bot_api import TG_bot

# start: 09.30 - 12.00 (tg_api is working)
# start: 15.00 - 18.00 (fb_api is working)
# start: 19.00 - 20.00 (docker is working) MVP
# start: 19.00 - 21.00 (refactor)

try:
    with open("./src/credentials.json", "r") as cr:
        CREDENTIALS = json.load(cr)
except:
    print("Can't open credentials.json")
    exit()

bot = TG_bot(CREDENTIALS["telegram"]["token"])

while True:
    bot.getUpdates()
    sleep(1)