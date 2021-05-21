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
	...

def get_area(name):
	...

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
		...

	def get_random_loot(self):
		...