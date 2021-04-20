from . import sql, chunk, rarity_info, BASE_PATH, Page
from datetime import datetime as dt, timedelta as td
from io import BytesIO
from pandas import DataFrame
from PIL import Image
from random import choice, choices, random
import json
import logging
import requests as r

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

#############
# Constants #
#############
UPDATE_ROULETTE = '''update roulette 
set amount = (select tr.amount from tmp_roulette tr where tr.user_id = roulette.user_id and tr.poke_id = roulette.poke_id and tr.shiny = roulette.shiny)
where roulette.user_id in (select tr.user_id from tmp_roulette tr where tr.user_id = roulette.user_id and tr.poke_id = roulette.poke_id and tr.shiny = roulette.shiny)
	and roulette.poke_id in (select tr.poke_id from tmp_roulette tr where tr.user_id = roulette.user_id and tr.poke_id = roulette.poke_id and tr.shiny = roulette.shiny)
	and roulette.shiny in (select tr.shiny from tmp_roulette tr where tr.user_id = roulette.user_id and tr.poke_id = roulette.poke_id and tr.shiny = roulette.shiny);'''

shiny_chance = 1/8192

default_rewards = {
	'levels': 0,
	'cash': 0,
	'rolls': 0,
	'rewards': 0
}

#############
# Functions #
#############
# Pokemon #
def get_all_pokemon():
	df = sql('select * from pokemon')
	return [Pokemon(**d) for d in df.to_dict('records')]

def get_pokemon(args):
	shiny = 0
	name = ' '.join(args) if isinstance(args, tuple) else args
	if isinstance(name, str):
		if name[-1] == 'S':
			name = name[:-1]
			shiny = 1
	try:
		id = float(name)
		pkmn = get_pokemon_by_id(id)
	except ValueError:
		pkmn = get_pokemon_by_name(name)
	if not pkmn:
		return None
	pkmn.shiny = shiny
	return pkmn

def get_pokemon_by_id(id):
	df = sql('select * from pokemon where id = ?', (id,))
	if df.empty:
		return None
	return Pokemon(**df.to_dict('records')[0])

def get_pokemon_by_name(name):
	df = sql('select * from pokemon where lower(name) = ?', (name.lower(),))
	if df.empty:
		return None
	return Pokemon(**df.to_dict('records')[0])

def get_all_pokemon_by_rarity(rarity):
	df = sql('select * from pokemon where rarity = ?', (rarity,))
	return [Pokemon(**d) for d in df.to_dict('records')]

def get_random_pokemon_by_rarity(rarity):
	return choice(get_all_pokemon_by_rarity(rarity))

# Pokedex #
def get_user_pokedex(user):
	df = sql('select r.user_id, r.amount, r.shiny, p.* from roulette r left join pokemon p on p.id = r.poke_id where r.user_id = ?', (user.id,))
	if df.empty:
		return []
	return [PokedexEntry(**d) for d in df.to_dict('records')]

def get_user_pokedex_entry(user, pkmn):
	df = sql('select r.user_id, r.amount, r.shiny, p.* from roulette r left join pokemon p on p.id = r.poke_id where r.user_id = ? and r.poke_id = ? and r.shiny = ?', (user.id, pkmn.id, pkmn.shiny))
	if df.empty:
		return None
	return PokedexEntry(**df.to_dict('records')[0])

def get_duplicate_pokedex_extries(user, rarity):
	return [pkdx for pkdx in get_user_pokedex(user) if pkdx.amount > 1 and pkdx.rarity <= rarity]

