from discord.ext import commands
import asyncio
from . import sql, parse_args, mtgapi, query_builder
import logging
import re
import typing
from discord import Member, Embed, Colour
from string import ascii_uppercase, ascii_lowercase
from math import floor, ceil
from random import randint, choice

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

BACK = '\u2b05\ufe0f' # Left arrow
NEXT = '\u27a1\ufe0f' # Right arrow
YES = '\u2705' # white checkmark
NO = '\u274C' # Red x
PLAY = '\u2b06\ufe0f' # Up arrow

class CardCog(commands.Cog):
	
	trans = str.maketrans({u:"_"+l for u,l in zip(ascii_uppercase, ascii_lowercase)})

	def __init__(self, bot):
		self.bot = bot

	# Utilities
	# Database functions
	def query_card_from_db(self, **kwargs):
		if kwargs.get('multiverseid', None):
			df = sql('SELECT * FROM cards WHERE multiverseid = ?', (kwargs.get('multiverseid'),))
		else:
			q, vals = query_builder('SELECT * FROM cards', **kwargs)
			df = sql(q, vals)
		if df.empty:
			return None
		return self.gen_card(df.to_dict('records')[0])

	def query_cards_from_db(self, **kwargs):
		if kwargs.get('multiverseid', None):
			df = sql('SELECT * FROM cards WHERE multiverseid = ?', (kwargs.get('multiverseid'),))
		else:
			q, vals = query_builder('SELECT * FROM cards', **kwargs)
			df = sql(q, vals)
		if df.empty:
			return []
		return [self.gen_card(d) for d in df.to_dict('records')]

	def add_cards_not_in_db(self, db, api):
		cards_to_add = [c for c in api if c not in db]
		for card in cards_to_add:
			sql('INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?)', card.row)

	def add_card_not_in_db(self, card):
		if sql('SELECT * FROM cards WHERE multiverseid = ?', (card.multiverseid,)).empty:
			sql('INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?)', card.row)

	# MTGAPI functions
	def _search_cards(self, **kwargs):
		resp = mtgapi('cards', kwargs)
		if not resp.get('cards', []):
			return []
		ret = []
		for card in resp.get('cards'):
			if not 'multiverseid' in card.keys():
				continue
			try:
				ret.append(self.gen_card(card))
			except Exception as e:
				log.exception(str(e))
				continue
		return ret

	def _search_card(self, **kwargs):
		try:
			return self._search_cards(**kwargs)[0]
		except Exception as e:
			log.exception(str(e))
			return None

	def get_card(self, id):
		resp = mtgapi(f'cards/{id}')
		if not resp.get('card', None):
			return None
		return self.gen_card(resp.get('card'))

	# Card Objects
	def gen_card(self, card):
		card = {k.translate(__class__.trans): v for k, v in card.items()}
		if card.get('types', None):
			card['type'] = card.get('types')[0]
		if card.get('type') == 'Creature':
			return Creature(**card)
		return Card(**card)

	# Commands
	@commands.command(name='searchcards',
					pass_context=True,
					description='Search MTG cards',
					brief='Search cards',
					aliases=['sc'])
	async def search_cards(self, ctx, *search_str):
		await ctx.send('I am searching all my knowledge bases...')
		args = parse_args(' '.join(search_str))
		cards_from_db = self.query_cards_from_db(**args)
		cards_from_api = self._search_cards(**args)
		self.add_cards_not_in_db(cards_from_db, cards_from_api)
		cards_from_db.extend(cards_from_api)
		idx = 0
		emb = cards_from_db[idx].embed
		emb.set_footer(text=f'{idx + 1}/{len(cards_from_db)}')
		msg = await ctx.send(embed=emb)
		await msg.add_reaction(BACK)
		await msg.add_reaction(NEXT)

		def is_left_right(m):
			log.debug(m.emoji.name.encode('ascii', 'backslashreplace'))
			return all([
				(m.emoji.name == BACK or m.emoji.name == NEXT),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member.id == ctx.author.id
			])

		while True:
			try:
				react = await self.bot.wait_for('raw_reaction_add', check=is_left_right, timeout=60)
			except asyncio.TimeoutError:
				log.debug('Timeout, breaking')
				break
			if react.emoji.name == NEXT:
				idx = (idx + 1) % len(cards_from_db)
				await msg.remove_reaction(NEXT, react.member)
			else:
				idx = (idx - 1) % len(cards_from_db)
				await msg.remove_reaction(BACK, react.member)
			emb = cards_from_db[idx].embed
			emb.set_footer(text=f'{idx + 1}/{len(cards_from_db)}')
			await msg.edit(embed=emb)
		# return cards_from_db

	@commands.command(name='searchcard',
					pass_context=True,
					description='Search for a MTG card',
					brief='Search for a card',
					aliases=['s'])
	async def search_card(self, ctx, *search_str):
		log.debug(search_str)
		args = parse_args(' '.join(search_str))
		log.info(str(args))
		card = self.query_card_from_db(**args)
		if not card:
			log.debug('Didn\'t find a card in the database, searching API...')
			await ctx.send('I didn\'t find a card like that in my library, give me a moment...')
			card = self._search_card(**args)
			if card:
				log.debug('Adding card to database.')
				self.add_card_not_in_db(card)
		if card:
			return await ctx.send(embed=card.embed)
		else:
			return await ctx.send('I could not find the card you were searching for. Apologies.')

	# @commands.command(name='hand',
	# 				pass_context=True,
	# 				description='Shows the player\'s hand',
	# 				brief='Show hand',
	# 				aliases=['sh', 'h'])
	# async def show_hand(self, ctx):
	# 	if ctx.author.name != 'Zeppo':
	# 		return
	# 	ch = self.bot.get_channel(788611597244432494)
	# 	cards = self.query_cards_from_db()
	# 	emb = choice(cards).embed
	# 	emb.set_footer(text='1/7')
	# 	return await ch.send(embed=emb)




