from sqlite3 import connect
import pandas as pd
import requests as r

# API Function
def mtgapi(path, params={}):
	url = f'https://api.magicthegathering.io/v1/{path}'
	resp = r.get(url, params=params)
	resp.raise_for_status()
	if not resp.text:
		return None
	else:
		return resp.json()

# Database Functions
def sql(query, args):
	conn = connect('./mtg/mtg.db', isolation_level=None)
	cur = conn.cursor()
	cur.execute(query, args)
	try:
		_df = pd.DataFrame.from_records(cur.fetchall(), columns=[desc[0] for desc in cur.description])
		conn.close()
		return _df
	except Exception:
		return pd.DataFrame()

def query_builder(base, **kwargs):
	vals = []
	base += ' WHERE '
	for i, (k, v) in enumerate(kwargs.items(), start=1):
		base += f'{k} = ? {"AND " if i < len(kwargs) else ""}'
		v = ' '.join([c.capitalize() for c in v.split()]) if isinstance(v, str) else v
		vals.append(v)
	return base, vals

# Command functions
def parse_args(s):
	if '=' not in s:
		return {'name': s}
	return {p.split('=')[0]: p.split('=')[1] for p in s.split('/')}