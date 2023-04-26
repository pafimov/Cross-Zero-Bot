from aiogram import executor
from create_and_start import dp
from database_work import start_db


import client

client.register_handlers(dp)


start_db()

executor.start_polling(dp, skip_updates=True)
