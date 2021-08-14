from .. import Page
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
		log.error(str(e))
		log.debug(json.dumps(data))
		return []

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
			self.price = price['normal']['market']
		elif 'holofoil' in price:
			self.price = price['holofoil']['market']
		elif 'reverseHolofoil' in price:
			self.price = price['reverseHolofoil']['market']
		elif '1stEditionNormal' in price:
			self.price = price['1stEditionNormal']['market']
		else:
			self.price = 0.01

	@property
	def page(self):
		desc = f'_{self.supertype}_\n'
		desc += f'{self.number}/{self.set.total} {self.set.name}\n'
		desc += f'{self.rarity}\n'
		desc += f'Sells for: {self.price:.2f}'
		return Page(self.name, desc, self.colour, image=self.image)