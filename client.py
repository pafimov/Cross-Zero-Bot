from aiogram import types, Dispatcher
from database_work import get_user_game, add_to_db, edit_user_game, check_auth
from create_and_start import bot, games, free_id, waiting
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from cross_zero import game

# @dp.message_handler(commands=['start', 'help'])
async def go_hello(message : types.Message):
    game_id = get_user_game(message.from_id)
    if game_id == -2:
        print("NEW USER!!")
        add_to_db(message.from_id)
        await message.reply('Привет! Это игра в Крестики-Нолики!\nЧтобы начать новую игру, нажмите /play ')
    elif game_id == -1:
        await message.reply('Чтобы начать новую игру, нажмите /play ')
    else:
        await message.reply('Вы сейчас находитесь в игре. Продолжите игру, либо, если хотите её завершить, нажмите /stop ')

#sends current field to players
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


#starts a game
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

#adds to queue
async def search_for_opponent(user_id, sz):
    global free_id
    if waiting[sz] != -1:
        await start_game(waiting[sz], user_id, sz)
        waiting[sz] = -1
    else:
        waiting[sz] = user_id

# @dp.message_handler(commands=['play'], state=None)
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

# @dp.message_handler(state=FSM_search_game.sz)
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

#finish and delete the game
async def finish_game(game_id, someone=0):
    players = games[game_id].players
    edit_user_game(players[0], -1)
    edit_user_game(players[1], -1)
    del games[game_id]
    if someone == 1:
        await bot.send_message(players[0], 'Игра завершена одним из игроков.\nЧтобы начать новую игру, нажмите команду /play ')
        await bot.send_message(players[1], 'Игра завершена одним из игроков.\nЧтобы начать новую игру, нажмите команду /play ')

#manual game stop
# @dp.message_handler(commands=['stop'])
async def stop_game(message : types.Message):
    check_auth(message.from_id)
    global free_id
    game_id = get_user_game(message.from_id)
    if game_id == -1 or game_id >= free_id:
        await message.reply("Вы сейчас не в игре.\nЧтобы начать новую игру, нажмите /play ")
        return
    await finish_game(game_id, 1)

#manual seaching for opponent stop
# @dp.message_handler(commands=['cancel'])
async def stop_searching(message : types.Message):
    check_auth(message.from_id)
    global waiting
    user_id = message.from_id
    if user_id not in waiting:
        await message.reply("Вы сейчас не в поиске.\nЧтобы начать новую игру, нажмите /play ")
        return
    waiting[waiting.index(user_id)] = -1
    await message.reply("Поиск остановлен.\nЧтобы начать новую игру, нажмите /play ")
    
#handles user's move
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
    

# @dp.callback_query_handler()
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
    

def register_handlers(dp : Dispatcher):
    dp.register_message_handler(go_hello, commands=['start', 'help'])
    dp.register_message_handler(go_choose_sz, commands=['play'], state=None)
    dp.register_message_handler(sz_chosen, state=FSM_search_game.sz)
    dp.register_message_handler(stop_game, commands=['stop'])
    dp.register_message_handler(stop_searching, commands=['cancel'])
    dp.register_callback_query_handler(some_text)