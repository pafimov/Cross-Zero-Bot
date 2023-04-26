import sqlite3 as sq

#work with database
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
    
#checks if user is in database
def check_auth(user_id):
    if get_user_game(user_id) == -2:
        print("NEW USER!!")
        add_to_db(user_id)