def add_or_update_user_pokedex_entry_from_pokemon(user, pkmn_list, pkmn_counter):
	user_pkdx = get_user_pokedex(user)
	unique = list(set(pkmn_list))
	new = [p for p in unique if p not in user_pkdx]
	updating = [p for p in unique if p not in new]
	if new:
		new_chunks = chunk(new, 249)
		for nc in new_chunks:
			vals = []
			sql_str = 'insert into roulette values '
			for p in nc:
				sql_str += ' (?,?,?,?),'
				vals.extend((user.id, p.id, pkmn_counter[p], p.shiny))
			sql(sql_str[:-1], vals)
	if updating:
		sql('drop table if exists tmp_roulette')
		sql('create table tmp_roulette (user_id INTEGER, poke_id INTEGER, amount INTEGER, shiny INTEGER)')
		pkdx_map = {pkdx.id: pkdx for pkdx in user_pkdx}
		updating_chunks = chunk(updating, 249)
		for uc in updating_chunks:
			vals = []
			sql_str = 'insert into tmp_roulette values '
			for p in uc:
				sql_str += ' (?,?,?,?),'
				amt = pkdx_map.get(p.id).amount + pkmn_counter[p]
				vals.extend((user.id, p.id, amt, p.shiny))
			sql(sql_str[:-1], vals)
		sql(UPDATE_ROULETTE)

def add_or_update_user_pokedex_entry_from_pokedex_entries(user, pokedex_entries):
	new = [pkdx for pkdx in pokedex_entries if pkdx.amount == -1]
	updating = [pkdx for pkdx in pokedex_entries if pkdx.amount >= 0]
	deleting = []
	if new:
		new_chunks = chunk(new, 249)
		for nc in new_chunks:
			vals = []
			sql_str = 'insert into roulette values '
			for p in nc:
				sql_str += ' (?,?,?,?),'
				vals.extend([p.user_id, p.id, 1, p.shiny])
			sql(sql_str[:-1], vals)
	if updating:
		sql('drop table if exists tmp_roulette')
		sql('create table tmp_roulette (user_id INTEGER, poke_id INTEGER, amount INTEGER, shiny INTEGER)')
		updating_chunks = chunk(updating, 249)
		for uc in updating_chunks:
			vals = []
			sql_str = 'insert into tmp_roulette values '
			for p in uc:
				sql_str += ' (?,?,?,?),'
				vals.extend(p.to_row)
				if p.amount == 0:
					deleting.append(p)
			sql(sql_str[:-1], vals)
		sql(UPDATE_ROULETTE)
	if deleting:
		sql('delete from roulette where amount = 0')
		deleting_chunks = chunk(deleting, 249)
		for dc in deleting_chunks:
			vals = [user.id]
			sql_str = 'delete from battle where user_id = ? and poke_id in ('
			for p in dc:
				sql_str += '?,'
				vals.append(p.id)
			sql_str = f'{sql_str[:-1]})'
			sql(sql_str, vals)

# PokeBattle #
def get_pokemon_info(id):
	df = sql('select * from poke_info where poke_id = ?', (id,))
	return df.to_dict('records')[0]

def get_all_user_poke_battle(user, level=1):
	df = sql('select b.user_id, b.level, b.exp, pi.hp, pi.attack, pi.defense, p.* from battle b left join poke_info pi on b.poke_id = pi.poke_id left join pokemon p on b.poke_id = p.id where b.user_id = ? and level >= ?', (user.id, level))
	if df.empty:
		return []
	return [PokeBattle(**d) for d in df.to_dict('records')]

def get_user_poke_battle(user, poke_id):
	df = sql('select b.user_id, b.level, b.exp, pi.hp, pi.attack, pi.defense, p.* from battle b left join poke_info pi on b.poke_id = pi.poke_id left join pokemon p on b.poke_id = p.id where b.user_id = ? and b.poke_id = ?', (user.id, poke_id))
	if df.empty:
		return None
	return PokeBattle(**df.to_dict('records')[0])

def get_user_total_level(user):
	pkbts = get_all_user_poke_battle(user)
	if pkbts:
		return sum([pkbt.level for pkbt in pkbts])
	return 0

def create_user_poke_battle(user, pkmn):
	pkin = get_pokemon_info(pkmn.id)
	pkbt = PokeBattle(user.id, 1, 0, pkin['hp'], pkin['attack'], pkin['defense'], id=pkmn.id, name=pkmn.name, rarity=pkmn.rarity, shiny=pkmn.shiny)
	sql('insert into battle values (?,?,?,?)', pkbt.pokebattle_creation_row)
	return pkbt

