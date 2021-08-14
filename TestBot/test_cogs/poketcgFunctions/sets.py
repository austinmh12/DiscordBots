import json
from datetime import datetime as dt, timedelta as td
from .. import Page, log
from . import api_call

# functions
def get_sets():
	data = api_call('sets')
	try:
		sets = [Set(**d) for d in data['data']]
		return sets		
	except Exception as e:
		log.error(str(e))
		log.debug(json.dumps(data))
		return []

def get_set(set_id):
	data = api_call(f'sets/{set_id}')
	try:
		set_ = Set(**data['data'])
		return set_		
	except Exception as e:
		log.error(str(e))
		log.debug(json.dumps(data))
		return None

class Set:
	def __init__(self, id, name, series, total, images, **kwargs):
		self.id = id
		self.name = name
		self.series = series
		self.total = total
		self.images = images
		self.release_date = dt.strptime(kwargs.get('releaseDate'), '%Y/%m/%d')

	@property
	def page(self):
		desc = ''
		desc += f'Series: {self.series}\n'
		desc += f'Total cards: {self.total}\n'
		desc += f'ID: {self.id}'
		return Page(self.name, desc, image=self.images['logo'], thumbnail=self.images['symbol'])

	@property
	def pack_price(self):
		base_price = 4.50
		return base_price + (dt.now().year - self.release_date.year) * 0.50

	def __str__(self):
		return f'**{self.name}** _{self.id}_'