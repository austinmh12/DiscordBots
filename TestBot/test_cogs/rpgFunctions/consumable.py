from .. import sql, log, BASE_PATH, chunk, Page
from . import *
from discord import Embed, Colour
from random import randint, choice

#############
# Constants #
#############


#############
# Functions #
#############
def get_next_consumable_id():
	df = sql('rpg', 'select id from consumables')
	if df.empty:
		return 1
	return max(df.id) + 1

def get_consumables():
	df = sql('rpg', 'select * from consumables')
	if df.empty:
		return []
	return [Consumable(**d) for d in df.to_dict('records')]

def get_consumable(id):
	df = sql('rpg', 'select * from consumables where id = ?', (id,))
	if df.empty:
		return None
	return Consumable(**df.to_dict('records')[0])

def add_consumable(consumable):
	sql('rpg', 'insert into consumables values (?,?,?,?,?,?)', consumable.to_row)

def delete_consumable(consumable):
	sql('rpg', 'delete from consumables where id = ?', (consumable.id,))

def generate_consumable(type, level):
	# Level just determines how many rolls it does
	id = get_next_consumable_id()
	if type in ('Health', 'Mana'):
		restored = sum([randint(0, 3) for _ in range(level)])
		consumable = RestorationPotion(id=id, name=f'{type} Potion ({restored})', type=type, restored=restored)
	else:
		stat = choice(['STR','DEX','INT','CON'])
		gain = sum([randint(0, 1) for _ in range(level)])
		consumable = StatPotion(id=id, name=f'{stat} Potion ({gain})', type=type, stat=stat, bonus=gain)
	add_consumable(consumable)
	return consumable

###########
# Classes #
###########
class Consumable:
	def __init__(self, id, name, type, **kwargs):
		self.id = id
		self.name = name
		self.type = type

class RestorationPotion(Consumable):
	def __init__(self, restored, **kwargs):
		super().__init__(**kwargs)
		self.restored = restored

	@property
	def to_row(self):
		return (
			self.id,
			self.name,
			self.type,
			self.restored,
			'',
			0
		)

	@property
	def price(self):
		return self.restored * 5
	
	@property
	def page(self):
		desc = f'Restores {self.restored} {self.type}\n\n'
		desc += f'**Sell Price:** {self.price} :coin:'
		return Page(self.name, desc, colour=(255, 45, 45) if self.type == 'Health' else (22, 0, 240))

class StatPotion(Consumable):
	def __init__(self, stat, bonus, **kwargs):
		super().__init__(**kwargs)
		self.stat = stat
		self.bonus = bonus

	@property
	def to_row(self):
		return (
			self.id,
			self.name,
			self.type,
			0,
			self.stat,
			self.bonus
		)

	@property
	def price(self):
		return self.bonus * 12
	
	@property
	def page(self):
		desc = f'Buffs {self.stat} by {self.bonus} for **1hr** (_does not stack_)\n\n'
		desc += f'**Sell Price:** {self.price} :coin:'
		return Page(self.name, desc, colour=(0, 218, 240))