from .sets import Set

class Card:
	def __init__(self, id, name, supertype, set, number, rarity, images, tcgplayer, **kwargs):
		self.id = id
		self.name = name
		self.supertype = supertype
		self.set = Set.from_dict(set)
		self.number = number
		self.rarity = rarity
		self.images = images
		self.price = tcgplayer.get('prices').get('normal').get('market')

	@classmethod
	def from_api(cls, api_data):
		return cls(**api_data)

	@property
	def page(self):
		...
		return Page()