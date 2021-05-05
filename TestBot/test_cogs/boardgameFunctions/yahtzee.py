from .. import sql, log, BASE_PATH, chunk
from . import font
from PIL import Image, ImageDraw
from random import randint
import typing
from io import BytesIO
from discord import File

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
	'3kind': (620, 867.0),
	'4kind': (620, 924.5),
	'full_house': (620, 982.0),
	'small': (620, 1039.5),
	'large': (620, 1097.0),
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
		self.idx = 0
		self.turn_counter = 0
		self.total_turns = 13 * len(self.players)
		self.current_player = self.players[self.idx]

	@property
	def game_done(self):
		return self.turn_counter < self.total_turns	

	def next_player(self):
		self.turn_counter += 1
		self.idx = (self.idx + 1) % len(self.players)
		self.current_player = self.players[self.idx]

class YahtzeePlayer:
	def __init__(self, id):
		self.id = id
		self.board = Image.open(f'{BASE_PATH}/rsc/yahtzee_base.jpg') # This might be bad with a lot of players
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
			'3kind': -1,
			'4kind': -1,
			'fullhouse': -1,
			'small': -1,
			'large': -1,
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
		self.remaining_rolls = 3
		self.held_this_turn = False

	@property
	def unscored_categories(self):
		return [k for k, v in self.values.items() if v == -1 and k not in ['subtotal_top', 'bonus', 'total_top_top', 'yahtzee_bonus_total', 'total_bottom', 'total_top_bottom', 'grand_total']]	

	def get_board(self):
		bytes_io = BytesIO()
		self.board.save(f'{BASE_PATH}/rsc/{self.id}_board.jpg', format='JPEG')
		return File(f'{BASE_PATH}/rsc/{self.id}_board.jpg', filename=f'{self.id}_board.jpg')

	def update_board(self, category):
		x, y = yahtzee_card_positions.get(category, (0, 0))
		if not x:
			return
		tx, ty = self.draw.textsize(f'{self.values[category]}', font=font)
		self.draw.text((x - (tx/2), y - (ty/2)), f'{self.values[category]}', fill=(0, 0, 0), font=font)

	def calculate_score(self, category):
		self.held_dice.extend(self.last_roll)
		if category == '1s':
			value = sum([d for d in self.held_dice if d == 1])
		elif category == '2s':
			value = sum([d for d in self.held_dice if d == 2])
		elif category == '3s':
			value = sum([d for d in self.held_dice if d == 3])
		elif category == '4s':
			value = sum([d for d in self.held_dice if d == 4])
		elif category == '5s':
			value = sum([d for d in self.held_dice if d == 5])
		elif category == '6s':
			value = sum([d for d in self.held_dice if d == 6])
		elif category == '3kind':
			has_three = False
			for i in set(self.held_dice):
				if self.held_dice.count(i) >= 3:
					has_three = True
			if has_three:
				value = sum(self.held_dice)
			else:
				value = 0
		elif category == '4kind':
			has_three = False
			for i in set(self.held_dice):
				if self.held_dice.count(i) >= 4:
					has_three = True
			if has_three:
				value = sum(self.held_dice)
			else:
				value = 0
		elif category == 'fullhouse':
			if len(set(self.held_dice)) == 2:
				three = False
				two = False
				for i in set(self.held_dice):
					if self.held_dice.count(i) == 2:
						two = True
					if self.held_dice.count(i) == 3:
						three = True
				if two and three:
					value = 25
				else:
					value = 0
			else:
				value = 0
		elif category == 'small':
			dice = list(set(self.held_dice))
			dice.sort()
			if dice == [1, 2, 3, 4] or dice == [2, 3, 4, 6] or dice == [3, 4, 5, 6]:
				value = 30
			else:
				value = 0
		elif category == 'large':
			dice = list(set(self.held_dice))
			dice.sort()
			if dice == [1, 2, 3, 4, 5] or dice == [2, 3, 4, 5, 6]:
				value = 40
			else:
				value = 0
		elif category == 'yahtzee':
			if len(set(self.held_dice)) == 1:
				if self.held_dice.count(self.held_dice[0]) == 5:
					value = 50
				else:
					value = 0
			else:
				value = 50
		else:
			value = sum(self.held_dice)
		self.values[category] = value
		self.last_roll = []
		self.held_dice = []
		self.remaining_rolls = 3
		self.held_this_turn = False
		self.update_board(category)