from .. import Page

def get_player(discord_id):
	...

def add_player(discord_id):
	...

class Player:
	def __init__(self, discord_id, cash, daily_reset, packs, opened_packs):
		self.discord_id = discord_id
		self.cash = cash
		self.daily_reset = daily_reset
		self.packs = packs
		self.opened_packs = opened_packs