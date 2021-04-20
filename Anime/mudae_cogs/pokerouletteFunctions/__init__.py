from datetime import datetime as dt
from sqlite3 import connect
from discord import Embed, Colour
import asyncio
import pandas as pd
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)
"""
This holds all the constants and functions shared by all classes used in the pokeroulette module
"""

#############
# Constants #
#############
BASE_PATH = './mudae_cogs'
BACK = '\u2b05\ufe0f' # Left arrow
NEXT = '\u27a1\ufe0f' # Right arrow

achievement_requirements = {
	'rolls': {
		1: 10,
		2: 100,
		3: 500,
		4: 1000,
		5: 5000,
		6: 10000,
		7: 25000
	},
	'pokemon': {
		1: 10,
		2: 50,
		3: 100,
		4: 250,
		5: 500,
		6: 898,
		7: 946
	},
	'upgrades': {
		1: 1,
		2: 5,
		3: 10,
		4: 20,
		5: 50,
		6: 100
	},
	'released': {
		1: 10,
		2: 100,
		3: 500,
		4: 1000,
		5: 5000,
		6: 10000,
		7: 25000
	},
	'gifts': {
		1: 1,
		2: 5,
		3: 10,
		4: 25,
		5: 50
	},
	'boofs': {
		1: 1,
		2: 10,
	},
	'trades': {
		1: 1,
		2: 5,
		3: 10,
		4: 25,
		5: 50
	},
	'pokecash': {
		1: 1000,
		2: 10000,
		3: 50000,
		4: 100000,
		5: 1000000,
		6: 5000000,
		7: 10000000
	},
	'safari': {
		1: 1,
		2: 5,
		3: 10,
		4: 25,
		5: 50
	},
	'badges': {
		1: 1,
		2: 10,
		3: 50,
		4: 100,
		5: 250
	},
	'stored': {
		1: 100
	},
	'battles': {
		1: 10,
		2: 100,
		3: 250,
		4: 500,
		5: 1000
	},
	'gyms': {
		1: 1,
		2: 3,
		3: 5,
		4: 8
	},
	'levels': {
		1: 10,
		2: 100,
		3: 1000,
		4: 5000,
		5: 10000,
		6: 89800,
		7: 94600
	},
	'elite four': {
		1: 1,
		2: 5,
		3: 10,
		4: 25,
		5: 50
	},
	'raids': {
		1: 1,
		2: 5,
		3: 10,
		4: 25,
		5: 50
	},
	'raids complete': {
		1: 1,
		2: 5,
		3: 10,
		4: 25,
		5: 50
	}
}

achievement_stat_mapping = {
	'rolls': 'total_rolls',
	'pokemon': None,
	'upgrades': None,
	'released': 'total_released',
	'gifts': 'total_gifts',
	'boofs': 'boofs',
	'trades': 'total_traded',
	'pokecash': 'total_pokecash',
	'safari': 'total_bought',
	'badges': None,
	'stored': 'stored_rolls',
	'battles': 'total_battles',
	'gyms': None,
	'levels': None,
	'elite four': 'e4_completions',
	'raids': 'total_raids',
	'raids complete': 'raid_completions'
}

achievement_descriptions = {
	'rolls': 'Earned by rolling',
	'pokemon': 'Earned by owning unique pokemon',
	'upgrades': 'Earned by buying upgrades',
	'released': 'Earned by releasing pokemon',
	'gifts': 'Earned by giving gifts',
	'boofs': 'Earned by getting bOofs',
	'trades': 'Earned by trading with other players',
	'pokecash': 'Earned by increasing your total PokeCash',
	'safari': 'Earned by buying pokemon from the Safari Zone',
	'badges': 'Earned by getting pokemon badges',
	'stored': 'Earned by saving extra rolls.\nEarning all in this category rewards 2x daily rewards.',
	'battles': 'Earned by battling',
	'gyms': 'Earned by defeating gyms',
	'levels': 'Earned by getting your pokemon\'s total level up',
	'elite four': 'Earned by defeating the Elite Four',
	'raids': 'Earned by participating in raids',
	'raids complete': 'Earned by completing raids'
}

