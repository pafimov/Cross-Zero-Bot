from aiogram import Bot, executor, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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

def edit_user_game(id, val):
    cur.execute('UPDATE users SET game=? WHERE id=?', (str(val), str(id)))
    base.commit()

def get_user_game(id):
    c = cur.execute('SELECT * FROM users WHERE id=?', (str(id),))
    rws = c.fetchall()
    if len(rws) == 0:
        return -2
    else:
        return rws[0][1]
  

@dp.message_handler(commands=['start', 'lol'])
async def go_hello(message : types.Message):
    print("NEW USER!!")
    game_id = get_user_game(message.from_id)
    if game_id == -2:
        add_to_db(message.from_id)
        await message.reply('Привет! Это игра в Крестики-Нолики!\nЧтобы начать новую игру, напишите команду /play ')
    elif game_id == -1:
        await message.reply('Чтобы начать новую игру, напишите команду /play ')
    else:
        await message.reply('Вы сейчас находитесь в игре. Продолжите игру, либо, если хотите её завершить, напишите /stop ')



class game:
    symb = ['X', 'O']
    def __init__(self, _player1, _player2):
        self.players = [_player1, _player2]
        self.field = []
        self.current = 0
        for i in range(3):
            row = ['@', '@', '@']
            self.field.append(row)

    def check_won(self):
        #check for the draw
        cnt_free = 0
        for i in range(3):
            for j in range(3):
                if self.field[i][j] == '@':
                    cnt_free+=1
        if cnt_free == 0:
            return 1
        #check vertical
        for i in range(3):
            cur_el = self.field[0][i]
            if cur_el == '@':
                continue
            ok = 1
            for j in range(3):
                if self.field[j][i] != cur_el:
                    ok = 0
            if not ok:
                continue
            return 0
        #check horisontal
        for i in range(3):
            cur_el = self.field[i][0]
            if cur_el == '@':
                continue
            ok = 1
            for j in range(3):
                if self.field[i][j] != cur_el:
                    ok = 0
            if not ok:
                continue
            return 0
        #check main diagonal
        ok = 1
        cur_el = self.field[0][0]
        for i in range(3):
            if self.field[i][i] != cur_el:
                ok = 0
        if ok == 1 and cur_el != '@':
            return 0
        
        ok = 1
        cur_el = self.field[2][0]
        for i in range(3):
            if self.field[2-i][i] != cur_el:
                ok = 0
        if ok == 1 and cur_el != '@':
            return 0
        
        return -1

    def get_kb(self):
        kb = InlineKeyboardMarkup(row_width=3)
        for i in range(3):
            cur_row = []
            for j in range(3):
                cur_row.append(InlineKeyboardButton(text=self.field[i][j], callback_data=str(i) + ' '+ str(j)))
            kb.row(*cur_row)
        return kb

    def go(self, x, y):
        was = self.current
        if self.field[x][y] != '@':
            return -1
        
        self.field[x][y] = self.symb[was]
        self.current = 1-self.current
        res_check = self.check_won()
        if res_check != -1:
            return res_check
        return 2

        
waiting = -1
free_id = 0
games = dict()

async def send_field(game_id, final = 0):
    kb = games[game_id].get_kb()
    players = games[game_id].players
    if final == 0:
        await bot.send_message(players[games[game_id].current], 'Ваш ход- - - - - - - -', reply_markup=kb)
        await bot.send_message(players[1-games[game_id].current], 'Ход соперника---', reply_markup=kb)
    else:
        await bot.send_message(players[games[game_id].current], 'Финальная карта.', reply_markup=kb)
        await bot.send_message(players[1-games[game_id].current], 'Финальная карта.', reply_markup=kb)


async def start_game(player1, player2):
    global free_id
    edit_user_game(player1, free_id)
    edit_user_game(player2, free_id)
    new_game = game(player1, player2)
    games[free_id] = new_game
    game_id = free_id
    free_id+=1
    await bot.send_message(player1, 'Игра началась!\nЧтобы завершить игру до её окончания, напишите /stop ')
    await bot.send_message(player2, 'Игра началась!\nЧтобы завершить игру до её окончания, напишите /stop ')
    await send_field(game_id)


@dp.message_handler(commands=['play'])
async def search_for_opponent(message : types.Message):
    await message.reply('Ищу соперника!')
    global waiting
    if waiting != -1:
        await start_game(waiting, message.from_id)
        waiting = -1
    else:
        waiting = message.from_id

async def finish_game(game_id, someone=0):
    players = games[game_id].players
    edit_user_game(players[0], -1)
    edit_user_game(players[1], -1)
    del games[game_id]
    if someone == 1:
        await bot.send_message(players[0], 'Игра завершена одним из игроков.\nЧтобы начать новую игру, напишите команду /play ')
        await bot.send_message(players[1], 'Игра завершена одним из игроков.\nЧтобы начать новую игру, напишите команду /play ')

@dp.message_handler(commands=['stop'])
async def stop_game(message : types.Message):
    game_id = get_user_game(message.from_id)
    if game_id == -1 or game_id >= free_id:
        await message.reply("Вы сейчас не в игре.\nЧтобы начать новую игру, напишите команду /play ")
    await finish_game(game_id, 1)


async def make_go(game_id, x, y):
    st = games[game_id].go(x, y)
    players = games[game_id].players
    if st == -1:
        await bot.send_message(players[games[game_id].current], 'Некорректный ход')
        return 0
    
    if st == 2:    
        await send_field(game_id)
        return 1
    
    await send_field(game_id, 1)
    if st == 0:
        await bot.send_message(players[1-games[game_id].current], 'Вы выиграли!\nЧтобы начать новую игру, напишите команду /play ')
        await bot.send_message(players[games[game_id].current], 'Вы проиграли!\nЧтобы начать новую игру, напишите команду /play ')
    else:
        await bot.send_message(players[1-games[game_id].current], 'Ничья!\nЧтобы начать новую игру, напишите команду /play ')
        await bot.send_message(players[games[game_id].current], 'Ничья!\nЧтобы начать новую игру, напишите команду /play ')
    await finish_game(game_id)
    return 1
    


@dp.callback_query_handler()
async def some_text(callback : types.CallbackQuery):
    message = callback.message
    user_id = callback.from_user.id
    game_id = get_user_game(user_id)
    if game_id == -1 or game_id >= free_id:
        await message.reply("Вы сейчас не в игре. Напишите /play, чтобы играть.")
        await callback.answer()
        return
    # print(game_id)
    if games[game_id].players[games[game_id].current] != user_id:
        await message.reply("Сейчас не ваш ход")
        await callback.answer()
        return
    
    # print(callback)
    need_del = await make_go(game_id, int(callback.data[0]), int(callback.data[2]))
    if need_del:
        pass
        # await message.delete()
    await callback.answer()
    

    

start_db()

executor.start_polling(dp, skip_updates=True)
