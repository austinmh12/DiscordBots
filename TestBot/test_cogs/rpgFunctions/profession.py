from .. import sql, log, BASE_PATH, chunk, Page
from .equipment import Equipment, get_equipment

#############
# Constants #
#############
all_professions = [
	'warrior',
	'wizard',
	'archer',
	'rogue'
]
light_professions = ['Archer', 'Wizard']
medium_professions = ['Rogue']
heavy_professions = ['Warrior']

#############
# Functions #
#############
def get_professions():
	df = sql('rpg', 'select * from professions')
	return [Profession(**d) for d in df.to_dict('records')]

def get_profession(name):
	df = sql('rpg', 'select * from professions where lower(name) = ?', (name.lower(),))
	if df.empty:
		return None
	return Profession(**df.to_dict('records')[0])

###########
# Classes #
###########
class Profession:
	def __init__(self,
				name,
				primary_stat,
				secondary_stat,
				base_str,
				base_dex,
				base_int,
				base_con,
				str_mod,
				dex_mod,
				int_mod,
				con_mod,
				starting_weapon,
				starting_off_hand,
				weight
	):
		self.name = name
		self.primary_stat = primary_stat
		self.secondary_stat = secondary_stat
		self.base_str = base_str
		self.base_dex = base_dex
		self.base_int = base_int
		self.base_con = base_con
		self.str_mod = str_mod
		self.dex_mod = dex_mod
		self.int_mod = int_mod
		self.con_mod = con_mod
		self.starting_weapon = starting_weapon if isinstance(starting_weapon, Equipment) else get_equipment(starting_weapon)
		self.starting_off_hand = starting_off_hand if isinstance(starting_off_hand, Equipment) else get_equipment(starting_off_hand)
		self.weight = weight

	@property
	def page(self):
		desc = f'**Primary Stat:** {self.primary_stat}\n'
		desc += f'**Secondary Stat:** {self.secondary_stat}\n'
		desc += f'**STR:** {self.base_str:02d} | **DEX:** {self.base_dex:02d}\n'
		desc += f'**INT:** {self.base_int:02d} | **CON:** {self.base_con:02d}\n\n'
		desc += f'**Starting Weapon:** {self.starting_weapon.name}\n'
		if self.starting_off_hand:
			desc += f'**Starting Off Hand:** {self.starting_off_hand.name}'
		desc += f'\n\n**Weight Class:** {self.weight}'
		return Page(self.name, desc, colour=(150, 150, 150))