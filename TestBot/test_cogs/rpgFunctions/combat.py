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


###########
# Classes #
###########
class Combat:
	def __init__(self, character):
		self.character = character
		self.area = self.character.current_area
		self.enemy = self.area.get_random_monster()
		self.desc = f'**{self.character.name}** v. **{self.enemy.name}** (Lvl {self.enemy.level})\n{self.character.name}\'s turn first'
		self.winner = None
		self.colour = (150, 150, 150)

	def alive(self, entity):
		return entity.current_con > 0

	def character_combat(self, action):
		if action == 'Attack':
			enemy_dodge_chance = self.enemy.stats['DEX'] / (self.character.stats['DEX'] * 100)
			if random() <= enemy_dodge_chance:
				self.desc = f'**{self.enemy.name}** dodged your attack!'
			else:
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
			self.exp = self.enemy.base_exp + (self.enemy.level * self.enemy.exp_mod)
			self.loot = self.area.get_random_loot()
			self.desc += f'\nYou gained {self.exp} EXP and {self.loot["gold"]} gold.'
			if self.loot['items']:
				self.desc += '\nYou also got:\n'
				self.desc += '\n'.join([f'{i.name}' for i in self.loot['items']])
			self.winner = self.character
			self.colour = (0, 196, 18)

	def enemy_combat(self):
		char_dodge_chance = self.character.stats['DEX'] / (self.enemy.stats['DEX'] * 100)
		if random() <= char_dodge_chance:
			self.desc += f'\n**{self.character.name}** dodged the attack!'
		else:
			if self.character.off_hand and self.character.off_hand.type == 'Shield':
				blocked = random() <= .15
			else:
				blocked = False
			if blocked:
				self.desc += f'\n**{self.character.name}** blocked the attack!'
			else:
				enemy_dmg = self.enemy.damage
				dmg_done = floor(enemy_dmg * self.character.defense)
				self.character.current_con -= dmg_done
				self.desc += f'\n**{self.enemy.name}** did {dmg_done} to the **{self.character.name}**!'
		if self.alive(self.character):
			return
		else:
			self.desc += f'\n**{self.character.name}** has died!'
			self.winner = self.enemy
			self.colour = (222, 0, 0)

	@property
	def embed(self):
		emb = Embed(
			title='Combat',
			description=self.desc,
			colour=Colour.from_rgb(*self.colour)
		)
		emb.add_field(name=self.character.name, value=f'HP: {self.character.current_con}', inline=True)
		emb.add_field(name=f'{self.enemy.name} (Lvl {self.enemy.level})', value=f'HP: {self.enemy.current_con}', inline=True)
		return emb