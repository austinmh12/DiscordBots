import json
from .. import Page, log, sql, chunk
from . import api_call
from .sets import Set
from .player import Player, get_player
from collections import Counter

# contants
UPDATE_CARDS = '''update cards
set amount = (select tc.amount from tmp_cards tc where tc.discord_id = cards.discord_id and tc.card_id = cards.card_id)
where cards.discord_id in (select tc.discord_id from tmp_cards tc where tc.discord_id = cards.discord_id and tc.card_id = cards.card_id)
	and cards.card_id in (select tc.card_id from tmp_cards tc where tc.discord_id = cards.discord_id and tc.card_id = cards.card_id);'''

# functions
def get_cards():
	data = api_call('cards')
	try:
		cards = [Card(**d) for d in data['data']]
		return cards		
	except Exception as e:
		log.error(str(e))
		log.debug(json.dumps(data))
		return []

def get_cards_with_query(q):
	params = {'q': q}
	data = api_call('cards', params)
	try:
		cards = [Card(**d) for d in data['data']]
		return cards		
	except Exception as e:
		log.debug(json.dumps(data))
		log.error(str(e), exc_info=True)
		return []

def get_card_by_id(card_id):
	data = api_call(f'cards/{card_id}')
	try:
		card = Card(**data['data'])
		return card
	except Exception as e:
		log.error(str(e))
		log.debug(json.dumps(data))
		return None

def get_player_cards(player):
	df = sql('poketcg', 'select card_id, amount from cards where discord_id = ?', (player.discord_id,))
	if df.empty:
		return []
	return [PlayerCard(player, **d) for d in df.to_dict('records')]

def get_player_card(player, card_id):
	df = sql('poketcg', 'select card_id, amount from cards where discord_id = ? and card_id = ?', (player.discord_id, card_id))
	if df.empty:
		return None
	return PlayerCard(player, **df.to_dict('records')[0])

def add_or_update_card(player, card):
	# TODO: revamp this garbage
	player_card = get_player_card(player, card.id)
	if player_card is None:
		player_card = PlayerCard(player.discord_id, card.id, -1)
	if player_card.amount == -1:
		sql('poketcg', 'insert into cards values (?,?,?)', (player.discord_id, card.id, 1))
	else:
		sql('poketcg', 'update cards set amount = ? where discord_id = ? and card_id = ?', (player.discord_id, card.id, player_card.amount + 1))

def add_or_update_cards_from_pack(player, pack):
	player_cards = get_player_cards(player)
	amounts = Counter(pack)
	unique = list(set(pack))
	new = [c for c in unique if c not in player_cards]
	updating = [c for c in unique if c not in new]
	if new:
		new_chunks = chunk(new, 249)
		for nc in new_chunks:
			vals = []
			sql_str = 'insert into cards values '
			for c in nc:
				sql_str += ' (?,?,?),'
				vals.extend((player.discord_id, c.id, amounts[c]))
			sql('poketcg', sql_str[:-1], vals)
	if updating:
		sql('poketcg', 'drop table if exists tmp_cards')
		sql('poketcg', 'create table tmp_cards (discord_id integer, card_id text, amount integer)')
		card_map = {c.card: c for c in player_cards}
		updating_chunks = chunk(updating, 249)
		for uc in updating_chunks:
			vals = []
			sql_str = 'insert into tmp_cards values '
			for u in uc:
				sql_str += ' (?,?,?),'
				amt = card_map.get(u.id).amount + amounts[u]
				vals.extend((player.discord_id, u.id, amt))
			sql('poketcg', sql_str[:-1], vals)
		sql('poketcg', UPDATE_CARDS)

def add_or_update_cards_from_player_cards(player, player_cards):
	new = [pc for pc in player_cards if pc.amount == -1]
	updating = [pc for pc in player_cards if pc not in new]
	if new:
		new_chunks = chunk(new, 249)
		for nc in new_chunks:
			vals = []
			sql_str = 'insert into cards values '
			for c in nc:
				sql_str += ' (?,?,?),'
				vals.extend((player.discord_id, c.card, 1))
			sql('poketcg', sql_str[:-1], vals)
	if updating:
		sql('poketcg', 'drop table if exists tmp_cards')
		sql('poketcg', 'create table tmp_cards (discord_id integer, card_id text, amount integer)')
		updating_chunks = chunk(updating, 249)
		for uc in updating_chunks:
			vals = []
			sql_str = 'insert into tmp_cards values '
			for u in uc:
				sql_str += ' (?,?,?),'
				vals.extend((player.discord_id, u.card, u.amount))
			sql('poketcg', sql_str[:-1], vals)
		sql('poketcg', UPDATE_CARDS)
	sql('poketcg', 'delete from cards where amount = 0')

class Card:
	colour = (243, 205, 11)

	def __init__(self, id, name, supertype, set, number, images, **kwargs):
		self.id = id
		self.name = name
		self.supertype = supertype
		self.set = Set(**set)
		self.number = number
		self.image = images['large']
		self.rarity = kwargs.get('rarity', '?')
		price = kwargs.get('tcgplayer', {}).get('prices', {})
		amt = None
		if price:
			if 'normal' in price:
				amt = price['normal']['market']
				if amt is None:
					amt = price['normal']['mid']
			elif 'holofoil' in price:
				amt = price['holofoil']['market']
				if amt is None:
					amt = price['holofoil']['mid']
			elif 'reverseHolofoil' in price:
				amt = price['reverseHolofoil']['market']
				if amt is None:
					amt = price['reverseHolofoil']['mid']
			elif '1stEditionNormal' in price:
				amt = price['1stEditionNormal']['market']
				if amt is None:
					amt = price['1stEditionNormal']['mid']
		else:
			price = kwargs.get('cardmarket', {}).get('prices', {})
			amt = price['averageSellPrice']
		self.price = 0.01 if amt is None else amt 

	@property
	def page(self):
		desc = ''
		desc += f'**{self.rarity}**\n'
		desc += f'_{self.supertype}_\n'
		desc += f'{self.number}/{self.set.total} {self.set.name}\n'
		desc += f'**Sells for:** ${self.price:.2f}\n'
		desc += f'**ID:** {self.id}\n'
		return Page(self.name, desc, self.colour, image=self.image)

	def __eq__(self, c):
		if isinstance(c, PlayerCard):
			return self.id == c.card
		return self.id == c.id

	def __hash__(self):
		return hash(self.id)

class PlayerCard:
	def __init__(self, player, card_id, amount):
		self.player = player
		self.card = card_id
		self.amount = amount

	@property
	def page(self):
		page = self.card.page
		page.desc += f'Owned: {self.amount}'
		return page

	def update(self):
		if self.amount != 0:
			return sql('poketcg', 'update cards set amount = ? where discord_id = ? and card_id = ?', (self.amount, self.player.discord_id, self.card))
		return sql('poketcg', 'delete from cards where discord_id = ? and card_id = ?', (self.player.discord_id, self.card))

	def __eq__(self, c):
		if isinstance(c, Card):
			return self.card == c.id
		return self.card == pc.card

	def __hash__(self):
		return hash(self.card_id)