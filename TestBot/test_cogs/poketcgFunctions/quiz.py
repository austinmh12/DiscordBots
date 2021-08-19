from .. import sql, log
from io import BytesIO
from PIL import Image
from random import choice, choices, random
import json

def update_player_quiz_stats(player, correct):
	...

class Quiz:
	def __init__(self, nat_id, name):
		self.nat_id = nat_id
		self.name = name
		self.gen = self.get_gen(nat_id)

	@property
	def image(self):
		...

	@property
	def silhouette(self):
		...

	def get_gen(self, nat_id):
		...