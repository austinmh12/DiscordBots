from .. import sql, log, BASE_PATH, chunk

#############
# Constants #
#############


#############
# Functions #
#############
def get_equipment(id):
	df = sql('rpg', 'select * from equipment where id = ?', (id,))
	if df.empty:
		return None
	if df['min_damage'] > 0:
		return Weapon(**df.to_dict('records')[0])
	elif df['defense'] > 0:
		return Armour(**df.to_dict('records')[0])
	else:
		return Jewelry(**df.to_dict('records')[0])

def add_equipment(equipment):
	...

###########
# Classes #
###########
class Equipment:
	def __init__(self,
				id,
				name,
				rarity,
				type,
				level,
				str_bonus,
				dex_bonus,
				int_bonus,
				con_bonus,
				def_bonus,
				atk_bonus,
				**kwargs
	):
		self.id = id
		self.name = name
		self.rarity = rarity
		self.type = type
		self.level = level
		self.str_bonus = str_bonus
		self.dex_bonus = dex_bonus
		self.int_bonus = int_bonus
		self.con_bonus = con_bonus
		self.def_bonus = def_bonus
		self.atk_bonus = atk_bonus

class Weapon(Equipment):
	def __init__(self, min_damage, max_damage, stat, crit_chance, **kwargs):
		super().__init__(**kwargs)
		self.min_damage = min_damage
		self.max_damage = max_damage
		self.stat = stat
		self.crit_chance = crit_chance

class Armour(Equipment):
	def __init__(self, weight, defense, **kwargs):
		super().__init__(**kwargs)
		self.weight = weight
		self.defense = defense

class Jewelry(Equipment):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)