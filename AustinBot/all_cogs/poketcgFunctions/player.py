from .. import Page, sql, format_remaining_time
from datetime import datetime as dt
import json

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
	return player

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
		self.cached = self.to_dict().copy()

	@property
	def creation_row(self):
		return (
			self.discord_id,
			round(self.cash, 2),
			self.daily_reset.timestamp(),
			json.dumps(self.packs),
			self.packs_opened,
			self.packs_bought,
			round(self.total_cash, 2),
			self.total_cards,
			self.cards_sold
		)

	def to_dict(self):
		return {
			'discord_id': self.discord_id,
			'cash': round(self.cash, 2),
			'daily_reset': self.daily_reset.timestamp(),
			'packs': json.dumps(self.packs),
			'packs_opened': self.packs_opened,
			'packs_bought': self.packs_bought,
			'total_cash': round(self.total_cash, 2),
			'total_cards': self.total_cards,
			'cards_sold': self.cards_sold
		}

	def update(self):
		current = self.to_dict()
		sql_str = 'update players set '
		col_val = []
		for k in current.keys():
			if current[k] != self.cached[k]:
				col_val.append((k, current[k]))
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where discord_id = ?'
		vals = [v for _, v in col_val]
		vals.append(self.discord_id)
		if not col_val:
			return
		return sql('poketcg', sql_str, vals)

	@property
	def stats_desc(self):
		desc = f'**Wallet:** ${self.cash:.2f} | **Total Earned:** ${self.total_cash:.2f}\n\n'
		desc += f'**Current Packs:** {sum(self.packs.values())}\n'
		desc += f'**Opened Packs:** {self.packs_opened} | **Bought Packs:** {self.packs_bought}\n\n'
		desc += f'**Total Cards:** {self.total_cards} | **Cards Sold:** {self.cards_sold}\n\n'
		desc += f'Daily reset in **{format_remaining_time(self.daily_reset)}**'
		return desc