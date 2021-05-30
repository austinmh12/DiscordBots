from .. import sql, log, BASE_PATH, chunk, Page
from random import randint, random, choice
import json
from .monster import get_monster
from .equipment import (Equipment, generate_random_equipment, simple_weapons, advanced_weapons, complex_weapons,
	all_weapons, basic_armour, off_hands, all_armour, jewelry)
from .consumable import Consumable, generate_consumable, potions

#############
# Constants #
#############


#############
# Functions #
#############
def get_areas():
	df = sql('rpg', 'select * from areas')
	if df.empty:
		return []
	return [Area(**d) for d in df.to_dict('records')]

def get_area(name):
	df = sql('rpg', 'select * from areas where lower(name) = ?', (name.lower(),))
	if df.empty:
		return None
	return Area(**df.to_dict('records')[0])

def get_item(item_info):
	if item_info['type'] == 'Simple Weapon':
		type = choice(simple_weapons)
	elif item_info['type'] == 'Advanced Weapon':
		type = choice(advanced_weapons)
	elif item_info['type'] == 'Complex Weapon':
		type = choice(complex_weapons)
	elif item_info['type'] == 'All Weapons':
		type = choice(all_weapons)
	elif item_info['type'] == 'Basic Armour':
		type = choice(basic_armour)
	elif item_info['type'] == 'Off Hand':
		type = choice(off_hands)
	elif item_info['type'] == 'All Armour':
		type = choice(all_armour)
	elif item_info['type'] == 'Jewelry':
		type = choice(jewelry)
	elif item_info['type'] == 'Restoration':
		type = choice(potions)
	else:
		type = item_info['type']
	level = randint(item_info['min_level'], item_info['max_level'])
	if type in potions:
		return generate_consumable(type, level)
	rarity = choice(item_info['rarities'])
	return generate_random_equipment(type, rarity, level)

###########
# Classes #
###########
class Area:
	def __init__(self, name, recommended_level, monsters, loot_table):
		self.name = name
		self.recommended_level = recommended_level
		self.monsters = json.loads(monsters)
		self.loot_table = json.loads(loot_table)

	def get_random_monster(self):
		rand_monster = choice(list(self.monsters.keys()))
		monster = get_monster(rand_monster)
		monster.generate_stats(randint(self.monsters[rand_monster]['min_level'], self.monsters[rand_monster]['max_level']))
		return monster

	def get_random_loot(self):
		ret = {}
		ret['gold'] = randint(1, self.loot_table['gold'])
		items = []
		for _ in range(self.loot_table['100%']['drops']):
			item_info = choice(list(self.loot_table['100%']['items']))
			items.append(get_item(item_info))
		for _ in range(self.loot_table['main']['drops']):
			if random() < self.loot_table['main']['chance']:
				item_info = choice(list(self.loot_table['main']['items']))
				items.append(get_item(item_info))
		for _ in range(self.loot_table['secondary']['drops']):
			if random() < self.loot_table['secondary']['chance']:
				item_info = choice(list(self.loot_table['secondary']['items']))
				items.append(get_item(item_info))
		ret['equipment'] = [i for i in items if isinstance(i, Equipment)]
		ret['consumables'] = [i for i in items if isinstance(i, Consumable)]
		return ret

	@property
	def page(self):
		desc = f'**Recommended Level:** {self.recommended_level}\n\n'
		desc += '__**Monsters**__\n'
		for m, m_inf in self.monsters.items():
			desc += f'{m} ({m_inf["min_level"]} - {m_inf["max_level"]})\n'
		return Page(self.name, desc, colour=(150, 150, 150))