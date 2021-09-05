from .. import sql, log, BASE_PATH, chunk, Page
from . import *
from random import randint, choice

#############
# Constants #
#############
## Weapon Info
simple_weapons = ['Sword', 'Shortbow', 'Dagger', 'Wand']
advanced_weapons = ['Longsword', 'Longbow', 'Knife', 'Staff']
complex_weapons = ['Claymore', 'Crossbow', 'Whip', 'Grimoire']
all_weapons = [*simple_weapons, *advanced_weapons, *complex_weapons]

str_weapons = ['Sword', 'Longsword', 'Claymore']
dex_weapons = ['Shortbow', 'Longbow', 'Crossbow', 'Dagger', 'Knife', 'Whip']
int_weapons = ['Staff', 'Wand', 'Grimoire']
con_weapons = []

dual_wield_weapons = ['Sword', 'Dagger', 'Knife', 'Crossbow']
two_handed_weapons = ['Claymore', 'Shortbow', 'Longbow', 'Staff', 'Whip']

## Armour Info
basic_armour = ['Helmet', 'Chest', 'Gloves', 'Legs', 'Boots']
off_hands = ['Shield', 'Orb', 'Quiver']
all_armour = [*basic_armour, *off_hands]

ignores_two_handed = ['Orb', 'Quiver']

## Jewelry Info
jewelry = ['Ring', 'Amulet']


## Rarity Info
rarity_magic_properties = {
	'Trash': 0,
	'Common': 1,
	'Uncommon': 2,
	'Rare': 3,
	'Legendary': 4,
	'Mythic': 5
}
rarity_price_bonus = {
	'Trash': 1,
	'Common': 5,
	'Uncommon': 20,
	'Rare': 100,
	'Legendary': 250,
	'Mythic': 1000
}
rarity_colour = {
	'Trash': (100, 100, 100),
	'Common': (235, 235, 235),
	'Uncommon': (0, 189, 57),
	'Rare': (0, 92, 179),
	'Legendary': (254, 238, 0),
	'Mythic': (151, 0, 166)
}

## Icons
up_indicator = '<:good_icon:846539230901829702>'
down_indicator = '<:bad_icon:846539241353773056>'

#############
# Functions #
#############
def get_next_equipment_id():
	df = sql('rpg', 'select id from equipment')
	return max(df.id) + 1

def get_equipment(id):
	if id is None:
		id = 0
	df = sql('rpg', 'select * from equipment where id = ?', (id,))
	if df.empty:
		return None
	if df['type'][0] in all_weapons:
		return Weapon(**df.to_dict('records')[0])
	elif df['type'][0] in all_armour:
		return Armour(**df.to_dict('records')[0])
	else:
		return Jewelry(**df.to_dict('records')[0])

def add_equipment(equipment):
	sql('rpg', 'insert into equipment values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', equipment.to_row)

def delete_equipment(equipment):
	if equipment.id <= 11:
		return
	sql('rpg', 'delete from equipment where id = ?', (equipment.id,))

def generate_random_equipment(type, rarity, level):
	id = get_next_equipment_id()
	if type in all_weapons:
		equip = generate_weapon(id, type, rarity, level)
	elif type in all_armour:
		equip = generate_armour(id, type, rarity, level)
	else:
		equip = generate_jewelry(id, type, rarity, level)
	add_equipment(equip)
	return equip

def generate_weapon(id, type, rarity, level):
	magic_properties = generate_random_magic_properties(type, rarity, level)
	name = generate_name(type, rarity, magic_properties)
	if type in simple_weapons:
		min_dmg = randint(level, ceil(level * 1.1))
		max_dmg = randint(ceil(level * 1.1), int(ceil(level * 1.1) * 2))
		crit_chance = randint(0, 5 * rarity_magic_properties[rarity]) / 100
		if type in dex_weapons:
			crit_chance *= 1.5
	elif type in advanced_weapons:
		min_dmg = randint(level, ceil(level * 1.25))
		max_dmg = randint(ceil(level * 1.25), int(ceil(level * 1.25) * 2))
		crit_chance = randint(0, 5 * rarity_magic_properties[rarity]) / 100
		if type in dex_weapons:
			crit_chance *= 1.8
	else:
		min_dmg = randint(level, ceil(level * 1.5))
		max_dmg = randint(ceil(level * 1.5), int(ceil(level * 1.5) * 2))
		crit_chance = randint(0, 5 * rarity_magic_properties[rarity]) / 100
		if type in dex_weapons:
			crit_chance *= 2.25
	if type in str_weapons:
		stat = 'STR'
	elif type in dex_weapons:
		stat = 'DEX'
	elif type in int_weapons:
		stat = 'INT'
	else:
		stat = 'CON'
	return Weapon(
		id=id, 
		name=name, 
		rarity=rarity, 
		type=type, 
		level=level, 
		min_damage=min_dmg, 
		max_damage=max_dmg, 
		crit_chance=crit_chance,
		stat=stat, 
		**magic_properties
	)

