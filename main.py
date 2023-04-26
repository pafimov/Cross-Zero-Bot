from aiogram import Bot, executor, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3 as sq
import emoji


storage = MemoryStorage()
bot = Bot('6235349333:AAH37djTzR62bJYXgDnbPKdA8K0wo-lktBU')
dp = Dispatcher(bot, storage=storage)

def start_db():
    global base, cur
    base = sq.connect('Database.db')
    cur = base.cursor()
    if base:
        print("DB OKAY")
    base.execute('CREATE TABLE IF NOT EXISTS users(id BIGINT PRIMARY KEY, game BIGINT)')
    base.execute('UPDATE users SET game=?', ('-1',))
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
        await message.reply('Привет! Это игра в Крестики-Нолики!\nЧтобы начать новую игру, нажмите /play ')
    elif game_id == -1:
        await message.reply('Чтобы начать новую игру, нажмите /play ')
    else:
        await message.reply('Вы сейчас находитесь в игре. Продолжите игру, либо, если хотите её завершить, нажмите /stop ')


def check_auth(user_id):
    if get_user_game(user_id) == -2:
        print("NEW USER!!")
        add_to_db(user_id)

class game:
    symb = [emoji.emojize(":cross_mark:"), emoji.emojize(":green_circle:")]
    neutral = emoji.emojize(":white_large_square:")
    def __init__(self, _player1, _player2, _sz):
        self.players = [_player1, _player2]
        self.field = []
        self.sz = _sz
        self.current = 0
        self.need_to_win = 3
        if self.sz >= 5:
            self.need_to_win = 4
        for i in range(self.sz):
            row = [self.neutral for j in range(self.sz)]
            self.field.append(row)

    def check_cell(self, x, y):
        if x >= self.sz or y >= self.sz or x < 0 or y < 0:
            return 0
        if self.field[x][y] == self.neutral:
            return 0
        return 1 

    def have_winning_path(self, x, y, dx, dy):
        cur_el = self.field[x][y]
        ok = 1
        for k in range(self.need_to_win):
            if self.check_cell(x, y) == 0:
                ok = 0
                break
            if self.field[x][y] != cur_el:
                ok = 0
                break
            x += dx
            y += dy
        return ok

    #returns -1 if game continues
    #returns 0 if someone won
    #returns 1 if its draw
    def check_won(self):
        #check the draw
        cnt_free = 0
        for i in range(self.sz):
            for j in range(self.sz):
                if self.field[i][j] == self.neutral:
                    cnt_free+=1
        if cnt_free == 0:
            return 1
        
        n = self.sz
        for i in range(n):
            for j in range(n):
                #(i, j) - left upper corner
                #check bottom way
                if self.have_winning_path(i, j, 1, 0):
                    return 0
                #check right way
                if self.have_winning_path(i, j, 0, 1):
                    return 0
                #check bottom-right way
                if self.have_winning_path(i, j, 1, 1):
                    return 0
                #check bottom-left way
                if self.have_winning_path(i, j, 1, -1):
                    return 0
        
        return -1

    def get_kb(self):
        kb = InlineKeyboardMarkup(row_width=3)
        for i in range(self.sz):
            cur_row = []
            for j in range(self.sz):
                cur_row.append(InlineKeyboardButton(text=self.field[i][j], callback_data=str(i) + ' '+ str(j)))
            kb.row(*cur_row)
        return kb

    def go(self, x, y):
        was = self.current
        if self.field[x][y] != self.neutral:
            return -1
        
        self.field[x][y] = self.symb[was]
        self.current = 1-self.current
        res_check = self.check_won()
        if res_check != -1:
            return res_check
        return 2

        
waiting = [-1 for i in range(10)]
free_id = 0
games = dict()

async def send_field(game_id, final = 0):
    kb = games[game_id].get_kb()
    players = games[game_id].players
    if final == 0:
        await bot.send_message(players[games[game_id].current], 'Ваш ход - - - - - - - -', reply_markup=kb)
        await bot.send_message(players[1-games[game_id].current], 'Ход соперника- - - -', reply_markup=kb)
    else:
        await bot.send_message(players[games[game_id].current], 'Финальная карта- - -', reply_markup=kb)
        await bot.send_message(players[1-games[game_id].current], 'Финальная карта- - -', reply_markup=kb)

class FSM_search_game(StatesGroup):
    sz = State()

