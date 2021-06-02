from .. import sql, log, BASE_PATH, chunk
from .character import Character, get_character
from .equipment import get_equipment
from .consumable import get_consumable
import json

#############
# Constants #
#############


#############
# Functions #
#############
def get_player(id, guild_id):
	df = sql('rpg', 'select * from players where id = ? and guild_id = ?', (id, guild_id))
	if df.empty:
		return None
	return Player(**df.to_dict('records')[0])

def add_player(id, guild_id):
	player = Player(id, guild_id)
	sql('rpg', 'insert into players values (?,?,?)', (player.id, player.guild_id, ''))
	return player

###########
# Classes #
###########
class Player:
	def __init__(self,
				id,
				guild_id,
				current_character='',
				bank={'gold': 0, 'equipment': [], 'consumables': []}
	):
		self.id = id
		self.guild_id = guild_id
		self.current_character = current_character if isinstance(current_character, Character) else get_character(self, current_character)
		self._bank = self.parse_bank(bank) if isinstance(bank, str) else bank

	@classmethod
	def from_ids(cls, id, guild_id):
		return get_player(id, guild_id)

	@property
	def bank(self):
		ret = {
			'gold': self._bank['gold'],
			'equipment': [e.id for e in self._bank['equipment']], 
			'consumables': [c.id for c in self._bank['consumables']]
		}
		return json.dumps(ret)

	def parse_bank(self, bank):
		ret = {'equipment': [], 'consumables': []}
		for e in inventory['equipment']:
			eq = get_equipment(e)
			if eq:
				ret['equipment'].append(eq)
		for c in inventory['consumables']:
			co = get_consumable(c)
			if co:
				ret['consumables'].append(co)
		ret['gold'] = bank['gold']
		return ret

	def update(self):
		sql('rpg', 'update players set current_character = ?, bank = ? where id = ? and guild_id = ?', (self.current_character.name if self.current_character else '', self.bank, self.id, self.guild_id))