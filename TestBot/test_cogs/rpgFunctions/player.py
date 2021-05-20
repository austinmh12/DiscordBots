from .. import sql, log, BASE_PATH, chunk

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
				current_character=''
	):
		self.id = id
		self.guild_id = guild_id
		self.current_character = current_character

	@classmethod
	def from_ids(cls, id, guild_id):
		return get_player(id, guild_id)