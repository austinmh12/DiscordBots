from .. import sql, log, BASE_PATH, chunk, Page
from . import *
from discord import Embed, Colour
from random import randint, random

#############
# Constants #
#############


#############
# Functions #
#############
def get_spells():
	df = sql('rpg', 'select * from spells')
	if df.empty:
		return []
	return [Spell(**d) for d in df.to_dict('records')]

def get_spells_by_profession(profession):
	df = sql('rpg', 'select * from spells where profession = ?', (profession.name,))
	if df.empty:
		return []
	return [Spell(**d) for d in df.to_dict('records')]

def get_spell(name):
	df = sql('rpg', 'select * from spells where lower(name) = ?', (name.lower(),))
	if df.empty:
		return None
	return Spell(**df.to_dict('records')[0])

###########
# Classes #
###########
class Spell:
	def __init__(self, name, profession, level, min_damage, max_damage, stat, cost):
		self.name = name
		self.profession = profession
		self.level = level
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.stat = stat
		self.cost = cost

	@property
	def avg_dmg(self):
		return (self.min_damage + self.max_damage) / 2

	def avg_dmg_with_character_stats(self, character):
		dmg = (self.min_damage + (floor(character.armour_attack / 5) * 2) + self.max_damage + (floor(character.stats['INT'] / 5) * 2)) / 2
		dmg += floor(character.stats[self.stat] / 5)
		dmg += floor(character.stats.get(character.profession.primary_stat, 0) / 10)
		return round(dmg, 2)

	def stat_page(self, character):
		desc = f'**DPS:** {self.avg_dmg_with_character_stats(character)}\n\n'
		desc += f'**Damage:** {self.min_damage} - {self.max_damage}\n'
		desc += f'**Costs:** {self.cost}\n'
		desc += f'**Main Stat:** {self.stat}\n\n'
		return Page(self.name, desc, colour=(22, 0, 240))

	def __eq__(self, s):
		return self.name == s.name and self.profession == s.profession