# Daycare #
def get_user_daycare(user):
	df = sql('select d.user_id, d.enter_time, d.rewards, p.* from daycare d left join pokemon p on d.poke_id = p.id where user_id = ?', (user.id,))
	if df.empty:
		return None
	return Daycare(**df.to_dict('records')[0])

def create_user_daycare(user, pkmn):
	pkdc = Daycare(user.id, dt.now(), default_rewards, **pkmn.to_dict())
	sql('insert into daycare values (?,?,?,?)', pkdc.daycare_creation_row)
	return pkdc

def delete_user_daycare(user):
	sql('delete from daycare where user_id = ?', (user.id,))

# Badge #
def get_badges(user):
	df = sql('select b.user_id, b.level, b.amount, p.* from badges b left join pokemon p on b.poke_id = p.id where user_id = ?', (user.id,))
	if df.empty:
		return []
	return [Badge(**d) for d in df.to_dict('records')]

def get_badge(user, poke_id):
	df = sql('select b.user_id, b.level, b.amount, p.* from badges b left join pokemon p on b.poke_id = p.id where user_id = ? and poke_id = ?', (user.id, poke_id))
	if df.empty:
		return ()
	return Badge(**df.to_dict('records')[0])

def add_badge(user, poke_id):
	sql('insert into badges values (?,?,?,?)', (user.id, poke_id, 1, 1))

# General #
def roll_pokemon(user):
	ret = []
	hunting = get_pokemon_by_id(user._hunting['poke_id']) if user._hunting['poke_id'] else None
	for i in range(6):
		chance = min(rarity_info.get(i+1).get('chance') * (1.1 ** user.get_upgrade('baserarity')), .99)
		if random() <= chance:
			if hunting and hunting.rarity == i+1:
				all_pkmn = get_all_pokemon_by_rarity(i+1)
				pkmn_weights = [(1 if hunting != p else min(3, 1 * ((1.02 + .02 * user.get_upgrade('huntchance')) ** max(user._hunting['caught'], 1)))) for p in all_pkmn]
				pkmn = choices(all_pkmn, weights=pkmn_weights)[0]
			else:
				pkmn = get_random_pokemon_by_rarity(i+1)
			shiny = shiny_chance * (1.1 ** user.get_upgrade('shinyrarity'))
			if random() <= shiny:
				pkmn.shiny = 1
			ret.append(pkmn)
		else:
			ret.append(None)
	return ret

def roll_all_pokemon(user):
	tmp = []
	for _ in range(int(user.stored_rolls)):
		tmp.extend([1,2,3,4,5,6])
	df = DataFrame(tmp, columns=['rarity'])
	all_pkmn = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: []}
	for pkmn in get_all_pokemon():
		all_pkmn[pkmn.rarity].append(pkmn)
	caught = []
	hunting = get_pokemon_by_id(user._hunting['poke_id']) if user._hunting['poke_id'] else None
	user_chance = 1.1 ** user.get_upgrade('baserarity')
	user_shiny = shiny_chance * 1.1 ** user.get_upgrade('shinyrarity')
	for row in df.values.tolist():
		chance = min(rarity_info.get(row[0]).get('chance') * user_chance, .99)
		if random() <= chance:
			if hunting and hunting.rarity == row[0]:
				pkmn_weights = [(1 if hunting != p else min(3, 1 * ((1.02 + .02 * user.get_upgrade('huntchance')) ** max(user._hunting['caught'], 1)))) for p in all_pkmn[row[0]]]
				pkmn = choices(all_pkmn[row[0]], weights=pkmn_weights)[0]
			else:
				pkmn = choice(all_pkmn[row[0]])
			if random() <= user_shiny:
				pkmn.shiny = 1
			caught.append(pkmn)
		else:
			caught.append(None)
	df['caught'] = caught
	return df