rarity_info = {
	1: {
		'chance': .875,
		'rolls': .5,
		'cash': 100,
		'exp': 5,
		'total': 164
	},
	2: {
		'chance': .125,
		'rolls': 1,
		'cash': 200,
		'exp': 10,
		'total': 217
	},
	3: {
		'chance': .0167,
		'rolls': 2,
		'cash': 400,
		'exp': 25,
		'total': 298
	},
	4: {
		'chance': .005,
		'rolls': 4,
		'cash': 1000,
		'exp': 100,
		'total': 134
	},
	5: {
		'chance': .0001,
		'rolls': 8,
		'cash': 2500,
		'exp': 500,
		'total': 74
	},
	6: {
		'chance': .00001,
		'rolls': 15,
		'cash': 10000,
		'exp': 1000,
		'total': 11
	},
	7: {
		'chance': .000055,
		'rolls': 25,
		'cash': 25000,
		'exp': 2500,
		'total': 1
	},
	8: {
		'chance': .0000275,
		'rolls': 40,
		'cash': 50000,
		'exp': 5000,
		'total': 1
	},
	9: {
		'chance': .000011,
		'rolls': 100,
		'cash': 125000,
		'exp': 12500,
		'total': 1
	}
}

#############
# Functions #
#############
# Formatting and Other #
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

# Upgrade Prices (and upgrade constant due to compiling order) #
def baserarity(level, discount):
	return int((500 + sum([(i+1)*25 for i in range(level)])) * discount)

def shinyrarity(level, discount):
	return int((1000 + 1000 * level) * discount)

def rollcooldown(level, discount):
	return int(5000 * discount)

def rollrefund(level, discount):
	return int((10000 + 2500 * level) * discount)

def higherroll(level, discount):
	return int(20000 * discount)

def doublecash(level, discount):
	return int(30000 * discount)

def dailycooldown(level, discount):
	return int((10000 + 2500 * level) * discount)

def upgradediscount(level, discount):
	return 50000

def safarirefresh(level, discount):
	return int(100000 * discount)

def dittocooldown(level, discount):
	return int((10000 + 2500 * level) * discount)

def fasterbadge(level, discount):
	return int((2000 + 2000 * level) * discount)

def huntchance(level, discount):
	return int((750 + sum([(i+1)*50 for i in range(level)])) * discount)

def exprates(level, discount):
	return int((1000 + 100 * level) * discount)

def battlecooldown(level, discount):
	return int((2500 + sum([(i+1)*50 for i in range(level)])) * discount)

def e4cooldown(level, discount):
	return int((10000 + 2500 * level) * discount)

def daycaretime(level, discount):
	return int((2000 + sum([(i+1)*100 for i in range(level)])) * discount)

def tradecooldown(level, discount):
	return int((4000 + 500 * level) * discount)

def fullreset(level, discount):
	return int(250000 * discount)

def raidchance(level, discount):
	return int((1250 + sum([(i+1)*75 for i in range(level)])) * discount)

def raidreset(level, discount):
	return int(500000 * discount)