class Card:
	def __init__(self, name, cmc, rarity, type, **kwargs):
		self.name = name
		self.cmc = int(cmc)
		self.rarity = rarity
		self.type = type
		self.image_url = kwargs.get('image_url', None)
		self.multiverseid = kwargs.get('multiverseid', None)

	@property
	def embed(self):
		emb = Embed(
			description=f'**{self.type}** — {self.rarity}',
			colour=Colour.from_rgb(157, 120, 78)
		)
		emb.set_author(name=self.name)
		if self.image_url:
			emb.set_image(url=self.image_url)
		return emb

	@property
	def row(self):
		return (self.multiverseid, self.name, self.cmc, self.rarity, self.type, self.image_url, -1, -1, '')
	
	def __eq__(self, c):
		return self.multiverseid == c.multiverseid

	def __hash__(self):
		return self.multiverseid

	def __bool__(self):
		return self.multiverseid != None

class Creature(Card):
	RARITY_MULTI = {
		'Common': 1,
		'Uncommon': 1.5,
		'Rare': 2.5,
		'Mythic': 5
	}
	RARITY_DICE = {
		'Common': 4,
		'Uncommon': 6,
		'Rare': 8,
		'Mythic': 12
	}
	def __init__(self, power, toughness, subtypes, **kwargs):
		super().__init__(**kwargs)
		self.base_power = int(power)
		self.base_toughness = int(toughness)
		self.current_power = self.base_power
		self.bonus_toughness = 0
		self.hp = self.generate_health()
		self.current_hp = self.hp
		self.subtypes = subtypes if isinstance(subtypes, list) else subtypes.split(',')

	@property
	def power(self):
		return self.current_power
	
	@property
	def toughness(self):
		return self.base_toughness + self.bonus_toughness

	@property
	def ac(self):
		return (2 * self.base_toughness) + floor(self.base_power / 2) + self.bonus_toughness

	@property
	def embed(self):
		emb = Embed(
			description=f'**{self.type}** — {" ".join(self.subtypes)} — {self.rarity}\n{self.current_power}/{self.base_toughness + self.bonus_toughness}\nHP: {self.hp}\nAC: {self.ac}',
			colour=Colour.from_rgb(157, 120, 78)
		)
		emb.set_author(name=self.name)
		if self.image_url:
			emb.set_image(url=self.image_url)
		return emb

	@property
	def row(self):
		return (self.multiverseid, self.name, self.cmc, self.rarity, self.type, self.image_url, self.base_power, self.base_toughness, ','.join(self.subtypes))

	def generate_health(self):
		base_hp = self.cmc * __class__.RARITY_DICE[self.rarity] + self.base_toughness
		return ceil(base_hp * __class__.RARITY_MULTI[self.rarity])

	def damage(crit=False):
		rolls = randint(1, __class__.RARITY_DICE[self.rarity])
		if crit:
			rolls += randint(1, __class__.RARITY_DICE[self.rarity])
		return ceil((rolls + self.current_power) * __class__.RARITY_MULTI[self.rarity])

	def buff_toughness(amt):
		self.bonus_toughness += amt

	def buff_power(amt):
		self.current_power += amt

	def add_health(amt):
		self.current_hp += amt