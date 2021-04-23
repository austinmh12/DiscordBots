from . import rarity_info, Page, chunk
from .pokemon import get_pokemon_info, get_random_pokemon_by_rarity, PokeBattle
from random import choices, randint, random
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

#############
# Functions #
#############

###########
# Classes #
###########
class BattleLog:
	def __init__(self, user, opponent):
		self.user = user
		self.opponent = opponent
		self.log = []
		self.winner = None
		self.rewards = {
			'exp': 0,
			'rolls': 0,
			'cash': 0
		} if isinstance(opponent, Trainer) else {}
		self.pages = []
		self.battle()

	def available_pokemon(self, player):
		return any([(0 if pkbt.current_hp <= 0 else pkbt.current_hp) for pkbt in player._party])

	def battling(self):
		return self.available_pokemon(self.user) and self.available_pokemon(self.opponent)

	def calc_damage(self, atkr, defn):
		return int((randint(85, 100) / 100) * (((((2 * atkr.level) / 5) + 2) * (atkr.attack / defn.defense)) + 2))

	def battle(self):
		user_idx = 0
		opponent_idx = 0
		turn = 'u' if round(random(), 0) else 'o'
		self.log.append(f'{self.user.username} goes first!') if turn == 'u' else self.log.append(f'Opponent goes first!')
		while self.battling():
			user_pkbt = self.user._party[user_idx]
			opponent_pkbt = self.opponent._party[opponent_idx]
			if turn == 'u':
				dmg = self.calc_damage(user_pkbt, opponent_pkbt)
				opponent_pkbt.current_hp -= dmg
				self.log.append(f'{user_pkbt.name} did {int(dmg)} damage to {opponent_pkbt.name}')
				if opponent_pkbt.current_hp <= 0:
					opponent_idx += 1
					self.log.append(f'**Opponent\'s {opponent_pkbt.name} fainted**')
					if self.rewards:
						self.add_rewards(opponent_pkbt)
				turn = 'o'
			else:
				dmg = self.calc_damage(opponent_pkbt, user_pkbt)
				user_pkbt.current_hp -= dmg
				self.log.append(f'{opponent_pkbt.name} did {int(dmg)} damage to {user_pkbt.name}')
				if user_pkbt.current_hp <= 0:
					user_idx += 1
					self.log.append(f'**Your {user_pkbt.name} fainted**')
				turn = 'u'
		if self.available_pokemon(self.user):
			self.log.append('***All opponent\'s pokemon fainted!***')
			self.winner = self.user
		else:
			self.log.append('***All of your pokemon fainted!***')
			self.log.append('***You whited out!***')
			self.winner = self.opponent
		desc = ''
		for slot, pkbt in enumerate(self.opponent._party, start=1):
			if pkbt.current_hp <= 0:
				desc += '~~'
			desc += f'**{slot}:** {pkbt.name} - _{pkbt.level}_ {":star:" * pkbt.rarity}'
			desc += '~~\n' if pkbt.current_hp <= 0 else '\n'
		self.pages.append(Page('Battle Results - Opponent', desc))
		log_chunks = list(chunk(self.log, 15))
		self.pages.extend([Page('Battle Results - Log', lc) for lc in log_chunks])

	def add_rewards(self, pkbt):
		self.rewards['exp'] += rarity_info[pkbt.rarity]['exp'] * pkbt.level * (1 + (.1 * self.user.get_upgrade('exprates')))
		self.rewards['rolls'] += rarity_info[pkbt.rarity]['rolls']
		self.rewards['cash'] += rarity_info[pkbt.rarity]['cash']

	@property
	def exp(self):
		return int(self.rewards['exp'] / len(self.opponent._party))

	@property
	def rolls(self):
		return round(self.rewards['rolls'] / len(self.opponent._party), 2)
		
	@property
	def cash(self):
		return int(self.rewards['cash'] / len(self.opponent._party))

class Trainer:
	def __init__(self, size, level, rarity):
		self._party = self.generate_party(size, level, rarity)

	def generate_party(self, size, level, rarity):
		ret = []
		for i in range(size):
			pkmn_rarity = choices([1, 2, 3, 4, 5, 6], weights=[max(0, 3 - abs(i - rarity)) for i in range(1, 7)])[0]
			pkmn = get_random_pokemon_by_rarity(pkmn_rarity)
			pkin = get_pokemon_info(pkmn.id)
			lvl = randint(max(1, int(level * .90)), min(100, int(level * 1.10)))
			ret.append(PokeBattle.from_id(pkmn.id, lvl))
		return ret

