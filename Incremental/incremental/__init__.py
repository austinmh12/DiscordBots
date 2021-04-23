from psycopg2 import connect, ProgrammingError
import pandas as pd, numpy as np

# ENV
with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

# Global Utilities
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
	df = sql('SELECT id FROM users WHERE discord_id = %s', (user,))
	if df.empty:
		return
	return int(df.id[0])

def get_resource_id(resource):
	df = sql('SELECT id FROM resources WHERE name = %s', (resource,))
	if df.empty:
		return
	return int(df.id[0])

def reply_to_choice(s):
	if s.lower() == 'none':
		return
	try:
		return int(s)
	except ValueError:
		return s

# Global Classes:
class _Resource:
	def __init__(self, id, name, amount, produces, cost, unlock, unlock_amount, *args, **kwargs):
		self.id = id
		self.name = name
		self.amount = amount
		self.produces = produces
		self.cost = cost
		self.unlock = unlock
		self.unlock_amount = unlock_amount

	@classmethod
	def from_row(cls, *args, **kwargs):
		return cls(*args, **kwargs)
	# Money = _Resource(2, 'money', 10, None, 0, None, None)
	# Jobs = _Resource(3, 'jobs', 0, Money, 10, Money, 10)
	# Corporation = _Resource(4, 'corporations', 0, Jobs, 100, Jobs, 50)
	#

class _Player:
	def __init__(self, id, discord_id, resources):
		self.id = id
		self.discord_id = discord_id
		self.resources = resources

	@classmethod
	def from_row(cls, *args, **kwargs):
		return cls(*args, **kwargs)