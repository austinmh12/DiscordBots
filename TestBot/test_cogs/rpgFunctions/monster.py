from .. import sql, log, BASE_PATH, chunk, Page
from random import randint, random, choice
from . import *

#############
# Constants #
#############


#############
# Functions #
#############
def get_monsters():
	df = sql('rpg', 'select * from monsters')
	if df.empty:
		return []
	return [Monster(**d) for d in df.to_dict('records')]

def get_monster(name):
	df = sql('rpg', 'select * from monsters where name = ?', (name,))
	if df.empty:
		return None
	return Monster(**df.to_dict('records')[0])

# TODO: Add add_monster function for admin

###########
# Classes #
###########
class Monster:
	def __init__(self, 
				name,
				primary_stat,
				secondary_stat,
				min_damage,
				max_damage,
				crit_chance,
				base_str,
				base_dex,
				base_int,
				base_con,
				str_mod,
				dex_mod,
				int_mod,
				con_mod,
				base_exp,
				exp_mod
	):
		self.name = name
		self.primary_stat = primary_stat
		self.secondary_stat = secondary_stat
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.crit_chance = crit_chance
		self.base_str = base_str
		self.base_dex = base_dex
		self.base_int = base_int
		self.base_con = base_con
		self.str_mod = str_mod
		self.dex_mod = dex_mod
		self.int_mod = int_mod
		self.con_mod = con_mod
		self.base_exp = base_exp
		self.exp_mod = exp_mod

	def generate_stats(self, level):
		s = self.base_str + (level * self.str_mod)
		d = self.base_dex + (level * self.dex_mod)
		i = self.base_int + (level * self.int_mod)
		c = self.base_con + (level * self.con_mod)
		self.stats = {'STR': s, 'DEX': d, 'INT': i, 'CON': c}
		self.current_con = c * 10
		self.level = level

	@property
	def defense(self):
		return 80 / (80 + self.stats['STR'])
	
	@property
	def damage(self):
		dmg = randint(self.level, floor(self.level * 1.25))
		dmg += floor(self.stats.get(self.primary_stat, 0) / 10)
		dmg += floor(self.stats.get(self.secondary_stat, 0) / 20)
		if random() < self.crit_chance:
			dmg *= 1.5
		return dmg