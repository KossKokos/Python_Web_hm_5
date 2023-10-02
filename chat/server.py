import asyncio
import logging
from datetime import datetime, timedelta
from time import time

import aiohttp
import aiofile
import websockets
import names
from aiofile import async_open
from aiopath import AsyncPath 
from websockets import WebSocketServerProtocol, WebSocketProtocolError 
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)

async def request(url):

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    r = await response.json()
                    return r
                logging.error(f'Error status: {response.status} for url: {url}')
        except aiohttp.ClientConnectionError as err:
            logging.error(f'ConnectioError for url: {url}: {err}')
        return None

async def get_users_date(days: str):
    await asyncio.sleep(0.1)
    date_today = datetime.today()
    if not 0 <= int(days) < 11:
        return 'Not more than 10 days and not less than 0'
    divided_days = timedelta(days=int(days))
    users_date = date_today - divided_days
    users_date = users_date.strftime("%d.%m.%Y")
    return users_date

async def get_todays_date():
    await asyncio.sleep(0.1)
    todays_date = datetime.today().strftime("%d.%m.%Y")
    return todays_date

async def get_few_days_exchange(command: list):
    result = []
    days = int(command[1])
    i = 0
    while i <= days:
        users_date = await get_users_date(i)
        data = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={users_date}')
        result.append(data)
        i += 1
    return result

async def get_todays_exchange(command):
    todays_date = await get_todays_date()
    data = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={todays_date}')
    return data

PARSE_EXCHANGE = {1: get_todays_exchange, 2: get_few_days_exchange}

async def logging_exchange():
    path = AsyncPath('exchange_logging')
    async with async_open(path, 'a') as afp:
        await afp.write(f"The command was called at - {datetime.now()}\n")

async def get_exchange(user_input: list):
    # await logging_exchange()
    parse_input = len(user_input)
    result = await PARSE_EXCHANGE[parse_input](user_input)
    return str(result)

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def send_to_client(self, message: str, ws: WebSocketServerProtocol):
        await ws.send(message)

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.lower().strip().startswith('exchange'):
                # await logging_exchange()
                res = await get_exchange(message.strip().split())
                await self.send_to_client(res, ws)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())