import asyncio
import aiohttp
import json
import urllib3
import time

try:
    with open("credentials.json", "r") as cr:
        CREDENTIALS = json.load(cr)
except:
    print("Can't open credentials.json")
    exit()

link = "https://api.telegram.org/bot" + CREDENTIALS["telegram"]["token"]

async def getMe1():
    async with aiohttp.ClientSession() as session:
        url = link + "/getMe"

        async with session.get(url) as resp:
            me = await resp.json()

            print("*** FROM 1 ***")
            print(me)

async def getMe2():
    loop = asyncio.get_event_loop()
    http = urllib3.PoolManager()
    future = loop.run_in_executor(
        None, 
        http.request,
        "GET",
        link + "/getMe"
    )

    responce = await future

    print("*** FROM 2 ***")
    print(json.loads(responce.data.decode('utf-8')))

async def getUpdates():
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(
        None, 
        QueryCallback,
        "GET",
        link + "/getUpdates",
        {
            "timeout": 60
        },
        60
    )

    responce = await future

    print("*** FROM UPD ***")
    print(json.loads(responce.data.decode('utf-8')))

def QueryCallback(method, URL, fields, timeout):
    http = urllib3.PoolManager()
    return http.request(
        method, URL, 
        fields=fields, 
        timeout=timeout
    )

async def p1(): print(1)
async def p2(): print(2)

ioloop = asyncio.get_event_loop()
tasks = [
    ioloop.create_task(p1()),
    ioloop.create_task(getMe1()),
    ioloop.create_task(getMe2()),
    ioloop.create_task(getUpdates()),
    ioloop.create_task(p2()),
]

ioloop.run_until_complete(asyncio.wait(tasks))
ioloop.close()