class Leader(Trainer):
	def __init__(self, name, party):
		self.name = name
		self._party = party

	@property
	def avg_party_level(self):
		return sum([pkbt.level for pkbt in self._party]) // len(self._party)

	# Gym leaders #
	@classmethod
	def brock(cls):
		return cls('Brock',
			[
				PokeBattle.from_id(74, 12),
				PokeBattle.from_id(95, 14)
			]
		)

	@classmethod
	def bugsy(cls):
		return cls('Bugsy',
			[
				PokeBattle.from_id(11, 14),
				PokeBattle.from_id(14, 14),
				PokeBattle.from_id(123, 15)
			]
		)

	@classmethod
	def wattson(cls):
		return cls('Wattson',
			[
				PokeBattle.from_id(100, 20),
				PokeBattle.from_id(309, 20),
				PokeBattle.from_id(82, 22),
				PokeBattle.from_id(310, 24)
			]
		)

	@classmethod
	def maylene(cls):
		return cls('Maylene',
			[
				PokeBattle.from_id(307, 28),
				PokeBattle.from_id(67, 29),
				PokeBattle.from_id(448, 32)
			]
		)

	@classmethod
	def clay(cls):
		return cls('Clay',
			[
				PokeBattle.from_id(552, 34),
				PokeBattle.from_id(28, 34),
				PokeBattle.from_id(95, 34),
				PokeBattle.from_id(530, 36)
			]
		)

	@classmethod
	def valerie(cls):
		return cls('Valerie',
			[
				PokeBattle.from_id(303, 38),
				PokeBattle.from_id(122, 39),
				PokeBattle.from_id(700, 42)
			]
		)

	@classmethod
	def hapu(cls):
		return cls('Hapu',
			[
				PokeBattle.from_id(623, 48),
				PokeBattle.from_id(423, 48),
				PokeBattle.from_id(330, 48),
				PokeBattle.from_id(750, 49)
			]
		)

	@classmethod
	def raihan(cls):
		return cls('Raihan',
			[
				PokeBattle.from_id(526, 51),
				PokeBattle.from_id(330, 52),
				PokeBattle.from_id(844, 51),
				PokeBattle.from_id(884, 53)
			]
		)

	# Elite Four #
	@classmethod
	def will(cls):
		return cls('Will',
			[
				PokeBattle.from_id(437, 58),
				PokeBattle.from_id(124, 60),
				PokeBattle.from_id(326, 59),
				PokeBattle.from_id(80, 60),
				PokeBattle.from_id(282, 61),
				PokeBattle.from_id(178, 62)
			]
		)

	@classmethod
	def koga(cls):
		return cls('Koga',
			[
				PokeBattle.from_id(435, 61),
				PokeBattle.from_id(454, 60),
				PokeBattle.from_id(317, 62),
				PokeBattle.from_id(49, 63),
				PokeBattle.from_id(89, 62),
				PokeBattle.from_id(169, 64)
			]
		)

	@classmethod
	def bruno(cls):
		return cls('Bruno',
			[
				PokeBattle.from_id(237, 62),
				PokeBattle.from_id(106, 61),
				PokeBattle.from_id(297, 62),
				PokeBattle.from_id(68, 64),
				PokeBattle.from_id(448, 64),
				PokeBattle.from_id(107, 61)
			]
		)

	@classmethod
	def karen(cls):
		return cls('Karen',
			[
				PokeBattle.from_id(461, 62),
				PokeBattle.from_id(442, 62),
				PokeBattle.from_id(430, 64),
				PokeBattle.from_id(197, 64),
				PokeBattle.from_id(229, 63),
				PokeBattle.from_id(359, 63)
			]
		)

	@classmethod
	def lance(cls):
		return cls('Lance',
			[
				PokeBattle.from_id(373, 72),
				PokeBattle.from_id(445, 72),
				PokeBattle.from_id(149, 75),
				PokeBattle.from_id(6, 68),
				PokeBattle.from_id(334, 73),
				PokeBattle.from_id(130, 68)
			]
		)

