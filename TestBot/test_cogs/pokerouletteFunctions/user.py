from . import sql, achievement_stat_mapping, achievement_requirements
from .pokemon import PokeBattle, get_user_total_level, get_user_pokedex, get_badges, get_user_poke_battle
from datetime import datetime as dt, timedelta as td
import json
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

#############
# Constants #
#############
default_achievements = {
	'rolls': [0],
	'pokemon': [0],
	'upgrades': [0],
	'released': [0],
	'gifts': [0],
	'boofs': [0],
	'trades': [0],
	'pokecash': [0],
	'safari': [0],
	'badges': [0],
	'stored': [0],
	'battles': [0],
	'gyms': [0],
	'levels': [0],
	'elite four': [0],
	'raids': [0],
	'raids complete': [0]
}

default_upgrades = {
	'baserarity': 0, 		# 1
	'shinyrarity': 0, 		# 2
	'rollcooldown': 0, 		# 3
	'rollrefund': 0, 		# 4
	'doublecash': 0, 		# 6
	'dailycooldown': 0, 	# 7
	'dittocooldown': 0, 	# 8
	'fasterbadge': 0, 		# 9
	'huntchance': 0,		# 10
	'upgradediscount': 0, 	# 11
	'safarirefresh': 0, 	# 12
	'exprates': 0,			# 13
	'battlecooldown': 0,	# 14
	'e4cooldown': 0,		# 15
	'daycaretime': 0,		# 16
	'tradecooldown': 0,		# 17
	'fullreset': 0,			# 18
	'raidchance': 0,		# 19
	'raidreset': 0,			# 20
}

default_hunting = {'poke_id': 0, 'caught': 0}

default_options = {'wtconfirm': 'y'}

#############
# Functions #
#############
def get_all_users():
	df = sql('select * from users', ())
	if df.empty:
		return []
	return [User(**u) for u in df.to_dict('records')]

def get_user(id):
	df = sql('select * from users where id = ?', (id,))
	if df.empty:
		return None
	return User(**df.to_dict('records')[0])

def add_user(id, name):
	user = User(
		id, 						# id
		name,						# username
		dt(1999,1,1), 				# roll_reset
		0, 							# pokecash
		0, 							# boofs
		default_upgrades, 			# upgrades
		0, 							# stored_rolls
		0, 							# total_rolls
		0, 							# total_pokecash
		0, 							# total_released
		0, 							# total_caught
		0, 							# total_traded
		0, 							# total_bought
		dt(1999,1,1), 				# daily_reward
		dt(1999,1,1), 				# ditto_reset
		0, 							# total_gifts
		default_achievements, 		# achievements
		default_hunting,			# hunting
		default_options,			# options
		[],							# party
		0,							# total_battles
		dt(1999,1,1),				# battle_reset
		[],							# savelist
		[],							# gyms
		dt(1999,1,1),				# gym_reset
		0,							# e4_completions
		dt(1999,1,1),				# e4_reset
		dt(1999,1,1),				# wt_reset
		{},							# saved_parties
		0,							# total_raids
		0,							# raid_completions
		0							# favourite
	)
	sql('insert into users values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,0,?,?,?,?,?,?,?,?,?,?,?)', user.user_creation_row)
	return user