def gen_result_pic(pkmn_rolls):
	ids = [(p.id if p else 'x') for p in pkmn_rolls]	
	imgs = [Image.open(f'{BASE_PATH}/rsc/{i}.png') for i in ids]
	w = sum([i.size[0] for i in imgs])
	h = max([i.size[1] for i in imgs])
	bg = Image.new('RGBA', (w, h), color=(255,255,255,0))
	x = 0
	for img in imgs:
		img = img.convert('RGBA')
		bg.paste(img, (x, h-img.size[1]), img)
		x += img.size[0]
	bg.save(f'{BASE_PATH}/rsc/tmp.png')

def get_pkmn_colour(url):
	resp = r.get(url)
	im = Image.open(BytesIO(resp.content))
	im.thumbnail((1, 1))
	return im.getpixel((0, 0))

###########
# Classes #
###########
class Pokemon:
	def __init__(self, id, name, rarity, shiny=0):
		self.id = id
		self.name = name
		self.rarity = rarity
		self.shiny = shiny

	@property
	def url(self):
		url_name = self.name
		if url_name == 'NidoranF':
			url_name = 'nidoran-f'
		if url_name == 'NidoranM':
			url_name = 'nidoran-m'
		if url_name == 'Meowstic':
			url_name = 'meowstic-m'
		if 'Mega' in url_name:
			if url_name[-1] == 'X':
				suffix = 'megax'
			elif url_name[-1] == 'Y':
				suffix = 'megay'
			else:
				suffix = 'mega'
			url_name = f'{self.name.split(" ")[1]}-{suffix}'
		url_name = url_name.lower().replace(':','').replace('.','').replace("'",'').replace(' ','-')
		if self.shiny:
			return f'https://projectpokemon.org/images/shiny-sprite/{url_name}.gif'
		return f'https://projectpokemon.org/images/normal-sprite/{url_name}.gif'
	
	@property
	def icon(self):
		url_name = self.name
		if url_name == 'NidoranF':
			url_name = 'nidoran-f'
		if url_name == 'NidoranM':
			url_name = 'nidoran-m'
		if url_name == 'Meowstic':
			url_name = 'meowstic-m'
		if 'Mega' in url_name:
			if url_name[-1] == 'X':
				suffix = 'mega-x'
			elif url_name[-1] == 'Y':
				suffix = 'mega-y'
			else:
				suffix = 'mega'
			url_name = f'{self.name.split(" ")[1]}-{suffix}'
		url_name = url_name.lower().replace(':','').replace('.','').replace("'",'').replace(' ','-')
		if self.shiny:
			return f'https://img.pokemondb.net/sprites/home/shiny/{url_name}.png'
		return f'https://img.pokemondb.net/sprites/home/normal/{url_name}.png'

	def embed(self, user):
		pkin = get_pokemon_info(self.id)
		owned = get_user_pokedex_entry(user, self)
		desc = ':star:' * self.rarity + '\n'
		desc += f'**PokeCash value** - {rarity_info[self.rarity]["cash"]}\n**Roll refund value** - {rarity_info[self.rarity]["rolls"]}\n'
		desc += f'**HP:** {pkin["hp"]} | **ATK:** {pkin["attack"]} | **DEF:** {pkin["defense"]}\n'
		if owned:
			desc += f'**Owned:** Yes - **{owned.amount}**\n'
			if owned in user._party:
				desc += '**In Party:** Yes\n'
			else:
				desc += '**In Party:** No\n'
		else:
			desc += f'**Owned:** No\n'
		user_badge = get_badge(user, self.id)
		if user_badge:
			desc += f'**Badge:** {user_badge.display.replace(self.name, "")}\n'
		else:
			desc += '**Badge:** N\n'
		r, g, b, _ = get_pkmn_colour(self.icon)
		return Page(f'{int(self.id)} - {self.name}', desc, colour=(r, g, b), icon=self.icon, image=self.url)

	def to_dict(self):
		return {
			'id': self.id,
			'name': self.name,
			'rarity': self.rarity,
			'shiny': self.shiny
		}

	def __eq__(self, p):
		if p == None:
			return False
		try:
			return self.user_id == p.user_id and self.id == p.id
		except AttributeError:
			return self.id == p.id	

	def __bool__(self):
		return self.id > 0

	def __repr__(self):
		return f'Pokemon({self.id}, {self.name})'

	def __str__(self):
		return f'{self.id} - {self.name}'

	def __hash__(self):
		if '.' in str(self.id):
			if str(self.id).split('.')[-1] == '0':
				return int(self.id)
			else:
				return hash(str(self.id))
		# return self.id

