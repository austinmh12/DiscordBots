from .. import sql, log, BASE_PATH, chunk
from . import font
from PIL import Image, ImageDraw
from random import randint
import typing

# Constants
yahtzee_card_positions = {
	'1s': (620, 292),
	'2s': (620, 349.5),
	'3s': (620, 407.0),
	'4s': (620, 464.5),
	'5s': (620, 522.0),
	'6s': (620, 579.5),
	'subtotal_top': (620, 637.0),
	'bonus': (620, 694.5),
	'total_top_top': (620, 752.0),
	'3_of_a_kind': (620, 867.0),
	'4_of_a_kind': (620, 924.5),
	'full_house': (620, 982.0),
	'small_straight': (620, 1039.5),
	'large_straight': (620, 1097.0),
	'yahtzee': (620, 1154.5),
	'chance': (620, 1212.0),
	'yahtzee_bonus1': (580, 1269.5),
	'yahtzee_bonus2': (620, 1269.5),
	'yahtzee_bonus3': (660, 1269.5),
	'yahtzee_bonus_total': (620, 1327.0),
	'total_bottom': (620, 1384.5),
	'total_top_bottom': (620, 1442.0),
	'grand_total': (620, 1499.5)
}

class YahtzeeGame:
	def __init__(self, players):
		self.players = [YahtzeePlayer(p) for p in players]
		self.current_player = None

class YahtzeePlayer:
	def __init__(self, id):
		self.id = id
		self.board = Image.open(f'{BASE_PATH}/rsc/yahtzee_board.jpg')
		self.draw = ImageDraw.Draw(self.board)
		self.values = {
			'1s': -1,
			'2s': -1,
			'3s': -1,
			'4s': -1,
			'5s': -1,
			'6s': -1,
			'subtotal_top': -1,
			'bonus': -1,
			'total_top_top': -1,
			'3_of_a_kind': -1,
			'4_of_a_kind': -1,
			'full_house': -1,
			'small_straight': -1,
			'large_straight': -1,
			'yahtzee': -1,
			'chance': -1,
			'yahtzee_bonus1': '',
			'yahtzee_bonus2': '',
			'yahtzee_bonus3': '',
			'yahtzee_bonus_total': -1,
			'total_bottom': -1,
			'total_top_bottom': -1,
			'grand_total': -1
		}
		self.last_roll = []
		self.held_dice = []

	def update_board(self, row, value):
		x, y = yahtzee_card_positions.get(row, (0, 0))
		if not x:
			return
		tx, ty = self.draw.textsize(f'{value}', font=font)
		self.draw.text((x - (tx/2), y - (ty/2)), f'{value}', fill=(0, 0, 0), font=font)