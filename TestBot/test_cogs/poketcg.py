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
from .poketcgFunctions import card
from .poketcgFunctions import sets
from .poketcgFunctions import packs
from .poketcgFunctions import player
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
		self.store = None
		if not os.path.exists(f'{BASE_PATH}/poketcg.db'):
			log.info('Initialising database.')
			initialise_db()

	# Utilities

	def generate_store(self):
		...

	# Commands
	## cards
	@commands.command(name='cards',
					pass_context=True,
					description='',
					brief='')
	async def get_cards(self, ctx, *name):
		cards = card.get_cards_with_query(f'name:{query_builder(name)}')
		return await self.paginated_embeds(ctx, [c.page for c in cards])

	@commands.command(name='card',
					pass_context=True,
					description='',
					brief='')
	async def get_card(self, ctx, card_id):
		card_ = card.get_card_by_id(card_id)
		if card_ is None:
			return await ctx.send('I couldn\'t find a card with that ID \\:(')
		return await self.paginated_embeds(ctx, card_.page)

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
		sets_ = sets.get_sets()
		sets_.sort(key=lambda x: x.name)
		pages = []
		for set_chunk in chunk(sets_, 15):
			desc = '\n'.join([str(s) for s in set_chunk])
			pages.append(Page('Sets', desc))
		await self.paginated_embeds(ctx, pages)

	@commands.command(name='set',
					pass_context=True,
					description='',
					brief='')
	async def get_set(self, ctx, set_id):
		set_ = sets.get_set(set_id)
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
		...

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