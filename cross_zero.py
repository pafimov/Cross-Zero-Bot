import emoji
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

#class with cross-zero logic
class game:
    #symbols which game uses
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

    #checks if cell is correct
    def check_cell(self, x, y):
        if x >= self.sz or y >= self.sz or x < 0 or y < 0:
            return 0
        if self.field[x][y] == self.neutral:
            return 0
        return 1 

    #checks 4 in row
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

    #returns keyboard with current map
    def get_kb(self):
        kb = InlineKeyboardMarkup(row_width=3)
        for i in range(self.sz):
            cur_row = []
            for j in range(self.sz):
                cur_row.append(InlineKeyboardButton(text=self.field[i][j], callback_data=str(i) + ' '+ str(j)))
            kb.row(*cur_row)
        return kb

    #user made a move
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
