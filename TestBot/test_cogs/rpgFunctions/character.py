from .. import sql, log, BASE_PATH, chunk, Page
from random import randint, random, choice
from datetime import datetime as dt, timedelta as td
import json
from . import *
from .equipment import (Equipment, Weapon, Armour, Jewelry, get_equipment, all_weapons,
	dual_wield_weapons, two_handed_weapons, all_armour, ignores_two_handed, jewelry)
from .profession import Profession, get_profession
from .area import Area, get_area
from .consumable import RestorationPotion, StatPotion, get_consumable
from .spell import Spell, get_spell

#############
# Constants #
#############


#############
# Functions #
#############
def get_all_characters():
	df = sql('rpg', 'select * from characters')
	if df.empty:
		return []
	return [Character(**d) for d in df.to_dict('records')]

def get_characters(id, guild_id):
	df = sql('rpg', 'select * from characters where player_id = ? and player_guild_id = ?', (id, guild_id))
	if df.empty:
		return []
	return [Character(**d) for d in df.to_dict('records')]

def get_character(id, guild_id, name):
	df = sql('rpg', 'select * from characters where player_id = ? and player_guild_id = ? and name = ?', (id, guild_id, name))
	if df.empty:
		return None
	return Character(**df.to_dict('records')[0])

def add_character(id, guild_id, name, profession, chest_id, legs_id, weapon_id, off_hand_id):
	char = Character(
		id,
		guild_id,
		name,
		profession,
		1, # Level
		0, # Exp
		0, # Gold
		None, # Helmet
		chest_id, # Chest
		legs_id, # Legs
		None, # Boots
		None, # Gloves
		None, # Amulet
		None, # Ring
		weapon_id,
		off_hand_id
	)
	sql('rpg', 'insert into characters values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', char.to_dict().values())
	return char

def delete_character(id, guild_id, name):
	sql('rpg', 'delete from characters where player_id = ? and player_guild_id = ? and name = ?', (id, guild_id, name))

