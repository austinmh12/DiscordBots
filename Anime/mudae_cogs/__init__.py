from datetime import datetime as dt, timedelta as td
from psycopg2 import connect, ProgrammingError
import pandas as pd, numpy as np
import sys

# ENV
with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

# CONSTANTS
waifu_channel = 761112336286220309
mudae_id = 432610292342587392

# UTILITIES
def le_minutes(time, n=20):
	if time > dt.now():
		return (time - dt.now()).total_seconds() // 60 + 1 <= n
	return True


# DATABASE
def sql(q, args):
	conn = connect(database='pisscord', host='localhost', port='5432', user=ENV['DBUSER'], password=ENV['DBPASS'])
	conn.autocommit = True
	cur = conn.cursor()
	cur.execute(q, args)
	try:
		_df = pd.DataFrame.from_records(cur.fetchall(), columns=[desc[0] for desc in cur.description])
		conn.close()
		return _df
	except ProgrammingError:
		return

def get_user_id(user):
	if isinstance(user, str): # Username search
		df = sql('SELECT id FROM users WHERE user_name = %s', (user,))
	elif isinstance(user, int): # Discord ID search
		df = sql('SELECT id FROM users WHERE discord_id = %s', (user,))
	else:
		raise TypeError(f'user must be of type str or int, not {type(user)}')
	if df.empty:
		return
	return int(df.id[0])

def add_user(discord_id, user_name):
	sql('INSERT INTO users (discord_id, user_name) VALUES (%s, %s)', (discord_id, user_name,))
	user_id = get_user_id(discord_id)
	sql('INSERT INTO waifu_info (user_id) VALUES (%s)', (user_id,))
	sql('INSERT INTO poke_info (user_id) VALUES (%s)', (user_id,))

def get_user_resets():
	df = sql('''SELECT 
		u.discord_id,
		wi.claim_reset, 
		wi.rolls_reset,
		wi.daily_reset,
		wi.react_reset,
		wi.kakera_reset,
		pi.poke_reset
	FROM
		users u
		INNER JOIN waifu_info wi ON wi.user_id = u.id
		INNER JOIN poke_info pi ON pi.user_id = u.id''',
	())
	return df

def get_timer(user, timer, table):
	user_id = get_user_id(user)
	df = sql('SELECT {} FROM {} WHERE user_id = %s'.format(timer, table), (user_id,))
	if df.empty:
		return
	return df[timer][0]

def update_user_timer(user, timer, table, value):
	user_id = get_user_id(user)
	return sql('UPDATE {} SET {} = %s WHERE user_id = %s'.format(table, timer), (value, user_id,))

def update_waifu_timers(user, claim_reset, rolls_reset, daily_reset, react_reset, kakera_reset):
	user_id = get_user_id(user)
	return sql('''UPDATE waifu_info
	SET
		claim_reset = %s,
		rolls_reset = %s,
		daily_reset = %s,
		react_reset = %s,
		kakera_reset = %s
	WHERE
		user_id = %s''',
	(claim_reset, rolls_reset, daily_reset, react_reset, kakera_reset, user_id,))