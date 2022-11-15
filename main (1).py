import asyncio
from multiprocessing.dummy import Pool
from os.path import exists
from sys import platform, stderr, version_info

import discord
from discord.ext import tasks
from dotenv import dotenv_values
from loguru import logger
from random import randint
from time import sleep

env_values = dotenv_values()
CHAT_ID = int(env_values['CHAT_ID'])
TO_SLEEP_BETWEEN_COMMAND = int(env_values['TO_SLEEP_BETWEEN_COMMAND'])
MIN_SLEEP_RANGE_BEFORE_FIRST_MESSAGE = int(env_values['MIN_SLEEP_RANGE_BEFORE_FIRST_MESSAGE'])
MAX_SLEEP_RANGE_BEFORE_FIRST_MESSAGE = int(env_values['MAX_SLEEP_RANGE_BEFORE_FIRST_MESSAGE'])

if platform == "win32" and (3, 8, 0) <= version_info < (3, 9, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


logger.remove()
logger.add(stderr,
           format="<white>{time:HH:mm:ss}</white> | <level>"
                  "{level: <8}</level> | <cyan>"
                  "{line}</cyan> - <white>{message}</white>")


class MyClient(discord.Client):
    async def on_ready(self):
        to_send_command_data = None
        logger.info(f'{self.user} | Успешно авторизован')

        channel = MyClient.get_channel(self, CHAT_ID)

        async for command in channel.slash_commands():
            if command.name == need_command:
                to_send_command_data = command
                break

        else:
            logger.error(f'{self.user} | Не удалось обнаружить команду в списке доступных')
            exit()

        self.send_commands_task.start(to_send_command_data=to_send_command_data)

    @tasks.loop(seconds=TO_SLEEP_BETWEEN_COMMAND)
    async def send_commands_task(self,
                                 to_send_command_data: discord.commands.SlashCommand):
        await to_send_command_data()
        logger.success(f'{self.user} | Команда успешно отправлена, сплю {TO_SLEEP_BETWEEN_COMMAND} секунд')


def wrapper(current_data: str) -> None:
    current_token_wrapper = current_data[0]
    current_proxy_wrapper = current_data[1]

    time_to_sleep = randint(MIN_SLEEP_RANGE_BEFORE_FIRST_MESSAGE,
                            MAX_SLEEP_RANGE_BEFORE_FIRST_MESSAGE)
    logger.info(f'{current_token_wrapper} | Сплю {time_to_sleep} сек. перед первым запуском')
    sleep(time_to_sleep)

    client = MyClient(proxy=current_proxy_wrapper)
    client.run(token=current_token_wrapper)


if __name__ == '__main__':
    with open('tokens.txt', 'r', encoding='utf-8-sig') as file:
        tokens = [row.strip() for row in file]

    if exists('proxies.txt'):
        with open('proxies.txt', 'r', encoding='utf-8-sig') as file:
            proxies = [row.strip() for row in file]

    else:
        proxies = []

    logger.info(f'Успешно загружено {len(tokens)} токенов, {len(proxies)} proxies')

    need_command = input('\nВведите команду для отправки: ').replace('/', '')

    if proxies:
        while len(tokens) > len(proxies):
            for current_proxy in proxies:
                proxies.append(current_proxy)

                if len(proxies) >= len(tokens):
                    break

        proxies = proxies[:len(tokens)]
        source_data = list(zip(tokens, proxies))

    else:
        source_data = list(zip([current_data for current_data in tokens],
                               [None for _ in range(len(tokens))]))

    with Pool(processes=len(source_data)) as executor:
        executor.map(wrapper, source_data)
