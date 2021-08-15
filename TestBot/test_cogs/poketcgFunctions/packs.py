from random import choice, choices
from .sets import Set
from .card import Card, get_cards_with_query

rarity_mapping = {
	'Rare': 75,
	'Rare ACE': 10,
	'Rare BREAK': 10,
	'Rare Holo': 25,
	'Rare Holo EX': 12,
	'Rare Holo GX': 12,
	'Rare Holo LV.X': 12,
	'Rare Holo Star': 8,
	'Rare Holo V': 15,
	'Rare Holo VMAX': 10,
	'Rare Prime': 10,
	'Rare Prism Star': 10,
	'Rare Rainbow': 5,
	'Rare Secret': 1,
	'Rare Shining': 20,
	'Rare Shiny': 5,
	'Rare Shiny GX': 2,
	'Rare Ultra': 35,
	'Amazing Rare': 15,
	'LEGEND': 3
}

def generate_pack(set_id):
	pack = []
	cards = get_cards_with_query(f'set.id:{set_id.lower()}')
	rares = [c for c in cards if c.rarity not in ['Common', 'Uncommon', 'Promo']]
	uncommons = [c for c in cards if c.rarity == 'Uncommon']
	commons = [c for c in cards if c.rarity == 'Common']
	while len(pack) < 6:
		c = choice(commons)
		if c in pack:
			continue
		pack.append(c)
	while len(pack) < 9:
		u = choice(uncommons)
		if u in pack:
			continue
		pack.append(u)
	rare_weight = [rarity_mapping.get(r.rarity) for r in rares]
	rare = choices(rares, weights=rare_weight, k=1)[0]
	pack.append(rare)
	return Pack(set_id, pack)

def generate_packs(set_id, amount):
	pack = []
	cards = get_cards_with_query(f'set.id:{set_id.lower()}')
	rares = [c for c in cards if c.rarity not in ['Common', 'Uncommon', 'Promo']]
	uncommons = [c for c in cards if c.rarity == 'Uncommon']
	commons = [c for c in cards if c.rarity == 'Common']
	while len(pack) < 6 * amount:
		c = choice(commons)
		if c in pack:
			continue
		pack.append(c)
	while len(pack) < 9 * amount:
		u = choice(uncommons)
		if u in pack:
			continue
		pack.append(u)
	rares = choices(rares, weights=rare_weight, k=amount)
	pack.extend(rares)
	return Pack(set_id, packs)

class Pack:
	def __init__(self, set_id, cards):
		self.set_id = set_id
		self.cards = cards

	@property
	def pages(self):
		return [c.page for c in self.cards]

	def __iter__(self):
		yield from self.cards