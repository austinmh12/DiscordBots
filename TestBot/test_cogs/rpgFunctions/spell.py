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