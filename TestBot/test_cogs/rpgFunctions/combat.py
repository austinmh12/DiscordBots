from .. import sql, log, BASE_PATH, chunk, Page

#############
# Constants #
#############


#############
# Functions #
#############


###########
# Classes #
###########
class Combat:
	def __init__(self, area, enemies, characters):
		self.area = area
		self.enemies = [self.area.get_random_monster() for _ in range(enemies)]
		self.characters = characters

	def do_combat(self):
		...