def generate_armour(id, type, rarity, level):
	magic_properties = generate_random_magic_properties(type, rarity, level)
	weight = choice(['Heavy', 'Medium', 'Light'])
	name = generate_name(type, rarity, magic_properties, weight)
	if weight == 'Light':
		defense = randint(level, ceil(level * 1.2))
	elif weight == 'Medium':
		defense = randint(level, ceil(level * 1.35))
	else:
		defense = randint(level, ceil(level * 1.5))
	return Armour(
		id=id,
		name=name,
		rarity=rarity,
		type=type,
		level=level,
		weight=weight,
		defense=defense,
		**magic_properties
	)

def generate_jewelry(id, type, rarity, level):
	magic_properties = generate_random_magic_properties(type, rarity, level)
	name = generate_name(type, rarity, magic_properties)
	return Jewelry(
		id=id,
		name=name,
		rarity=rarity,
		type=type,
		level=level,
		**magic_properties
	)

def generate_name(type, rarity, magic_properties, weight=''):
	highest_bonus, _ = max([(k, v) for k,v in magic_properties.items()], key=lambda x: x[1])
	if highest_bonus == 'str_bonus' and magic_properties[highest_bonus] != 0:
		suffix = ' of the Lion'
	elif highest_bonus == 'dex_bonus' and magic_properties[highest_bonus] != 0:
		suffix = ' of the Hawk'
	elif highest_bonus == 'int_bonus' and magic_properties[highest_bonus] != 0:
		suffix = ' of the Scholar'
	elif highest_bonus == 'con_bonus' and magic_properties[highest_bonus] != 0:
		suffix = ' of the Bear'
	else:
		suffix = ''
	if magic_properties['def_bonus'] > magic_properties['atk_bonus']:
		prefix = 'Valiant '
	elif magic_properties['def_bonus'] < magic_properties['atk_bonus']:
		prefix = 'Brutal '
	else:
		prefix = ''
	return f'{rarity} {prefix}{weight + " " if weight else ""}{type}{suffix}'

def generate_random_magic_properties(type, rarity, level):
	properties = ['str_bonus', 'dex_bonus', 'int_bonus', 'con_bonus', 'def_bonus', 'atk_bonus']
	bonuses = ['con_bonus', 'def_bonus', 'atk_bonus']
	if type in str_weapons:
		bonuses.append('str_bonus')
	if type in dex_weapons:
		bonuses.append('dex_bonus')
	if type in int_weapons:
		bonuses.append('int_bonus')
	if type in all_armour or type in jewelry:
		bonuses = properties
	generated_properties = {p: 0 for p in properties}
	for _ in range(rarity_magic_properties[rarity]):
		prop = choice(bonuses)
		val = level
		generated_properties[prop] += val
	return generated_properties

