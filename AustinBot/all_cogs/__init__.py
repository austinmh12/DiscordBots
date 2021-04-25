from datetime import datetime as dt, timedelta as td
from sqlite3 import connect
import pandas as pd
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

#############
# Constants #
#############
BASE_PATH = './all_cogs'
BACK = '\u2b05\ufe0f' # Left arrow
NEXT = '\u27a1\ufe0f' # Right arrow

def format_remaining_time(date):
	time = date - dt.now()
	hrs, rem = divmod(time.total_seconds(), 3600)
	min_ = rem // 60 + 1
	if min_ == 60 and hrs:
		min_ = 59
	if hrs:
		return f'{int(hrs)}h {int(min_)}min'
	return f'{int(min_)}min'

def chunk(l, size):
	for i in range(0, len(l), size):
		yield l[i:i+size]

def sql(file, query, args=()):
	conn = connect(f'{BASE_PATH}/{file}.db', isolation_level=None)
	cur = conn.cursor()
	cur.execute(query, args)
	try:
		_df = pd.DataFrame.from_records(cur.fetchall(), columns=[desc[0] for desc in cur.description])
		conn.close()
		return _df
	except Exception:
		return pd.DataFrame()