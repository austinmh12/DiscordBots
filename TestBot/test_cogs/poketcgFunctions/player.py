from .. import Page

def get_player(discord_id):
	...

def add_player(discord_id):
	...

class Player:
	def __init__(
		self, 
		discord_id, 
		cash, 
		daily_reset, 
		packs, 
		packs_opened,
		packs_bought,
		total_cash,
		total_cards,
		cards_sold
	):
		self.discord_id = discord_id
		self.cash = cash
		self.daily_reset = daily_reset
		self.packs = packs
		self.packs_opened = packs_opened
		self.packs_bought = packs_bought
		self.total_cash = total_cash
		self.total_cards = total_cards
		self.cards_sold = cards_sold