class PokedexEntry(Pokemon):
	def __init__(self, user_id, amount, **kwargs):
		super().__init__(**kwargs)
		self.user_id = user_id
		self.amount = amount

	@property
	def to_row(self):
		return (self.user_id, self.id, self.amount, self.shiny)	

	def to_dict(self):
		return {
			'user_id': self.user_id,
			'poke_id': self.id,
			'amount': self.amount,
			'shiny': self.shiny
		}

class PokeBattle(Pokemon):
	def __init__(self, user_id, level, exp, hp, attack, defense, **kwargs):
		super().__init__(**kwargs)
		self.user_id = user_id
		self.level = level
		self.exp = exp
		self.next_lvl_exp = (self.level + 1) ** 3
		self.hp = int((((2 * hp * self.level) // 100) + self.level + 10) // 1)
		self.current_hp = self.hp
		self.attack = int((((2 * attack * self.level) // 100) + 5) // 1)
		self.defense = int((((2 * defense * self.level) // 100) + 5) // 1)
		self.loaded = self.to_dict().copy()

	@property
	def pokebattle_creation_row(self):
		return (
			self.user_id,
			self.id,
			self.level,
			self.exp
		)

	@classmethod
	def from_id(cls, id, level=1):
		pkmn = get_pokemon_by_id(id)
		pkin = get_pokemon_info(pkmn.id)
		return cls(1, level, 0, pkin['hp'], pkin['attack'], pkin['defense'], id=pkmn.id, name=pkmn.name, rarity=pkmn.rarity)

	def embed(self, user):
		pkin = get_pokemon_info(self.id)
		owned = get_user_pokedex_entry(user, self)
		desc = ':star:' * self.rarity + '\n'
		desc += f'**PokeCash value** - {rarity_info[self.rarity]["cash"]}\n**Roll refund value** - {rarity_info[self.rarity]["rolls"]}\n'
		desc += f'At lvl **{self.level}** | **HP:** {self.hp} | **ATK:** {self.attack} | **DEF:** {self.defense}\n'
		if owned:
			desc += f'**Owned:** Yes - **{owned.amount}**\n'
			if owned in user._party:
				desc += '**In Party:** Yes\n'
			else:
				desc += '**In Party:** No\n'
		else:
			desc += f'**Owned:** No\n'
		user_badge = get_badge(user, self.id)
		if user_badge:
			desc += f'**Badge:** {user_badge.display.replace(self.name, "")}\n'
		else:
			desc += '**Badge:** N\n'
		r, g, b, _ = get_pkmn_colour(self.icon)
		return Page(f'{self.id} - {self.name}', desc, colour=(r, g, b), icon=self.icon, image=self.url)

	def add_exp(self, exp):
		if self.level >= 100:
			self.level = 100
			return False
		starting_level = self.level
		while exp > 0 and self.level < 100:
			exp_to_lvl = max(self.next_lvl_exp - self.exp, 0)
			if exp >= exp_to_lvl:
				self.exp += exp_to_lvl
				self.level_up()
				exp -= exp_to_lvl
			else:
				self.exp += exp
				exp = 0
		return self.level > starting_level

	def level_up(self):
		if self.level >= 100:
			return
		self.level += 1
		self.next_lvl_exp = (self.level + 1) ** 3

	def full_health(self):
		self.current_hp = self.hp

	def to_dict(self):
		return {
			'user_id': self.user_id,
			'poke_id': self.id,
			'level': self.level,
			'exp': self.exp
		}

	def update(self):
		current = self.to_dict()
		sql_str = 'update battle set '
		col_val = []
		for k in ['level', 'exp']:
			if current[k] != self.loaded[k]:
				col_val.append((k, current[k]))
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where user_id = ? and poke_id = ?'
		vals = [v for _, v in col_val]
		vals.extend([self.user_id, self.id])
		if not col_val:
			return
		return sql(sql_str, vals)

class Daycare(Pokemon):
	def __init__(self, user_id, enter_time, rewards, **kwargs):
		super().__init__(**kwargs)
		self.user_id = user_id
		self._enter_time = dt.strptime(enter_time, '%Y-%m-%d %H:%M:%S') if isinstance(enter_time, str) else enter_time
		self._rewards = json.loads(rewards) if isinstance(rewards, str) else rewards
		self.loaded = self.to_dict().copy()

	@property
	def enter_time(self):
		return dt.strftime(self._enter_time, '%Y-%m-%d %H:%M:%S')
	
	@property
	def rewards(self):
		return json.dumps(self._rewards)
	
	@property
	def daycare_creation_row(self):
		return (
			self.user_id,
			self.id,
			self.enter_time,
			self.rewards
		)

	def generate_rewards(self, upgrade_level):
		total_seconds = (dt.now() - self._enter_time).total_seconds()
		rewards = total_seconds // (43200 - 3600 * upgrade_level)
		while rewards > self._rewards['rewards']:
			rw = choice([1, 2, 3, 4, 5, 6])
			if rw == 1:
				self._rewards['levels'] += 1
			elif rw == 2:
				self._rewards['cash'] += rarity_info[self.rarity]['cash']
			elif rw == 3:
				self._rewards['rolls'] += rarity_info[self.rarity]['rolls']
			self._rewards['rewards'] += 1
		self.update()

	def embed(self, user):
		desc = 'Welcome to the Daycare!\nTo claim your pokemon use **.daycare claim**\n\n'
		desc += f'**{self.name}** {":star:" * self.rarity}\n\n'
		for reward, value in self._rewards.items():
			if reward == 'rewards':
				pass
			else:
				desc += f'**{reward.capitalize()}:** {value}\n'
		r, g, b, _ = get_pkmn_colour(self.icon)
		return Page(f'{self.id} - {self.name}', desc, colour=(r, g, b), icon=self.icon, image=self.url, footer=f'Rewards rolled: {self._rewards["rewards"]}')

	def to_dict(self):
		return {
			'user_id': self.user_id,
			'poke_id': self.id,
			'enter_time': self.enter_time,
			'rewards': self.rewards
		}

	def update(self):
		current = self.to_dict()
		sql_str = 'update daycare set '
		col_val = []
		if current['rewards'] != self.loaded['rewards']:
			col_val.append(('rewards', current['rewards']))
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where user_id = ? and poke_id = ?'
		vals = [v for _, v in col_val]
		vals.extend([self.user_id, self.id])
		if not col_val:
			return
		return sql(sql_str, vals)

class Badge(Pokemon):
	def __init__(self, user_id, level, amount, **kwargs):
		super().__init__(**kwargs)
		self.user_id = user_id
		self.level = level
		self.amount = amount
		self.loaded = self.to_dict().copy()

	@property
	def display(self):
		if self.level == 1:
			return f':third_place: {self.name}'
		if self.level == 2:
			return f':second_place: {self.name}'
		if self.level == 3:
			return f':first_place: {self.name}'
		return f':military_medal: {self.name} x{self.amount}'

	def to_dict(self):
		return {
			'user_id': self.user_id,
			'poke_id': self.id,
			'level': self.level,
			'amount': self.amount
		}

	def update(self):
		current = self.to_dict()
		sql_str = 'update badges set '
		col_val = []
		for k in ['level', 'amount']:
			if current[k] != self.loaded[k]:
				col_val.append((k, current[k]))
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where user_id = ? and poke_id = ?'
		vals = [v for _, v in col_val]
		vals.extend([self.user_id, self.id])
		if not col_val:
			return
		return sql(sql_str, vals)
