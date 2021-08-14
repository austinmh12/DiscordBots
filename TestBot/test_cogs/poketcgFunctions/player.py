from .. import Page, sql
from datetime import datetime as dt

def get_player(discord_id):
	df = sql('poketcg', 'select * from players where discord_id = ?', (discord_id,))
	if df.empty:
		return add_player(discord_id)
	return Player(**df.to_dict('records')[0])

def add_player(discord_id):
	player = Player(
		discord_id,
		25,
		dt.now(),
		{},
		0,
		0,
		25,
		0,
		0
	)
	sql('poketcg', 'insert into players values (?,?,?,?,?,?,?,?,?)', player.creation_row)
	return Player

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
		self.daily_reset = daily_reset if isinstance(daily_reset, dt) else dt.fromtimestamp(daily_reset)
		self.packs = packs if isinstance(packs, dict) else json.loads(packs)
		self.packs_opened = packs_opened
		self.packs_bought = packs_bought
		self.total_cash = total_cash
		self.total_cards = total_cards
		self.cards_sold = cards_sold

	@property
	def creation_row(self):
		return (
			self.discord_id,
			self.cash,
			self.daily_reset.timestamp()
			json.dumps(self.packs),
			self.packs_opened,
			self.packs_bought,
			self.total_cash,
			self.total_cards,
			self.cards_sold
		)