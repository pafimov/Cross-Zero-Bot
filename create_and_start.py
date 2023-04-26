from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()
with open('token.txt', 'r') as f:
    token = f.readline()
    global bot
    bot = Bot(token)
dp = Dispatcher(bot, storage=storage)

#queue
waiting = [-1 for i in range(10)]

#free game id
free_id = 0

#all running games
games = dict()

