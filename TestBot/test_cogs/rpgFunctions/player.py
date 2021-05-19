from .. import sql, log, BASE_PATH, chunk

#############
# Constants #
#############


#############
# Functions #
#############
def get_player(id, guild_id):
	...

def add_player(id, guild_id):
	...

###########
# Classes #
###########
class Player:
	def __init__(self,
				id,
				guild_id,
				current_character=None
	):
		self.id = id
		self.guild_id = guild_id
		self.current_character = current_character

	@classmethod
	def from_ids(cls, id, guild_id):
		return get_player(id, guild_id)