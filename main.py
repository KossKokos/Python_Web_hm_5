import asyncio
import logging
import platform
import sys
from datetime import datetime, timedelta
from time import time

import aiohttp

# 'https://api.privatbank.ua/p24api/exchange_rates?json&date=28.09.2023'

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

async def get_one_currency_ex(users_args):
    result = []
    days = int(users_args[1])
    curr = users_args[2].strip().upper()
    i = 0
    while i < days:
        users_date = await get_users_date(i)
        data = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={users_date}')
        exchange_rate = data['exchangeRate']
        for dct in exchange_rate:
            if dct['currency'] == curr:
                result.append({users_date: {dct['currency']: {'sale': dct['saleRate'], 'purchase': dct['purchaseRate']}}})
        i += 1
    return result

async def get_few_days_exchange(users_args):
    result = []
    eur_usd_curr = []
    days = int(users_args[1])
    if not 0 < days < 11:
        return 'Not more than 10 days and not less than 0!'
    i = 0
    while i < days:
        users_date = await get_users_date(i)
        data = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={users_date}')
        exchange_rate = data['exchangeRate']
        for dct in exchange_rate:
            if dct['currency'] == 'EUR' or dct['currency'] == 'USD':
                eur_usd_curr.append(dct)
        result.append({users_date: {eur_usd_curr[0]['currency']: {'sale': eur_usd_curr[0]['saleRate'], 'purchase': eur_usd_curr[0]['purchaseRate']}},
                   eur_usd_curr[1]['currency']: {'sale': eur_usd_curr[1]['saleRate'], 'purchase': eur_usd_curr[1]['purchaseRate']}})
        i += 1
    return result

async def get_exchange_eur_usd(user_input):
    lst_eur_usd = []
    todays_date = await get_todays_date()
    data = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={todays_date}')
    lst_currency = data['exchangeRate']
    for dct in lst_currency:
        if dct['currency'] == 'EUR' or dct['currency'] == 'USD':
            lst_eur_usd.append(dct)
    return {todays_date: {lst_eur_usd[0]['currency']: {'sale': lst_eur_usd[0]['saleRate'], 'purchase': lst_eur_usd[0]['purchaseRate']}},
                   lst_eur_usd[1]['currency']: {'sale': lst_eur_usd[1]['saleRate'], 'purchase': lst_eur_usd[1]['purchaseRate']}}

PARSE_EXCHANGE = {1: get_exchange_eur_usd, 2: get_few_days_exchange, 3: get_one_currency_ex}

async def get_exchange():
    user_input = sys.argv
    len_input = len(user_input)
    result = await PARSE_EXCHANGE[len_input](user_input)
    return result

if __name__ == "__main__":
    try:
        start = time()
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        r = asyncio.run(get_exchange())
        print(r)
        print(time() - start,'s')
    except KeyError:
        print('Too many parameters, expected 1 or 2 or 3.')
    except ValueError:
        print('Please write a command in the format "py main.py (amount of days) (currency)"')