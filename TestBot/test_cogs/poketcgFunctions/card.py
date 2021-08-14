import json
from .. import Page, log
from . import api_call
from .sets import Set

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
		log.error(str(e))
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

def add_card(player, card):
	...

def remove_card(player, card, amount=1):
	...

def sell_card(player, card, amount=1):
	...

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
			amt = 0.01
		self.price = amt

	@property
	def page(self):
		desc = ''
		desc += f'{self.rarity}\n'
		desc += f'_{self.supertype}_\n'
		desc += f'{self.number}/{self.set.total} {self.set.name}\n'
		desc += f'Sells for: {self.price:.2f}\n'
		desc += f'ID: {self.id}\n'
		return Page(self.name, desc, self.colour, image=self.image)