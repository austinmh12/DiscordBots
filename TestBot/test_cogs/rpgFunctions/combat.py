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
	def __init__(self, area, character):
		self.area = area
		self.character = character
		self.enemy = self.area.get_random_monster()
		self.winner = None

	def alive(self, entity):
		return entity.current_con > 0

	def character_combat(self, action):
		if action == 'Attack':
			...
		elif action == 'Pass':
			...
		if self.alive(self.enemy):
			self.enemy_combat()
		else:
			self.winner = self.character

	def enemy_combat(self):
		...