###########
# Classes #
###########
# TODO: Convert this to an ABC
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

	def stat_indicator(self, eq, char):
		if char < eq:
			return up_indicator
		elif char > eq:
			return down_indicator
		else:
			return ':heavy_minus_sign:'

	def bonuses_details(self, equipment):
		if not equipment:
			equipment = Equipment(0, '', '', '', 0, 0, 0, 0, 0, 0, 0)
		desc = f'**STR:** {self.str_bonus} {self.stat_indicator(self.str_bonus, equipment.str_bonus)} | **DEX:** {self.dex_bonus} {self.stat_indicator(self.dex_bonus, equipment.dex_bonus)}\n'
		desc += f'**INT:** {self.int_bonus} {self.stat_indicator(self.int_bonus, equipment.int_bonus)} | **CON:** {self.con_bonus} {self.stat_indicator(self.con_bonus, equipment.con_bonus)}\n'
		desc += f'**ATK:** {self.atk_bonus} {self.stat_indicator(self.atk_bonus, equipment.atk_bonus)} | **DEF:** {self.def_bonus} {self.stat_indicator(self.def_bonus, equipment.def_bonus)}\n\n'
		return desc

	def __eq__(self, e):
		if e is None:
			return False
		return self.id == e.id

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

	@property
	def price(self):
		return floor(self.equipment_rating + rarity_price_bonus[self.rarity] * self.level)

	@property
	def avg_dmg(self):
		return (self.min_damage + self.max_damage) / 2

	@property
	def equipment_rating(self):
		return (1 - self.crit_chance) * self.avg_dmg + self.crit_chance * 1.5 * self.avg_dmg

	def equipment_rating_with_character_stats(self, character):
		average_damage = self.avg_dmg + floor(character.stats[self.stat] / 10)
		return (1 - self.crit_chance) * average_damage + self.crit_chance * 1.5 * average_damage

	def compare_weapons(self, character):
		if not character.weapon:
			return ''
		rating = 1 - (character.weapon.equipment_rating_with_character_stats(character) / self.equipment_rating_with_character_stats(character))
		if rating < -.5:
			return down_indicator * 3
		elif -.5 <= rating < -.35:
			return down_indicator * 2
		elif -.35 <= rating < -.1:
			return down_indicator
		elif -.1 <= rating < .1:
			return ''
		elif .1 <= rating < .35:
			return up_indicator
		elif .35 <= rating < .5:
			return up_indicator * 2
		else:
			return up_indicator * 3

	def stat_page(self, character):
		desc = f'**DPS:** {round(self.equipment_rating, 2)} {self.compare_weapons(character)}\n\n'
		desc += f'**Damage:** {self.min_damage} - {self.max_damage}\n'
		desc += f'**Crit Chance:** {round(self.crit_chance, 2)}\n'
		desc += f'**Main Stat:** {self.stat}\n\n'
		desc += self.bonuses_details(character.weapon)
		desc += f'**Sell Price:** {self.price} :coin:'
		return Page(self.name, desc, colour=rarity_colour[self.rarity])

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

	@property
	def price(self):
		return floor(self.level * rarity_price_bonus[self.rarity] * (1 + self.equipment_rating))

	@property
	def equipment_rating(self):
		return 80 / (80 + self.defense)

	def equipment_rating_with_character_stats(self, character):
		return 80 / (80 + self.defense + character.stats['STR'])

	def get_character_equipment(self, character):
		if self.type == 'Helmet':
			return character.helmet
		elif self.type == 'Chest':
			return character.chest
		elif self.type == 'Legs':
			return character.legs
		elif self.type == 'Boots':
			return character.boots
		elif self.type == 'Gloves':
			return character.gloves
		else:
			return character.off_hand

	def compare_armour(self, character):
		if self.weight != character.profession.weight:
			return ':x:'
		equipment = self.get_character_equipment(character)
		if not equipment:
			return up_indicator * 3
		rating = 1 - (equipment.equipment_rating_with_character_stats(character) / self.equipment_rating_with_character_stats(character))
		if rating < -.5:
			return down_indicator * 3
		elif -.5 <= rating < -.35:
			return down_indicator * 2
		elif -.35 <= rating < -.1:
			return down_indicator
		elif -.1 <= rating < .1:
			return ''
		elif .1 <= rating < .35:
			return up_indicator
		elif .35 <= rating < .5:
			return up_indicator * 2
		else:
			return up_indicator * 3

	def stat_page(self, character):
		eq = self.get_character_equipment(character)
		desc = f'**Defense:** {self.defense} {self.compare_armour(character)}\n'
		desc += f'**Weight:** {self.weight}\n\n'
		desc += self.bonuses_details(eq)
		desc += f'**Sell Price:** {self.price} :coin:'
		return Page(self.name, desc, colour=rarity_colour[self.rarity])

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

	@property
	def price(self):
		return floor(self.level * rarity_price_bonus[self.rarity])

	def get_character_equipment(self, character):
		if self.type == 'Ring':
			return character.ring
		else:
			return character.amulet

	def stat_page(self, character):
		eq = self.get_character_equipment(character)
		desc = self.bonuses_details(eq)
		desc += f'**Sell Price:** {self.price} :coin:'
		return Page(self.name, desc, colour=rarity_colour[self.rarity])