async def start_game(player1, player2, sz):
    global free_id
    edit_user_game(player1, free_id)
    edit_user_game(player2, free_id)
    new_game = game(player1, player2, sz)
    games[free_id] = new_game
    game_id = free_id
    free_id+=1
    await bot.send_message(player1, f"Игра началась!\nВам нужно поставить {games[game_id].need_to_win} {games[game_id].symb[0]} в ряд или в диагональ для победы. \nЧтобы завершить игру до её окончания, нажмите /stop ")
    await bot.send_message(player2, f"Игра началась!\nВам нужно поставить {games[game_id].need_to_win} {games[game_id].symb[1]} в ряд или в диагональ для победы. \nЧтобы завершить игру до её окончания, нажмите /stop ")
    await send_field(game_id)

async def search_for_opponent(user_id, sz):
    global free_id
    if waiting[sz] != -1:
        await start_game(waiting[sz], user_id, sz)
        waiting[sz] = -1
    else:
        waiting[sz] = user_id


@dp.message_handler(commands=['play'], state=None)
async def go_choose_sz(message : types.Message):
    check_auth(message.from_id)
    game_id = get_user_game(message.from_id)
    if game_id != -1:
        await message.reply('Вы сейчас находитесь в игре. Продолжите игру, либо, если хотите её завершить, нажмите /stop ')
        return
    if message.from_id in waiting:
        await message.reply('Вы уже в очереди.\nЧтобы остановить поиск, нажмите /cancel ')
        return
    await FSM_search_game.sz.set()
    kb = ReplyKeyboardMarkup(row_width=3).add(KeyboardButton('3x3'), KeyboardButton('5x5'), KeyboardButton('7x7'))
    await message.reply("Выберите размер игрового поля!", reply_markup=kb)

@dp.message_handler(state=FSM_search_game.sz)
async def sz_chosen(message: types.Message, state : FSM_search_game):
    allowed_sz = ('3x3', '5x5', '7x7')
    if not message.text in allowed_sz:
        await message.reply('Выберите корректный размер поля из предложенных ниже!')
        return
    async with state.proxy() as data:
        data['sz'] = int(message.text[0])

    async with state.proxy() as data:
        await message.reply('Ищу соперника!\nЧтобы остановить поиск, нажмите /cancel ', reply_markup=ReplyKeyboardRemove())
        await search_for_opponent(message.from_id, data['sz'])

    await state.finish()

async def finish_game(game_id, someone=0):
    players = games[game_id].players
    edit_user_game(players[0], -1)
    edit_user_game(players[1], -1)
    del games[game_id]
    if someone == 1:
        await bot.send_message(players[0], 'Игра завершена одним из игроков.\nЧтобы начать новую игру, нажмите команду /play ')
        await bot.send_message(players[1], 'Игра завершена одним из игроков.\nЧтобы начать новую игру, нажмите команду /play ')

@dp.message_handler(commands=['stop'])
async def stop_game(message : types.Message):
    check_auth(message.from_id)
    global free_id
    game_id = get_user_game(message.from_id)
    if game_id == -1 or game_id >= free_id:
        await message.reply("Вы сейчас не в игре.\nЧтобы начать новую игру, нажмите /play ")
        return
    await finish_game(game_id, 1)

@dp.message_handler(commands=['cancel'])
async def stop_searching(message : types.Message):
    check_auth(message.from_id)
    global waiting
    user_id = message.from_id
    if user_id not in waiting:
        await message.reply("Вы сейчас не в поиске.\nЧтобы начать новую игру, нажмите /play ")
        return
    waiting[waiting.index(user_id)] = -1
    await message.reply("Поиск остановлен.\nЧтобы начать новую игру, нажмите /play ")
    



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
        await bot.send_message(players[1-games[game_id].current], 'Вы выиграли!\nЧтобы начать новую игру, нажмите /play ')
        await bot.send_message(players[games[game_id].current], 'Вы проиграли!\nЧтобы начать новую игру, нажмите /play ')
    else:
        await bot.send_message(players[1-games[game_id].current], 'Ничья!\nЧтобы начать новую игру, нажмите /play ')
        await bot.send_message(players[games[game_id].current], 'Ничья!\nЧтобы начать новую игру, нажмите /play ')
    await finish_game(game_id)
    return 1
    


@dp.callback_query_handler()
async def some_text(callback : types.CallbackQuery):
    message = callback.message
    user_id = callback.from_user.id
    game_id = get_user_game(user_id)
    if game_id == -1 or game_id >= free_id:
        await message.reply("Вы сейчас не в игре. нажмите /play, чтобы играть.")
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
