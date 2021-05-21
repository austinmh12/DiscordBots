from .. import sql, log, BASE_PATH, chunk
from . import *
from random import randint, choice

#############
# Constants #
#############
weapon_types = [
	'Sword',
	'Longsword',
	'Claymore',
	'Shortbow',
	'Longbow',
	'Crossbow',
	'Staff',
	'Wand',
	'Dagger',
	'Knife'
]
str_weapons = ['Sword', 'Longsword', 'Claymore']
dex_weapons = ['Shortbow', 'Longbow', 'Crossbow', 'Dagger', 'Knife']
int_weapons = ['Staff', 'Wand']
con_weapons = []
armour_types = [
	'Helmet',
	'Chest',
	'Legs',
	'Boots',
	'Gloves',
	'Vambraces',
	'Coif',
	'Coat',
	'Shield',
	'Quiver',
	'Orb'
]
jewelry_types = [
	'Ring',
	'Amulet'
]
rarity_magic_properties = {
	'Trash': 0,
	'Common': 1,
	'Uncommon': 2,
	'Rare': 3,
	'Legendary': 4,
	'Mythic': 5
}

#############
# Functions #
#############
def get_next_equipment_id():
	df = sql('rpg', 'select id from equipment')
	log.debug(max(df.id))
	return max(df.id) + 1

def get_equipment(id):
	if id is None:
		id = 0
	df = sql('rpg', 'select * from equipment where id = ?', (id,))
	if df.empty:
		return None
	if df['type'][0] in weapon_types:
		return Weapon(**df.to_dict('records')[0])
	elif df['type'][0] in armour_types:
		return Armour(**df.to_dict('records')[0])
	else:
		return Jewelry(**df.to_dict('records')[0])

def add_equipment(equipment):
	sql('rpg', 'insert into equipment values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', equipment.to_row)

def generate_random_equipment(type, rarity, level):
	id = get_next_equipment_id()
	magic_properties = generate_random_magic_properties(rarity, level)
	if type in weapon_types:
		weapon_dict = {}
		weapon_dict['min_damage'] = randint(level, ceil(level * 1.1))
		weapon_dict['max_damage'] = randint(level + ceil(level / 10), int(level * 2))
		weapon_dict['crit_chance'] = randint(0, 5 * rarity_magic_properties[rarity]) / 100
		if type in str_weapons:
			weapon_dict['stat'] = 'STR'
		elif type in dex_weapons:
			weapon_dict['stat'] = 'DEX'
		elif type in int_weapons:
			weapon_dict['stat'] = 'INT'
		else:
			weapon_dict['stat'] = 'CON'
		return Weapon(id, f'{rarity} {type}', rarity, type, level, **magic_properties, **weapon_dict)
	elif type in armour_types:
		armour_dict = {}
		weight = choice(['Heavy', 'Medium', 'Light'])
		armour_dict['weight'] = weight
		if weight == 'Light':
			armour_dict['defense'] = randint(level, ceil(level * 1.2))
		elif weight == 'Medium':
			armour_dict['defense'] = randint(level, ceil(level * 1.35))
		else:
			armour_dict['defense'] = randint(level, ceil(level * 1.5))
		return Armour(id, f'{rarity} {weight} {type}', rarity, type, level, **magic_properties, **armour_dict)
	else:
		return Jewelry(id, f'{rarity} {type}', rarity, type, level, **magic_properties)

def generate_random_magic_properties(rarity, level):
	properties = ['str_bonus', 'dex_bonus', 'int_bonus', 'con_bonus', 'def_bonus', 'atk_bonus']
	generated_properties = {p: 0 for p in properties}
	for _ in range(rarity_magic_properties[rarity]):
		prop = choice(properties)
		val = sum([randint(0, 5) for _ in range(level)])
		generated_properties[prop] += val
	return generated_properties

###########
# Classes #
###########
class Equipment:
	def __init__(self,
				id,
				name,
				rarity,
				type,
				level,
				str_bonus,
				dex_bonus,
				int_bonus,
				con_bonus,
				def_bonus,
				atk_bonus,
				**kwargs
	):
		self.id = id
		self.name = name
		self.rarity = rarity
		self.type = type
		self.level = level
		self.str_bonus = str_bonus
		self.dex_bonus = dex_bonus
		self.int_bonus = int_bonus
		self.con_bonus = con_bonus
		self.def_bonus = def_bonus
		self.atk_bonus = atk_bonus

class Weapon(Equipment):
	def __init__(self, min_damage, max_damage, stat, crit_chance, **kwargs):
		super().__init__(**kwargs)
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.stat = stat
		self.crit_chance = crit_chance

	@property
	def to_row(self):
		return (
			self.id,
			self.name,
			self.rarity,
			self.type,
			self.level,
			self.str_bonus,
			self.dex_bonus,
			self.int_bonus,
			self.con_bonus,
			self.def_bonus,
			self.atk_bonus,
			'',
			0,
			self.min_damage,
			self.max_damage,
			self.stat,
			self.crit_chance
		)

class Armour(Equipment):
	def __init__(self, weight, defense, **kwargs):
		super().__init__(**kwargs)
		self.weight = weight
		self.defense = defense

	@property
	def to_row(self):
		return (
			self.id,
			self.name,
			self.rarity,
			self.type,
			self.level,
			self.str_bonus,
			self.dex_bonus,
			self.int_bonus,
			self.con_bonus,
			self.def_bonus,
			self.atk_bonus,
			self.weight,
			self.defense,
			0,
			0,
			'',
			0
		)

class Jewelry(Equipment):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	@property
	def to_row(self):
		return (
			self.id,
			self.name,
			self.rarity,
			self.type,
			self.level,
			self.str_bonus,
			self.dex_bonus,
			self.int_bonus,
			self.con_bonus,
			self.def_bonus,
			self.atk_bonus,
			'',
			0,
			0,
			0,
			'',
			0
		)