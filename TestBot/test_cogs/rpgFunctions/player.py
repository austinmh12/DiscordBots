from .. import sql, log
from .character import get_character

#############
# Functions #
#############
def get_player(id, guild_id):
	df = sql('rpg', 'select * from players where id = ? and guild_id = ?', (id, guild_id))
	if df.empty:
		return add_player(id, guild_id)
	return Player(**df.to_dict('records')[0])

def add_player(id, guild_id):
	player = Player(id, guild_id, '')
	sql('rpg', 'insert into players values (?,?,?)', (player.id, player.guild_id, ''))
	return player

###########
# Classes #
###########
class Player:
	def __init__(self,
				id,
				guild_id,
				current_character,
	):
		self.id = id
		self.guild_id = guild_id
		self.current_character = get_character(id, guild_id, current_character) if isinstance(current_character, str) else current_character

	def update(self):
		sql('rpg', 'update players set current_character = ? where id = ? and guild_id = ?', (self.current_character.name if self.current_character else '', self.id, self.guild_id))