class Raid:
	def __init__(self, players, difficulty):
		self.players = players
		self.difficulty = difficulty
		self.pokemon = self.generate_raid()
		self.won = False
		self.rewards = {
			'exp': 0,
			'rolls': 0,
			'cash': 0
		}
		self.log = []
		self.pages = []
		self.raid()

	@property
	def available_raid_pokemon(self):
		return any([(0 if pkbt.current_hp <= 0 else pkbt.current_hp) for pkbt in self.pokemon])

	def calc_damage(self, atkr, defn):
		return int((randint(85, 100) / 100) * (((((2 * atkr.level) / 5) + 2) * (atkr.attack / defn.defense)) + 2))

	def available_pokemon(self, player):
		return any([(0 if pkbt.current_hp <= 0 else pkbt.current_hp) for pkbt in player._party])

	def generate_raid(self):
		ret = []
		if self.difficulty == 'easy':
			# 4 pokemon of rarity 7
			ret.extend([PokeBattle.from_id(get_random_pokemon_by_rarity(7).id, 120) for _ in range(4)])
		if self.difficulty == 'medium':
			# 5 pokemon of rarity 7, 2 of rarity 8
			ret.extend([PokeBattle.from_id(get_random_pokemon_by_rarity(7).id, 120) for _ in range(5)])
			ret.extend([PokeBattle.from_id(get_random_pokemon_by_rarity(8).id, 120) for _ in range(2)])
		if self.difficulty == 'hard':
			# 7 pokemon of rarity 7, 3 of rarity 8
			ret.extend([PokeBattle.from_id(get_random_pokemon_by_rarity(7).id, 120) for _ in range(7)])
			ret.extend([PokeBattle.from_id(get_random_pokemon_by_rarity(8).id, 120) for _ in range(3)])
		return ret

	def available_players(self):
		return any([self.available_pokemon(player) for player in self.players])

	def raiding(self):
		return self.available_players() and self.available_raid_pokemon

	def battling(self, player):
		return self.available_pokemon(player) and self.available_raid_pokemon

	def raid(self):
		player_idx = 0
		pkmn_idx = 0
		while self.raiding():
			turn = 'u'
			player = self.players[player_idx]
			self.log.append(f'{player.username} goes first!')
			player_poke_idx = 0
			while self.battling(player):
				player_pkbt = player._party[player_poke_idx]
				opponent_pkbt = self.pokemon[pkmn_idx]
				if turn == 'u':
					dmg = self.calc_damage(player_pkbt, opponent_pkbt)
					opponent_pkbt.current_hp -= dmg
					self.log.append(f'{player_pkbt.name} did {int(dmg)} damage to {opponent_pkbt.name}')
					if opponent_pkbt.current_hp <= 0:
						pkmn_idx += 1
						self.log.append(f'**Opponent\'s {opponent_pkbt.name} fainted**')
						if self.rewards:
							self.add_rewards(opponent_pkbt, player)
					turn = 'o'
				else:
					dmg = self.calc_damage(opponent_pkbt, player_pkbt)
					player_pkbt.current_hp -= dmg
					self.log.append(f'{opponent_pkbt.name} did {int(dmg)} damage to {player_pkbt.name}')
					if player_pkbt.current_hp <= 0:
						player_poke_idx += 1
						self.log.append(f'**Your {player_pkbt.name} fainted**')
					turn = 'u'
			if self.available_pokemon(player):
				self.log.append('***All opponent\'s pokemon fainted!***')
				break
			else:
				self.log.append('***All of your pokemon fainted!***')
				self.log.append('***You whited out!***')
				player_idx += 1
		if self.available_players():
			self.won = True
		desc = ''
		for slot, pkbt in enumerate(self.pokemon, start=1):
			if pkbt.current_hp <= 0:
				desc += '~~'
			desc += f'**{slot}:** {pkbt.name} - _{pkbt.level}_ {":star:" * pkbt.rarity}'
			desc += '~~\n' if pkbt.current_hp <= 0 else '\n'
		self.pages.append(Page('Battle Results - Opponent', desc))
		log_chunks = list(chunk(self.log, 15))
		self.pages.extend([Page('Battle Results - Log', lc) for lc in log_chunks])
		
	def add_rewards(self, pkbt, player):
		self.rewards['exp'] += rarity_info[pkbt.rarity]['exp'] * pkbt.level * (1 + (.1 * player.get_upgrade('exprates')))
		self.rewards['rolls'] += rarity_info[pkbt.rarity]['rolls']
		self.rewards['cash'] += rarity_info[pkbt.rarity]['cash']

	@property
	def exp(self):
		return int(self.rewards['exp'] / len(self.pokemon))

	@property
	def rolls(self):
		return round(self.rewards['rolls'] / len(self.pokemon), 2)
		
	@property
	def cash(self):
		return int(self.rewards['cash'] / len(self.pokemon))

#############
# Constants #
#############
# Need to be here due to compiling errors #
gym_leaders = {
	1: Leader.brock,
	2: Leader.bugsy,
	3: Leader.wattson,
	4: Leader.maylene,
	5: Leader.clay,
	6: Leader.valerie,
	7: Leader.hapu,
	8: Leader.raihan
}

elite_four = {
	1: Leader.will,
	2: Leader.koga,
	3: Leader.bruno,
	4: Leader.karen,
	5: Leader.lance
}