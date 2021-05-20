from .. import sql, log, BASE_PATH, chunk, Page
from random import randint, random, choice
from . import *
from .equipment import Equipment, get_equipment
from .profession import Profession, get_profession

#############
# Constants #
#############


#############
# Functions #
#############
def get_characters(player):
	df = sql('rpg', 'select * from characters where player_id = ? and player_guild_id = ?', (player.id, player.guild_id))
	if df.empty:
		return []
	return [Character(**d) for d in df.to_dict('records')]

def get_character(player, name):
	df = sql('rpg', 'select * from characters where player_id = ? and player_guild_id = ? and name = ?', (player.id, player.guild_id, name))
	if df.empty:
		return None
	return Character(**df.to_dict('records')[0])

def add_character(character):
	sql('rpg', 'insert into characters values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', character.to_row)

def delete_character(player, name):
	sql('rpg', 'delete from characters where player_id = ? and player_guild_id = ? and name = ?', (player.id, player.guild_id, name))

###########
# Classes #
###########
class Character:
	def __init__(self, 
				player_id,
				player_guild_id,
				name,
				profession,
				level,
				exp,
				gold,
				helmet,
				chest,
				legs,
				boots,
				gloves,
				amulet,
				ring1,
				ring2,
				weapon,
				off_hand,
				current_con = 0
	):
		self.player_id = player_id
		self.player_guild_id = player_guild_id
		self.name = name
		self.profession = profession if isinstance(profession, Profession) else get_profession(profession)
		self.level = level
		self.exp = exp
		self.get_next_level_exp()
		self.gold = gold
		self.helmet = helmet if isinstance(helmet, Equipment) else get_equipment(helmet)
		self.chest = chest if isinstance(chest, Equipment) else get_equipment(chest)
		self.legs = legs if isinstance(legs, Equipment) else get_equipment(legs)
		self.boots = boots if isinstance(boots, Equipment) else get_equipment(boots)
		self.gloves = gloves if isinstance(gloves, Equipment) else get_equipment(gloves)
		self.amulet = amulet if isinstance(amulet, Equipment) else get_equipment(amulet)
		self.ring1 = ring1 if isinstance(ring1, Equipment) else get_equipment(ring1)
		self.ring2 = ring2 if isinstance(ring2, Equipment) else get_equipment(ring2)
		self.weapon = weapon if isinstance(weapon, Equipment) else get_equipment(weapon)
		self.off_hand = off_hand if isinstance(off_hand, Equipment) else get_equipment(off_hand)
		self.calculate_stats()
		self.current_con = self.stats['CON'] if not current_con else current_con

		# Original cached user
		self.loaded = self.to_dict().copy()

		# Migrations

	@property
	def to_row(self):
		return (
			self.player_id,
			self.player_guild_id,
			self.name,
			self.profession.name,
			self.level,
			self.exp,
			self.gold,
			self.helmet.id if self.helmet else 0,
			self.chest.id if self.chest else 0,
			self.legs.id if self.legs else 0,
			self.boots.id if self.boots else 0,
			self.gloves.id if self.gloves else 0,
			self.amulet.id if self.amulet else 0,
			self.ring1.id if self.ring1 else 0,
			self.ring2.id if self.ring2 else 0,
			self.weapon.id if self.weapon else 0,
			self.off_hand.id if self.off_hand else 0,
			self.current_con
		)

	def to_dict(self):
		return {
			'player_id,': self.player_id,
			'player_guild_id,': self.player_guild_id,
			'name,': self.name,
			'profession,': self.profession,
			'level,': self.level,
			'exp,': self.exp,
			'gold,': self.gold,
			'helmet,': self.helmet,
			'chest,': self.chest,
			'legs,': self.legs,
			'boots,': self.boots,
			'gloves,': self.gloves,
			'amulet,': self.amulet,
			'ring1,': self.ring1,
			'ring2,': self.ring2,
			'weapon,': self.weapon,
			'off_hand,': self.off_hand,
			'current_con': self.current_con
		}
	
	def update(self):
		current = self.to_dict()
		sql_str = 'update characters set '
		col_val = []
		for k in current.keys():
			if current[k] != self.loaded[k]:
				col_val.append((k, current[k]))
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where player_id = ? and player_guild_id = ? and name = ?'
		vals = [v for _, v in col_val]
		vals.extend([self.player_id, self.player_guild_id, self.name])
		if not col_val:
			return
		return sql('rpg', sql_str, vals)

	def get_next_level_exp(self):

		def exp_to_level(level):
			return int(round(.25 * floor((level - 1) + 300 * (2 ** ((level - 1) / 7))), 0))

		self.exp_to_next_level = sum([exp_to_level(i) for i in range(2, self.level + 2)])

	def calculate_stats(self):
		s = self.profession.base_str + (self.level * self.profession.str_mod)
		d = self.profession.base_dex + (self.level * self.profession.dex_mod)
		i = self.profession.base_int + (self.level * self.profession.int_mod)
		c = self.profession.base_con + (self.level * self.profession.con_mod)
		self.stats = {'STR': s, 'DEX': d, 'INT': i, 'CON': c}

	@property
	def pages(self):
		# Character Overview
		splash_desc = f'**Level:** {self.level} | **EXP:** {self.exp} ({self.exp_to_next_level})\n'
		splash_desc += f'**Gold:** {self.gold}\n'
		if self.helmet:
			splash_desc += f'**Helmet:** {self.helmet.name}\n'
		else:
			splash_desc += '**Helmet:** \n'
		if self.chest:
			splash_desc += f'**Chest:** {self.chest.name}\n'
		else:
			splash_desc += '**Chest:** \n'
		if self.legs:
			splash_desc += f'**Legs:** {self.legs.name}\n'
		else:
			splash_desc += '**Legs:** \n'
		if self.boots:
			splash_desc += f'**Boots:** {self.boots.name}\n'
		else:
			splash_desc += '**Boots:** \n'
		if self.gloves:
			splash_desc += f'**Gloves:** {self.gloves.name}\n'
		else:
			splash_desc += '**Gloves:** \n'
		if self.amulet:
			splash_desc += f'**Amulet:** {self.amulet.name}\n'
		else:
			splash_desc += '**Amulet:** \n'
		if self.ring1:
			splash_desc += f'**Ring1:** {self.ring1.name}\n'
		else:
			splash_desc += '**Ring1:** \n'
		if self.ring2:
			splash_desc += f'**Ring2:** {self.ring2.name}\n'
		else:
			splash_desc += '**Ring2:** \n'
		if self.weapon:
			splash_desc += f'**Weapon:** {self.weapon.name}\n'
		else:
			splash_desc += '**Weapon:** \n'
		if self.off_hand:
			splash_desc += f'**Off Hand:** {self.off_hand.name}\n'
		else:
			splash_desc += '**Off Hand:**'
		splash_page = Page(f'{self.name} - {self.profession.name}', splash_desc, colour=(150, 150, 150))

		# Stats page

		# Equipment details

		return [splash_page]