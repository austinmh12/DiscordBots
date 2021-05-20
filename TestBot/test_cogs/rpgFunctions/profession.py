from .. import sql, log, BASE_PATH, chunk

#############
# Constants #
#############
all_professions = [
	'warrior',
	'wizard',
	'archer',
	'rogue'
]
light_professions = ['archer', 'wizard']
medium_professions = ['rogue']
heavy_professions = ['warrior']

#############
# Functions #
#############
def get_professions():
	df = sql('rpg', 'select * from professions')
	return [Profession(**d) for d in df.to_dict('records')]

def get_profession(name):
	df = sql('rpg', 'select * from professions where name = ?', (name,))
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
				starting_off_hand
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
		self.starting_weapon = starting_weapon
		self.starting_off_hand = starting_off_hand