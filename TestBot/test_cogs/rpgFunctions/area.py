from .. import sql, log, BASE_PATH, chunk, Page
from random import randint, random, choice
import json
from .monster import get_monster

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
		...