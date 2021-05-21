from .. import sql, log, BASE_PATH, chunk, Page
from . import *
from discord import Embed, Colour

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
	def __init__(self, character):
		self.character = character
		self.enemy = self.character.current_area.get_random_monster()
		self.desc = f'**{self.character.name}** v. **{self.enemy.name}** (Lvl {self.enemy.level})\n{self.character.name}\'s turn first'
		self.winner = None

	def alive(self, entity):
		return entity.current_con > 0

	def character_combat(self, action):
		if action == 'Attack':
			char_dmg = self.character.damage
			dmg_done = floor(char_dmg * self.enemy.defense)
			self.enemy.current_con -= dmg_done
			self.desc = f'**{self.character.name}** did {dmg_done} to the **{self.enemy.name}**!'
		elif action == 'Pass':
			self.desc = f'**{self.character.name}** passed.'
		if self.alive(self.enemy):
			self.enemy_combat()
		else:
			self.desc += f'\n**{self.enemy.name}** has died!'
			self.winner = self.character

	def enemy_combat(self):
		enemy_dmg = self.enemy.damage
		dmg_done = floor(enemy_dmg * self.character.defense)
		self.character.current_con -= dmg_done
		self.desc += f'\n**{self.enemy.name}** did {dmg_done} to the **{self.character.name}**!'
		if self.alive(self.character):
			return
		else:
			self.desc += f'\n**{self.character.name}** has died!'
			self.winner = self.enemy

	@property
	def embed(self):
		emb = Embed(
			title='Combat',
			description=self.desc,
			colour=Colour.from_rbg(150, 150, 150)
		)
		emb.add_field(name=self.character.name, value=f'HP: {self.character.current_con}', inline=True)
		emb.add_field(name=f'{self.enemy.name} (Lvl {self.enemy.level})', value=f'HP: {self.enemy.current_con}', inline=True)
		return emb