###########
# Classes #
###########
# TODO: Remove underscore attrs and make them accessible as the type they'll be
# I.e. make current death_timer a datetime and inventory a dict
# Handle the conversions from db in the __init__ and conversions to db in to_dict
class Character:
	def __init__(self, 
				player_id,
				player_guild_id,
				name,
				profession,
				level,
				exp,
				gold,
				helmet,
				chest,
				legs,
				boots,
				gloves,
				amulet,
				ring,
				weapon,
				off_hand,
				current_con = -1,
				current_area = 'Sewer',
				death_timer = dt(1999, 1, 1),
				inventory = {'equipment': [], 'consumables': []},
				current_mp = -1,
				spells = '[]'
	):
		self.player_id = player_id
		self.player_guild_id = player_guild_id
		self.name = name
		self.profession = get_profession(profession) if isinstance(profession, str) else profession
		self.level = level
		self.exp = exp
		self.get_next_level_exp()
		self.gold = gold
		self.helmet = get_equipment(helmet) if isinstance(helmet, int) else helmet
		self.chest = get_equipment(chest) if isinstance(chest, int) else chest
		self.legs = get_equipment(legs) if isinstance(legs, int) else legs
		self.boots = get_equipment(boots) if isinstance(boots, int) else boots
		self.gloves = get_equipment(gloves) if isinstance(gloves, int) else gloves
		self.amulet = get_equipment(amulet) if isinstance(amulet, int) else amulet
		self.ring = get_equipment(ring) if isinstance(ring, int) else ring
		self.weapon = get_equipment(weapon) if isinstance(weapon, int) else weapon
		self.off_hand = get_equipment(off_hand) if isinstance(off_hand, int) else off_hand
		self.calculate_stats()
		self.current_con = self.stats['CON'] * 10 if 0 > current_con else current_con
		self.current_mp = self.stats['INT'] * 5 if 0 > current_mp else current_mp
		self.current_area = current_area if isinstance(current_area, Area) else get_area(current_area)
		self.death_timer = dt.fromtimestamp(death_timer) if isinstance(death_timer, int) else death_timer
		self.inventory = self.parse_inventory(inventory) if isinstance(inventory, str) else inventory
		self.spells = self.parse_spells(spells) if isinstance(spells, str) else spells

		# Original cached user
		self.cached = self.to_dict().copy()

	def to_dict(self):
		return {
			'player_id': self.player_id,
			'player_guild_id': self.player_guild_id,
			'name': self.name,
			'profession': self.profession.name,
			'level': self.level,
			'exp': self.exp,
			'gold': self.gold,
			'helmet': self.helmet.id if self.helmet else 0,
			'chest': self.chest if self.chest else 0,
			'legs': self.legs if self.legs else 0,
			'boots': self.boots if self.boots else 0,
			'gloves': self.gloves if self.gloves else 0,
			'amulet': self.amulet if self.amulet else 0,
			'ring': self.ring if self.ring else 0,
			'weapon': self.weapon if self.weapon else 0,
			'off_hand': self.off_hand if self.off_hand else 0,
			'current_con': self.current_con,
			'current_area': self.current_area,
			'death_timer': self.death_timer.timestamp(),
			'inventory': self.inventory_to_db(),
			'current_mp': self.current_mp,
			'spells': self.spells_to_db()
		}

	def inventory_to_db(self):
		ret = {
			'equipment': [e.id for e in self.inventory['equipment']], 
			'consumables': [c.id for c in self.inventory['consumables']]
		}
		return json.dumps(ret)

	def parse_inventory(self, inv):
		inventory = json.loads(inv)
		ret = {'equipment': [], 'consumables': []}
		for e in inventory['equipment']:
			eq = get_equipment(e)
			if eq:
				ret['equipment'].append(eq)
		for c in inventory['consumables']:
			co = get_consumable(c)
			if co:
				ret['consumables'].append(co)
		return ret

	def spells_to_db(self):
		return json.dumps([s.name for s in self.spells])

	def parse_spells(self, spells):
		spells = json.loads(spells)
		return [get_spell(s) for s in spells]
	
	def update(self):
		current = self.to_dict()
		if current == self.cached:
			return
		sql_str = 'update characters set '
		col_val = []
		for k in current.keys():
			if current[k] != self.cached[k]:
				if isinstance(current[k], Equipment):
					col_val.append((k, current[k].id))
				elif isinstance(current[k], Area):
					col_val.append((k, current[k].name))
				elif isinstance(current[k], Profession):
					col_val.append((k, current[k].name))
				else:
					col_val.append((k, current[k]))
		if not col_val:
			return
		sql_str += ', '.join([f'{col} = ?' for col, _ in col_val])
		sql_str += ' where player_id = ? and player_guild_id = ? and name = ?'
		vals = [v for _, v in col_val]
		vals.extend([self.player_id, self.player_guild_id, self.name])
		return sql('rpg', sql_str, vals)

	def get_next_level_exp(self):

		def exp_to_level(level):
			return int(round(.25 * floor((level - 1) + 300 * (2 ** ((level - 1) / 7))), 0))

		self.exp_to_next_level = sum([exp_to_level(i) for i in range(2, self.level + 2)])

	def calculate_stats(self):
		s = self.profession.base_str + (self.level * self.profession.str_mod)
		d = self.profession.base_dex + (self.level * self.profession.dex_mod)
		i = self.profession.base_int + (self.level * self.profession.int_mod)
		c = self.profession.base_con + (self.level * self.profession.con_mod)
		self.stats = {'STR': s, 'DEX': d, 'INT': i, 'CON': c}
		self.get_armour_bonuses()

	def get_armour_bonuses(self):
		s = 0
		d = 0
		i = 0
		c = 0
		for e in self.equipment:
			if e:
				s += e.str_bonus
				d += e.dex_bonus
				i += e.int_bonus
				c += e.con_bonus
		self.stats['STR'] += s
		self.stats['DEX'] += d
		self.stats['INT'] += i
		self.stats['CON'] += c

	def add_exp(self, exp):
		start = self.level
		while exp > 0:
			exp_to_level = self.exp_to_next_level - self.exp
			if exp >= exp_to_level:
				self.exp += exp_to_level
				self.level_up()
				exp -= exp_to_level
			else:
				self.exp += exp
				exp = 0
		return self.level > start

	def level_up(self):
		self.level += 1
		self.get_next_level_exp()
		self.calculate_stats()
		self.current_con = self.stats['CON'] * 10
		self.current_mp = self.stats['INT'] * 5

	def equip(self, equipment, slot=''):
		if equipment.type == 'Helmet':
			prev_equip = self.helmet
			self.helmet = equipment
		elif equipment.type == 'Chest':
			prev_equip = self.chest
			self.chest = equipment
		elif equipment.type == 'Legs':
			prev_equip = self.legs
			self.legs = equipment
		elif equipment.type == 'Boots':
			prev_equip = self.boots
			self.boots = equipment
		elif equipment.type == 'Gloves':
			prev_equip = self.gloves
			self.gloves = equipment
		elif equipment.type == 'Amulet':
			prev_equip = self.amulet
			self.amulet = equipment
		elif equipment.type == 'Ring':
			prev_equip = self.ring
			self.ring = equipment
		elif equipment.type in all_weapons:
			if slot == 'main':
				prev_equip = self.weapon
				self.weapon = equipment
			else:
				prev_equip = self.off_hand
				self.off_hand = equipment
		else:
			prev_equip = self.off_hand
			self.off_hand = equipment
		self.calculate_stats()
		if self.current_con > self.stats['CON'] * 10:
			self.current_con = self.stats['CON'] * 10
		if self.current_mp > self.stats['INT'] * 5:
			self.current_mp = self.stats['INT'] * 5
		self._inventory['equipment'].pop(self._inventory['equipment'].index(equipment))
		if prev_equip:
			self._inventory['equipment'].append(prev_equip)
		self.update()
		return prev_equip

	def unequip(self, slot):
		if slot == 'helmet':
			prev_equip = self.helmet
			self.helmet = None
		elif slot == 'chest':
			prev_equip = self.chest
			self.chest = None
		elif slot == 'legs':
			prev_equip = self.legs
			self.legs = None
		elif slot == 'boots':
			prev_equip = self.boots
			self.boots = None
		elif slot == 'gloves':
			prev_equip = self.gloves
			self.gloves = None
		elif slot == 'amulet':
			prev_equip = self.amulet
			self.amulet = None
		elif slot == 'ring':
			prev_equip = self.ring
			self.ring1 = None
		elif slot == 'weapon':
			prev_equip = self.weapon
			self.weapon = None
		else:
			prev_equip = self.off_hand
			self.off_hand = None
		self.calculate_stats()
		if self.current_con > self.stats['CON'] * 10:
			self.current_con = self.stats['CON'] * 10
		if self.current_mp > self.stats['INT'] * 5:
			self.current_mp = self.stats['INT'] * 5
		self._inventory['equipment'].append(prev_equip)
		self.update()
		return prev_equip

	def drink(self, potion):
		if isinstance(potion, RestorationPotion):
			if potion.type == 'Health':
				self.current_con += potion.restored
				if self.current_con > self.stats['CON'] * 10:
					self.current_con = self.stats['CON'] * 10
			else:
				self.current_mp += potion.restored
				if self.current_mp > self.stats['INT'] * 5:
					self.current_mp = self.stats['INT'] * 5
		self._inventory['consumables'].pop(self._inventory['consumables'].index(potion))
		self.update()
		return potion

	@property
	def equipment(self):
		return (
			self.helmet,
			self.chest,
			self.legs,
			self.boots,
			self.gloves,
			self.amulet,
			self.ring,
			self.weapon,
			self.off_hand
		)	

	@property
	def pages(self):
		pages = []

		# Character Overview
		splash_desc = f'**Level:** {self.level} | **EXP:** {self.exp} ({self.exp_to_next_level}){" :skull_crossbones:" if self._death_timer > dt.now() else ""}\n'
		splash_desc += f'**Current HP:** {self.current_con}/{self.stats["CON"] * 10} | **Current MP:** {self.current_mp}/{self.stats["INT"] * 5}\n'
		splash_desc += f'**Current Area:** {self.current_area.name if self.current_area else ""}\n'
		splash_desc += f'**Gold:** {self.gold}\n\n'
		splash_desc += '__**Stats**__\n'
		splash_desc += f'**STR:** {self.stats["STR"]} | **DEX:** {self.stats["DEX"]}\n'
		splash_desc += f'**INT:** {self.stats["INT"]} | **CON:** {self.stats["CON"]}\n'
		splash_desc += f'**ATK:** {round(self.atk_rating, 2)} | **DEF:** {self.armour_defense}\n\n'
		splash_desc += f'**Helmet:** {self.helmet.name if self.helmet else ""}\n'
		splash_desc += f'**Chest:** {self.chest.name if self.chest else ""}\n'
		splash_desc += f'**Legs:** {self.legs.name if self.legs else ""}\n'
		splash_desc += f'**Boots:** {self.boots.name if self.boots else ""}\n'
		splash_desc += f'**Gloves:** {self.gloves.name if self.gloves else ""}\n'
		splash_desc += f'**Amulet:** {self.amulet.name if self.amulet else ""}\n'
		splash_desc += f'**Ring:** {self.ring.name if self.ring else ""}\n'
		splash_desc += f'**Weapon:** {self.weapon.name if self.weapon else ""}\n'
		splash_desc += f'**Off Hand:** {self.off_hand.name if self.off_hand else ""}\n\n'
		splash_desc += '__**Spells**__\n'
		splash_desc += '\n'.join([s.name for s in self._spells])
		splash_page = Page(f'{self.name} - {self.profession.name}', splash_desc, colour=(150, 150, 150))
		pages.append(splash_page)

		# Equipment details
		for e in self.equipment:
			if e:
				pages.append(e.stat_page(self))

		return pages

	@property
	def armour_defense(self):
		base = sum([e.defense for e in self.equipment if isinstance(e, Armour)])
		base += sum([e.def_bonus for e in self.equipment if e])
		return base

	@property
	def armour_attack(self):
		return sum([e.atk_bonus for e in self.equipment if e])	

	@property
	def defense(self):
		return 80 / (80 + self.stats['STR'] + self.armour_defense)
	
	@property
	def damage(self):
		min_damage = 0
		max_damage = 0
		if self.weapon:
			min_damage += self.weapon.min_damage
			max_damage += self.weapon.max_damage
		if self.off_hand and self.off_hand.type in all_weapons:
			min_damage += self.off_hand.min_damage
			max_damage += self.off_hand.max_damage
		min_damage += floor(self.armour_attack / 5)
		max_damage += floor(self.armour_attack / 5)
		dmg = randint(min_damage, max_damage)
		if self.weapon:
			dmg += floor(self.stats[self.weapon.stat] / 10)
		if self.off_hand and self.off_hand.type in all_weapons:
			dmg += floor(self.stats[self.off_hand.stat] / 10)
		dmg += floor(self.stats.get(self.profession.primary_stat, 0) / 10)
		dmg += floor(self.stats.get(self.profession.secondary_stat, 0) / 20)
		if self.weapon:
			if random() < self.weapon.crit_chance:
				dmg *= 1.5
		return dmg

	@property
	def atk_rating(self):
		min_damage = 0
		max_damage = 0
		if self.weapon:
			min_damage += self.weapon.min_damage
			max_damage += self.weapon.max_damage
		if self.off_hand and self.off_hand.type in all_weapons:
			min_damage += self.off_hand.min_damage
			max_damage += self.off_hand.max_damage
		min_damage += floor(self.armour_attack / 5)
		max_damage += floor(self.armour_attack / 5)
		dmg = floor((min_damage + max_damage) / 2)
		if self.weapon:
			dmg += floor(self.stats[self.weapon.stat] / 10)
		if self.off_hand and self.off_hand.type in all_weapons:
			dmg += floor(self.stats[self.off_hand.stat] / 10)
		dmg += floor(self.stats.get(self.profession.primary_stat, 0) / 10)
		dmg += floor(self.stats.get(self.profession.secondary_stat, 0) / 20)
		if self.weapon:
			return (1 - self.weapon.crit_chance) * dmg + self.weapon.crit_chance * 1.5 * dmg
		return dmg

	def spell_damage(self, spell):
		dmg = randint(spell.min_damage + floor(self.armour_attack / 5) + floor(self.stats['INT'] / 5), spell.max_damage + floor(self.armour_attack / 5) + floor(self.stats['INT'] / 5))
		dmg += floor(self.stats[spell.stat] / 5)
		dmg += floor(self.stats.get(self.profession.primary_stat, 0) / 10)
		return dmg

	def heal(self):
		if 0 <= (dt.now() - self._death_timer).total_seconds() <= 600:
			self.current_con = self.stats['CON'] * 10
			self.current_mp = self.stats['INT'] * 5
		if self.stats['CON'] * 10 != self.current_con:
			self.current_con += self.stats['CON']
			if self.current_con > self.stats['CON'] * 10:
				self.current_con = self.stats['CON'] * 10
		if self.stats['INT'] * 5 != self.current_mp:
			self.current_mp += ceil(self.stats['INT'] / 2)
			if self.current_mp > self.stats['INT'] * 5:
				self.current_mp = self.stats['INT'] * 5
		self.update()