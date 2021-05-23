from .. import sql, log, BASE_PATH, chunk, Page
from random import randint, random, choice
import json
from .monster import get_monster
from .equipment import generate_random_equipment

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
	df = sql('rpg', 'select * from areas where name = ?', (name,))
	if df.empty:
		return None
	return Area(**df.to_dict('records')[0])

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
		for _ in range(self.loot_table['max_item_count']):
			if random() < self.loot_table['item_chance']:
				item_type = choice(list(self.loot_table['items'].keys()))
				item_info = self.loot_table['items'][item_type]
				rarity = choice(item_info['rarities'])
				level = randint(item_info['min_level'], item_info['max_level'])
				item = generate_random_equipment(item_type, rarity, level)
				items.append(item)
				log.debug(f'{item.id} {item.name} {item.level} {item.rarity}')
		ret['items'] = items
		return ret

	@property
	def page(self):
		desc = f'**Recommended Level:** {self.recommended_level}\n\n'
		desc += '__**Monsters**__\n'
		for m, m_inf in self.monsters.items():
			desc += f'{m} ({m_inf["min_level"]} - {m_inf["max_level"]})\n'
		desc += '\n__**Items**__\n'
		for i, i_inf in self.loot_table['items'].items():
			desc += f'{i.capitalize()} ({i_inf["min_level"]} - {i_inf["max_level"]})\n'
		return Page(self.name, desc, colour=(150, 150, 150))
	