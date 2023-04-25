from aiogram import Bot, executor, Dispatcher, types
import time
import asyncio
import sqlite3 as sq

bot = Bot('6235349333:AAH37djTzR62bJYXgDnbPKdA8K0wo-lktBU')
dp = Dispatcher(bot)

def start_db():
    global base, cur
    base = sq.connect('Database.db')
    cur = base.cursor()
    if base:
        print("DB OKAY")
    base.execute('CREATE TABLE IF NOT EXISTS users(id BIGINT PRIMARY KEY, game BIGINT)')
    base.commit()
    
def add_to_db(id):
    cur.execute('INSERT INTO users VALUES(?, ?)', (id, -1))
    base.commit()

def add_user(id):
    print(id)
    c = cur.execute('SELECT * FROM users WHERE id=?', (str(id),))
    rws = c.fetchall()
    if len(rws) == 0:
        add_to_db(id)
    
    cur.execute('UPDATE users SET game=? WHERE id = ?', (str(-1), str(id)))
    base.commit()


@dp.message_handler(commands=['start', 'lol'])
async def go_hello(message : types.Message):
    add_user(message.from_id)


@dp.message_handler()
async def go(message : types.Message):
    await asyncio.sleep(10)
    await message.reply("WOWOWOWOWO")
    





start_db()

add_user(1)
executor.start_polling(dp, skip_updates=True)