upgrade_info = {
	1: {
		'name': 'baserarity',
		'max_level': 100,
		'description': 'Improve rarity rolls',
		'cost': baserarity,
		'category': 'Rolls'
	},
	2: {
		'name': 'shinyrarity',
		'max_level': 100,
		'description': 'Improve shiny chance',
		'cost': shinyrarity,
		'category': 'Rolls'
	},
	3: {
		'name': 'rollcooldown',
		'max_level': 9,
		'description': 'Reduce roll cooldown by 10 minutes',
		'cost': rollcooldown,
		'category': 'Cooldown'
	},
	4: {
		'name': 'rollrefund',
		'max_level': 5,
		'description': 'Improve chance to immediately refund roll',
		'cost': rollrefund,
		'category': 'Rolls'
	},
	6: {
		'name': 'doublecash',
		'max_level': 1,
		'description': 'Double cash refund value',
		'cost': doublecash,
		'category': 'Rolls'
	},
	7: {
		'name': 'dailycooldown',
		'max_level': 8,
		'description': 'Reduce daily cooldown by 1 hour',
		'cost': dailycooldown,
		'category': 'Cooldown'
	},
	8: {
		'name': 'upgradediscount',
		'max_level': 1,
		'description': 'Reduces the costs of upgrades by 25%',
		'cost': upgradediscount,
		'category': 'Misc'
	},
	9: {
		'name': 'fasterbadge',
		'max_level': 5,
		'description': 'Reduces the amount of pokemon required for a badge by 1',
		'cost': fasterbadge,
		'category': 'Misc'
	},
	10: {
		'name': 'huntchance',
		'max_level': 100,
		'description': 'Increases the chance to get the pokemon being hunted',
		'cost': huntchance,
		'category': 'Rolls'
	},
	11: {
		'name': 'safarirefresh',
		'max_level': 9999,
		'description': 'Refreshes the Safari Zone for everyone',
		'cost': safarirefresh,
		'category': 'Misc'
	},
	12: {
		'name': 'dittocooldown',
		'max_level': 8,
		'description': 'Reduce ditto cooldown by 1 hour',
		'cost': dittocooldown,
		'category': 'Cooldown'
	},
	13: {
		'name': 'exprates',
		'max_level': 100,
		'description': 'Improve the exp gain from battling',
		'cost': exprates,
		'category': 'Battle'
	},
	14: {
		'name': 'battlecooldown',
		'max_level': 9,
		'description': 'Reduce battle cooldown by 10 minutes',
		'cost': battlecooldown,
		'category': 'Cooldown'
	},
	15: {
		'name': 'e4cooldown',
		'max_level': 8,
		'description': 'Reduce Elite Four cooldown by 1 hour',
		'cost': e4cooldown,
		'category': 'Cooldown'
	},
	16: {
		'name': 'daycaretime',
		'max_level': 6,
		'description': 'Reduce reward interval of daycare by 1 hour',
		'cost': daycaretime,
		'category': 'Cooldown'
	},
	17: {
		'name': 'tradecooldown',
		'max_level': 8,
		'description': 'Reduce WonderTrade cooldown by 1 hour',
		'cost': tradecooldown,
		'category': 'Cooldown'
	},
	18: {
		'name': 'fullreset',
		'max_level': 9999,
		'description': 'Resets every cooldown',
		'cost': fullreset,
		'category': 'Misc'
	},
	19: {
		'name': 'raidchance',
		'max_level': 50,
		'description': 'Improve the chance to get a pokemon from a raid',
		'cost': raidchance,
		'category': 'Battle'
	},
	20: {
		'name': 'raidreset',
		'max_level': 9999,
		'description': 'Resets the raid cooldown',
		'cost': raidreset,
		'category': 'Misc'
	}
}

# Database #
def sql(query, args=()):
	conn = connect(f'{BASE_PATH}/pokeroulette.db', isolation_level=None)
	cur = conn.cursor()
	cur.execute(query, args)
	try:
		_df = pd.DataFrame.from_records(cur.fetchall(), columns=[desc[0] for desc in cur.description])
		conn.close()
		return _df
	except Exception:
		return pd.DataFrame()

###########
# Classes #
###########
class Page:
	def __init__(self, author, desc, colour=(255, 50, 20), title=None, icon=None, image=None, thumbnail=None, footer=None):
		self.author = author
		self.desc = self.parse_desc(desc)
		self.colour = colour
		self.title = title
		self.icon = icon
		self.image = image
		self.thumbnail = thumbnail
		self.footer = footer

	@property
	def embed(self):
		emb = Embed(
			description=self.desc,
			colour=Colour.from_rgb(*self.colour)
		)
		if self.title:
			emb.title = self.title
		if self.icon:
			emb.set_author(name=self.author, icon_url=self.icon)
		else:
			emb.set_author(name=self.author)
		if self.image:
			emb.set_image(url=self.image)
		if self.thumbnail:
			emb.set_thumbnail(url=self.thumbnail)
		if self.footer:
			emb.set_footer(text=self.footer)
		return emb

	def parse_desc(self, desc):
		if isinstance(desc, str):
			return desc
		elif isinstance(desc, list) or isinstance(desc, tuple):
			return '\n'.join(desc)
		else:
			raise TypeError(f'Expected str or iterable, got {type(desc)}')