###########
# Classes #
###########
class User:
	def __init__(self, 
				id, 
				username, 
				roll_reset, 
				pokecash, 
				boofs, 
				upgrades, 
				stored_rolls, 
				total_rolls, 
				total_pokecash, 
				total_released, 
				total_caught, 
				total_traded, 
				total_bought, 
				daily_reward,
				ditto_reset,
				total_gifts,
				achievements,
				hunting,
				options,
				party,
				total_battles,
				battle_reset,
				savelist,
				gyms,
				gym_reset,
				e4_completions,
				e4_reset,
				wt_reset,
				saved_parties,
				total_raids,
				raid_completions,
				favourite,
				**kwargs
	):
		# Seting initial values
		self.id = id
		self.username = username
		self._roll_reset = dt.strptime(roll_reset, '%Y-%m-%d %H:%M:%S') if isinstance(roll_reset, str) else roll_reset
		self.pokecash = pokecash
		self.boofs = boofs
		self._upgrades = json.loads(upgrades) if isinstance(upgrades, str) else upgrades
		self.stored_rolls = stored_rolls
		self.total_rolls = total_rolls
		self.total_pokecash = total_pokecash
		self.total_released = total_released
		self.total_caught = total_caught
		self.total_traded = total_traded
		self.total_bought = total_bought
		self._daily_reward = dt.strptime(daily_reward, '%Y-%m-%d %H:%M:%S') if isinstance(daily_reward, str) else daily_reward
		self._ditto_reset = dt.strptime(ditto_reset, '%Y-%m-%d %H:%M:%S') if isinstance(ditto_reset, str) else ditto_reset
		self.total_gifts = total_gifts
		self._achievements = json.loads(achievements) if isinstance(achievements, str) else achievements
		self._hunting = json.loads(hunting) if isinstance(hunting, str) else hunting
		self._options = json.loads(options) if isinstance(options, str) else options
		self._party = self.get_party(party)
		self.total_battles = total_battles
		self._battle_reset = dt.strptime(battle_reset, '%Y-%m-%d %H:%M:%S') if isinstance(battle_reset, str) else battle_reset
		self._savelist = json.loads(savelist) if isinstance(savelist, str) else savelist
		self._gyms = json.loads(gyms) if isinstance(gyms, str) else gyms
		self._gym_reset = dt.strptime(gym_reset, '%Y-%m-%d %H:%M:%S') if isinstance(gym_reset, str) else gym_reset
		self.e4_completions = e4_completions
		self._e4_reset = dt.strptime(e4_reset, '%Y-%m-%d %H:%M:%S') if isinstance(e4_reset, str) else e4_reset
		self._wt_reset = dt.strptime(wt_reset, '%Y-%m-%d %H:%M:%S') if isinstance(wt_reset, str) else wt_reset
		self._saved_parties = self.get_saved_parties(saved_parties)
		self.total_raids = total_raids
		self.raid_completions = raid_completions
		self.favourite = favourite

		# Original cached user
		self.loaded = self.to_dict().copy()

		# Migration
		self._upgrades = self.migrate_dict(self._upgrades, default_upgrades, 'upgrades')
		self._achievements = self.migrate_dict(self._achievements, default_achievements, 'achievements')
		self._hunting = self.migrate_dict(self._hunting, default_hunting, 'hunting')
		self._options = self.migrate_dict(self._options, default_options, 'options')
		self._party = self.migrate_list(self._party, 'party')
		self._savelist = self.migrate_list(self._savelist, 'savelist')
		self._gyms = self.migrate_list(self._gyms, 'gyms')

	##############
	# Properties #
	##############
	@property
	def roll_reset(self):
		return dt.strftime(self._roll_reset, '%Y-%m-%d %H:%M:%S')

	@property
	def daily_reward(self):
		return dt.strftime(self._daily_reward, '%Y-%m-%d %H:%M:%S')

	@property
	def ditto_reset(self):
		return dt.strftime(self._ditto_reset, '%Y-%m-%d %H:%M:%S')

	@property
	def battle_reset(self):
		return dt.strftime(self._battle_reset, '%Y-%m-%d %H:%M:%S')
	
	@property
	def upgrades(self):
		return json.dumps(self._upgrades)

	@property
	def achievements(self):
		return json.dumps(self._achievements)

	@property
	def hunting(self):
		return json.dumps(self._hunting)

	@property
	def options(self):
		return json.dumps(self._options)

	@property
	def savelist(self):
		return json.dumps(self._savelist)

	@property
	def gyms(self):
		return json.dumps(self._gyms)

	@property
	def gym_reset(self):
		return dt.strftime(self._gym_reset, '%Y-%m-%d %H:%M:%S')

	@property
	def e4_reset(self):
		return dt.strftime(self._e4_reset, '%Y-%m-%d %H:%M:%S')

	@property
	def party(self):
		return json.dumps([pkbt.to_dict() for pkbt in self._party if pkbt])

	@property
	def wt_reset(self):
		return dt.strftime(self._wt_reset, '%Y-%m-%d %H:%M:%S')

	@property
	def saved_parties(self):
		ret = {slot: [pkbt.id for pkbt in party if pkbt] for slot, party in self._saved_parties.items()}
		return json.dumps(ret)	

	@property
	def user_creation_row(self):
		return (
			self.id, 
			self.username, 
			self.roll_reset, 
			self.pokecash, 
			self.boofs, 
			self.upgrades, 
			self.stored_rolls, 
			self.total_rolls, 
			self.total_pokecash, 
			self.total_released, 
			self.total_caught, 
			self.total_traded, 
			self.total_bought, 
			self.daily_reward,
			self.ditto_reset,
			self.total_gifts,
			self.achievements,
			self.hunting,
			self.options,
			self.party,
			self.total_battles,
			self.battle_reset,
			self.savelist,
			self.gyms,
			self.gym_reset,
			self.e4_completions,
			self.e4_reset,
			self.wt_reset,
			self.saved_parties,
			self.total_raids,
			self.raid_completions,
			self.favourite
		)

	@property
	def has_party(self):
		return any(self._party)

	@property
	def avg_party_level(self):
		if self.has_party:
			return sum([pkbt.level for pkbt in self._party]) // len(self._party)
		return 0

	@property
	def avg_party_rarity(self):
		if self.has_party:
			return sum([pkbt.rarity for pkbt in self._party]) // len(self._party)
	
	#############
	# Functions #
	#############
	# Migration #
	def migrate_dict(self, current, default, field=''):
		if not current:
			return default
		if current.keys() != default.keys():
			if field:
				log.debug(f'Migrating {field}')
			tmp = current.copy()
			for k in default.keys():
				if k not in tmp.keys():
					current[k] = default[k]
			for k in tmp.keys():
				if k not in default.keys():
					del current[k]
		return current

	def migrate_list(self, current, field=''):
		if not isinstance(current, list):
			if field:
				log.debug(f'Migrating {field}')
			return []
		return current

	# Upgrades #
	def get_upgrade(self, upgrade):
		return self._upgrades.get(upgrade, None)

	# Achievements #
	def get_achievement(self, category):
		return self._achievements.get(category, [0])

	def has_achievement(self, category, rank):
		return rank in self.get_achievement(category)

	def add_achievement(self, category, rank):
		self._achievements[category].append(rank)

	def reward_achievements(self, *categories):
		rolls_earned = 0
		cash_earned = 0
		reward_str = ''
		for category in categories:
			max_ach = max(self.get_achievement(category))
			prev = -1
			while prev != max_ach:
				next_ach = achievement_requirements.get(category).get(max_ach + 1, None)
				if not next_ach:
					break
				stat_map = achievement_stat_mapping.get(category)
				if not stat_map:
					if category == 'pokemon':
						stat = len(get_user_pokedex(self))
					if category == 'upgrades':
						stat = sum(self._upgrades.values())
					if category == 'badges':
						stat = sum(b.amount for b in get_badges(self))
					if category == 'gyms':
						stat = max(self._gyms) if self._gyms else 0
					if category == 'levels':
						stat = get_user_total_level(self)
				else:
					stat = self.to_dict()[stat_map]
				if stat >= next_ach:
					rolls = .5 * (2 ** max_ach + 1)
					cash = 100 * (2 ** max_ach + 1)
					rolls_earned += rolls
					cash_earned += cash
					reward_str += f'You got the **{"bOofs" if category == "boofs" else category.capitalize()} {max_ach + 1}** achievement and earned **{rolls}** rolls and **{cash}** PokeCash!\n'
					self.add_achievement(category, max_ach + 1)
				prev = max_ach
				max_ach = max(self.get_achievement(category))
		self.stored_rolls += rolls_earned
		self.pokecash += cash_earned
		self.total_pokecash += cash_earned
		self.update()
		return reward_str

	# Party #
	def get_party(self, party):
		ret = []
		if isinstance(party, str):
			party = json.loads(party)
		if not party:
			party = []
		else:
			for pkbt in party:
				ret.append(get_user_poke_battle(self, pkbt['poke_id']))
		return ret

	def get_saved_parties(self, parties):
		ret = {}
		if isinstance(parties, str):
			parties = json.loads(parties)
		if not parties:
			parties = {}
		else:
			for slot, party in parties.items():
				pt = []
				for id in party:
					pkbt = get_user_poke_battle(self, id)
					if pkbt:
						pt.append(pkbt)
				ret[int(slot)] = pt
				# ret[int(slot)] = [get_user_poke_battle(self, id) for id in party]
		return ret

	def refresh_party(self):
		self._party = [pkbt for pkbt in self._party if pkbt]
		self.update()

	def refresh_saved_party(self, party):
		return [pkbt for pkbt in party if pkbt]

	def refresh_saved_parties(self):
		ret = {}
		for i, k in enumerate(self._saved_parties.keys(), start=1):
			ret[i] = self.refresh_saved_party(self._saved_parties[k])
		self._saved_parties = ret
		self.update()

	def heal_party(self):
		for pkbt in self._party:
			if pkbt:
				pkbt.full_health()

	def add_exp_to_party(self, exp):
		ret_str = ''
		for pkbt in self._party:
			lvl_up = pkbt.add_exp(exp)
			if lvl_up:
				ret_str += f'**{pkbt.name}** leveled up! It\'s now level ***{pkbt.level}***\n'
			pkbt.update()
		self.refresh_party()
		return ret_str

	# Cooldowns #
	def refresh_cooldowns(self, upgrade):
		if upgrade == 'rollcooldown':
			self._roll_reset -= td(minutes=10)
		if upgrade == 'battlecooldown':
			self._battle_reset -= td(minutes=10)
		if upgrade == 'dailycooldown':
			self._daily_reward -= td(hours=1)
		if upgrade == 'gymcooldown':
			self._gym_reset -= td(hours=1)
		if upgrade == 'e4cooldown':
			self._e4_reset -= td(hours=1)
		if upgrade == 'dittocooldown':
			self._ditto_reset -= td(hours=1)
		if upgrade == 'tradecooldown':
			self._wt_reset -= td(hours=1)
		self.update()

	def cooldowns_now(self):
		self._roll_reset -= td(hours=24)
		self._battle_reset -= td(hours=24)
		self._daily_reward -= td(hours=24)
		self._gym_reset -= td(hours=24)
		self._e4_reset -= td(hours=24)
		self._ditto_reset -= td(hours=24)
		self._wt_reset -= td(hours=24)
		self.update()

	# Utility #
	def to_dict(self):
		return {
			'id': self.id,
			'username': self.username,
			'roll_reset': self.roll_reset,
			'pokecash': self.pokecash,
			'boofs': self.boofs,
			'upgrades': self.upgrades,
			'stored_rolls': round(self.stored_rolls, 2),
			'total_rolls': round(self.total_rolls, 2),
			'total_pokecash': self.total_pokecash,
			'total_released': self.total_released,
			'total_caught': self.total_caught,
			'total_traded': self.total_traded,
			'total_bought': self.total_bought,
			'daily_reward': self.daily_reward,
			'ditto_reset': self.ditto_reset,
			'total_gifts': self.total_gifts,
			'achievements': self.achievements,
			'hunting': self.hunting,
			'options': self.options,
			'party': self.party,
			'total_battles': self.total_battles,
			'battle_reset': self.battle_reset,
			'savelist': self.savelist,
			'gyms': self.gyms,
			'gym_reset': self.gym_reset,
			'e4_completions': self.e4_completions,
			'e4_reset': self.e4_reset,
			'wt_reset': self.wt_reset,
			'saved_parties': self.saved_parties,
			'total_raids': self.total_raids,
			'raid_completions': self.raid_completions,
			'favourite': self.favourite
		}

	def update(self):
		current = self.to_dict()
		sql_str = 'update users set '
		col_val = []
		for k in current.keys():
			if current[k] != self.loaded[k]:
				col_val.append((k, current[k]))
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where id = ?'
		vals = [v for _, v in col_val]
		vals.append(self.id)
		if not col_val:
			return
		return sql(sql_str, vals)

	def __bool__(self):
		return self.id > -1

	def __eq__(self, u):
		return self.id == u.id