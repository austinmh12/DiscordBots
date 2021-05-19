from .. import sql, log, BASE_PATH, chunk
from random import randint, random, choice

#############
# Constants #
#############


#############
# Functions #
#############
def get_characters(player_id, player_guild_id):
	...

def get_character(player_id, player_guild_id, name):
	...

def add_character(player_id, player_guild_id, name, profession):
	...

def delete_character(player_id, player_guild_id, name):
	...

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
				exp_to_next_level,
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
				off_hand
	):
		self.player_id = player_id
		self.player_guild_id = player_guild_id
		self.name = name
		self.profession = profession # get_profession(profession)
		self.level = level
		self.exp = exp
		self.exp_to_next_level = exp_to_next_level
		self.gold = gold
		self.helmet = helmet		# get_equipment_by_id(helmet)
		self.chest = chest			# get_equipment_by_id(chest)
		self.legs = legs			# get_equipment_by_id(legs)
		self.boots = boots			# get_equipment_by_id(boots)
		self.gloves = gloves		# get_equipment_by_id(gloves)
		self.amulet = amulet		# get_equipment_by_id(amulet)
		self.ring1 = ring1			# get_equipment_by_id(ring1)
		self.ring2 = ring2			# get_equipment_by_id(ring2)
		self.weapon = weapon		# get_equipment_by_id(weapon)
		self.off_hand = off_hand	# get_equipment_by_id(off_hand)

		# Original cached user
		self.loaded = self.to_dict().copy()

		# Not counted in updates
		self.stats = stats 				# calculate from profession and level
		self.current_con = current_con 	# calculate from profession and level

		# Migrations

	@property
	def to_row(self):
		return (
			self.player_id,
			self.player_guild_id,
			self.name,
			self.profession,
			self.level,
			self.exp,
			self.exp_to_next_level,
			self.gold,
			self.helmet,
			self.chest,
			self.legs,
			self.boots,
			self.gloves,
			self.amulet,
			self.ring1,
			self.ring2,
			self.weapon,
			self.off_hand,
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
			'exp_to_next_level,': self.exp_to_next_level,
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
		sql_str += ' where player_id = ? and player_guild_id = ?'
		vals = [v for _, v in col_val]
		vals.extend([self.player_id, self.player_guild_id])
		if not col_val:
			return
		return sql('rpg', sql_str, vals)