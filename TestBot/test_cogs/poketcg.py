from . import log, BASE_PATH, Page, MyCog, chunk, sql, format_remaining_time, BACK, NEXT
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint, choice, choices
import typing
import os.path
from datetime import datetime as dt, timedelta as td
import json
import re

from .poketcgFunctions import api_call
from .poketcgFunctions import card as Card
from .poketcgFunctions import sets as Sets
from .poketcgFunctions import packs as Packs
from .poketcgFunctions import player as Player
from .poketcgFunctions.database import initialise_db, migrate_db

version = '0.0.0'

def query_builder(q):
	if isinstance(q, tuple):
		q = ' '.join(q)
	if ' ' in q:
		q = f'"{q}"'
	return q

class PokeTCG(MyCog):
	def __init__(self, bot):
		self.bot = bot
		self.store = self.generate_store()
		if not os.path.exists(f'{BASE_PATH}/poketcg.db'):
			log.info('Initialising database.')
			initialise_db()

	# Utilities

	def generate_store(self):
		ret = {}
		sets = Sets.get_sets()
		store_sets =[]
		while len(store_sets) < 5:
			s = choice(sets)
			if s in store_sets:
				s = choice(sets)
			store_sets.append(s)
		for i, s in enumerate(store_sets, start=1):
			ret[i] = s
		ret['reset'] = (dt.now() + td(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
		return ret

	# Commands
	## cards
	@commands.command(name='cards',
					pass_context=True,
					description='',
					brief='')
	async def get_cards(self, ctx, *name):
		cards = Card.get_cards_with_query(f'name:{query_builder(name)}')
		return await self.paginated_embeds(ctx, [c.page for c in cards])

	@commands.command(name='card',
					pass_context=True,
					description='',
					brief='')
	async def get_card(self, ctx, card_id):
		card = Card.get_card_by_id(card_id)
		if card is None:
			return await ctx.send('I couldn\'t find a card with that ID \\:(')
		return await self.paginated_embeds(ctx, card.page)

	@commands.command(name='mycards',
					pass_context=True,
					description='',
					brief='')
	async def get_player_cards(self, ctx):
		...

	## sets
	@commands.command(name='sets',
					pass_context=True,
					description='',
					brief='')
	async def get_sets(self, ctx):
		sets = Sets.get_sets()
		sets.sort(key=lambda x: x.name)
		pages = []
		for set_chunk in chunk(sets, 15):
			desc = '\n'.join([str(s) for s in set_chunk])
			pages.append(Page('Sets', desc))
		await self.paginated_embeds(ctx, pages)

	@commands.command(name='set',
					pass_context=True,
					description='',
					brief='')
	async def get_set(self, ctx, set_id):
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		return await self.paginated_embeds(ctx, set_.page)

	## packs
	@commands.command(name='packs',
					pass_context=True,
					description='',
					brief='')
	async def get_player_packs(self, ctx):
		...

	@commands.command(name='openpack',
					pass_context=True,
					description='',
					brief='')
	async def open_pack(self, ctx, set_id):
		...

	## store
	@commands.command(name='store',
					pass_context=True,
					description='',
					brief='')
	async def card_store(self, ctx, slot: typing.Optional[int] = 0, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		slot = slot if 1 <= slot <= 5 else 0
		if not self.store:
			self.store = self.generate_store()
		if self.store.get('reset') < dt.now():
			self.store = self.generate_store()
		if slot:
			# buying pack code
			...
		desc = 'Welcome to the Card Store! Here you can spend cash for Packs of cards\n'
		desc += f'You have **${player.cash}**\n'
		desc += 'Here are the packs available today. To purchasae one, use **.store <slot no.>**\n\n'
		set_list = [(i, s) for i, s in self.store.items() if i != 'reset']
		set_list.sort(key=lambda x: x[0])
		for i, s in set_list:
			desc += f'**{i}:** {s.name} (_{s.id}_) - ${s.pack_price:.2f}\n'
		page = Page('Card Store', desc, footer=f'Resets in {format_remaining_time(self.store.get("reset"))}')
		return await self.paginated_embeds(ctx, page)

	## player
	@commands.command(name='stats',
					pass_context=True,
					description='',
					brief='')
	async def player_stats(self, ctx):
		...

	@commands.command(name='options',
					pass_context=True,
					description='',
					brief='')
	async def player_options(self, ctx):
		...

	## claimables
	@commands.command(name='daily',
					pass_context=True,
					description='',
					brief='')
	async def daily(self, ctx):
		...


	@commands.command(name='testpack',
					pass_context=True,
					description='',
					brief='')
	async def test_pack(self, ctx, set_id):
		pack = packs.Pack.from_set(set_id)
		return await self.paginated_embeds(ctx, pack.pages)