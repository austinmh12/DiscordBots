from .. import sql, log, BASE_PATH
import requests as r
from io import BytesIO
from PIL import Image
from random import randint
import json
from discord import File

def generate_random_quiz():
	resp = r.get(f'https://pokeapi.co/api/v2/pokemon/{randint(1, 898)}').json()
	return Quiz(resp['id'], resp['name'])

class Quiz:
	def __init__(self, nat_id, name):
		self.nat_id = nat_id
		self.name = name
		self.gen = self.get_gen(nat_id)

	@property
	def image(self):
		return f'https://img.pokemondb.net/sprites/home/normal/{self.name}.png'

	@property
	def silhouette(self):
		image_data = r.get(self.image)
		im = Image.open(BytesIO(image_data.content))
		pixels = im.load()
		for i in range(im.size[0]):
			for j in range(im.size[1]):
				if pixels[i,j][-1] != 0:
					pixels[i,j] = (0, 0, 0, 255)
		b = BytesIO()
		im.save(b, format='PNG')
		b.seek(0)
		return File(b, filename='quizsilhouette.PNG')

	@property
	def revealed(self):
		image_data = r.get(self.image)
		im = Image.open(BytesIO(image_data.content))
		b = BytesIO()
		im.save(b, format='PNG')
		b.seek(0)
		return File(b, filename=f'{self.guess_name}.PNG')

	@property
	def guess_name(self):
		# Replaces -
		if self.name in ['mr-mime',
						'mr-rime',
						'mime-jr',
						'tapu-koko',
						'tapu-lele',
						'tapu-bulu',
						'tapu-fini']:
			return self.name.replace('-', ' ')
		# Keeps -
		if self.name in ['ho-oh',
						'porygon-z',
						'type-null',
						'jangmo-o',
						'hakamo-o',
						'kommo-o']:
			return self.name
		# Removes extras
		if '-' in self.name:
			return self.name.split('-')[0]
		# Name is fine
		else:
			return self.name

	def get_gen(self, nat_id):
		if nat_id <= 151:
			return '1'
		elif 151 < nat_id <= 251:
			return '2'
		elif 251 < nat_id <= 386:
			return '3'
		elif 368 < nat_id <= 493:
			return '4'
		elif 493 < nat_id <= 649:
			return '5'
		elif 649 < nat_id <= 721:
			return '6'
		elif 721 < nat_id <= 809:
			return '7'
		else:
			return '8'