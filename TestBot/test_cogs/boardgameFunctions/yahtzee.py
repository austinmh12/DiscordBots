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
	'fullhouse': (620, 982.0),
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

top_categories = ['1s', '2s', '3s', '4s', '5s', '6s']
bottom_categories = ['3kind', '4kind', 'fullhouse', 'small', 'large', 'yahtzee', 'chance']

class YahtzeeGame:
	def __init__(self, players):
		self.players = [YahtzeePlayer(p) for p in players]
		self.idx = 0
		self.current_player = self.players[self.idx]
		self.players_done = 0
		self.game_done = False
		self.winner = None

	def next_player(self):
		if self.players_done == len(self.players):
			return self.end_game()
		self.idx = (self.idx + 1) % len(self.players)
		self.current_player = self.players[self.idx]
		if not self.current_player.turns_left:
			self.players_done += 1
			return self.next_player()

	def end_game(self):
		self.game_done = True
		self.winner = max([(p, p.values['grand_total']) for p in self.players], key=lambda x: x[1])[0]

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
		self.turns_left = True

	@property
	def unscored_categories(self):
		return [k for k, v in self.values.items() if v == -1 and k not in ['subtotal_top', 'bonus', 'total_top_top', 'yahtzee_bonus1', 'yahtzee_bonus2', 'yahtzee_bonus3', 'yahtzee_bonus_total', 'total_bottom', 'total_top_bottom', 'grand_total']]

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

	def update_top_board_values(self):
		total_values = sum([v for k, v in self.values.items() if k in top_categories and v >= 0])
		self.values['subtotal_top'] = total_values
		if all([v >= 0 for k, v in self.values.items() if k in top_categories]):
			if self.values['subtotal_top'] >= 63:
				total_values += 35
				self.values['bonus'] = 35
			else:
				self.values['bonus'] = 0
			self.update_board('subtotal_top')
			self.update_board('bonus')
			self.values['total_top_top'] = total_values
			self.values['total_top_bottom'] = total_values
			self.update_board('total_top_top')
			self.update_board('total_top_bottom')

	def update_bottom_board_values(self):
		total_values = sum([v for k, v in self.values.items() if k in bottom_categories and v >= 0])
		if self.values['yahtzee_bonus_total'] >= 0:
			total_values += self.values['yahtzee_bonus_total']
		self.values['total_bottom'] = total_values
		if all([v >= 0 for k, v in self.values.items() if k in bottom_categories]):
			self.update_board('total_bottom')

	def update_total(self):
		top = self.values['total_top_bottom'] if self.values['total_top_bottom'] >= 0 else 0
		bottom = self.values['total_bottom'] if self.values['total_bottom'] >= 0 else 0
		self.values['grand_total'] = top + bottom
		self.update_board('grand_total')

	def update_bonus_yahtzee(self):
		if not self.values['yahtzee_bonus1']:
			self.values['yahtzee_bonus1'] = 'X'
			self.values['yahtzee_bonus_total'] = 100
			return self.update_board('yahtzee_bonus1')
		if not self.values['yahtzee_bonus2']:
			self.values['yahtzee_bonus2'] = 'X'
			self.values['yahtzee_bonus_total'] = 200
			return self.update_board('yahtzee_bonus2')
		if not self.values['yahtzee_bonus3']:
			self.values['yahtzee_bonus3'] = 'X'
			self.values['yahtzee_bonus_total'] = 300
			return self.update_board('yahtzee_bonus3')
		self.values['yahtzee_bonus_total'] = 300
		return self.update_board('yahtzee_bonus_total')

	def update_turns(self):
		self.turns_left = any([v < 0 for k, v in self.values.items() if k in top_categories or k in bottom_categories])

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
			has_four = False
			for i in set(self.held_dice):
				if self.held_dice.count(i) >= 4:
					has_four = True
			if has_four:
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
					if self.values['yahtzee'] == 50:
						value = 'bonus'
					else:
						value = 50
				else:
					value = 0
			else:
				value = 0
		else:
			value = sum(self.held_dice)
		if value == 'bonus':
			category = self.update_bonus_yahtzee()
		else:
			self.values[category] = value
			self.update_board(category)
		if category in top_categories:
			self.update_top_board_values()
		elif category in bottom_categories:
			self.update_bottom_board_values()
		else:
			pass
		if not self.unscored_categories:
			self.update_total()
		self.update_turns()
		self.last_roll = []
		self.held_dice = []
		self.remaining_rolls = 3
		self.held_this_turn = False