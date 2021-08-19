from . import log, BASE_PATH, Page, MyCog, chunk, sql, format_remaining_time, BACK, NEXT
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint, choice, choices, random
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

version = '1.2.2'

def query_builder(q):
	if isinstance(q, tuple):
		q = ' '.join(q)
	if ' ' in q:
		q = f'"{q}"'
	return q

def admin_check(ctx):
	return ctx.message.author.guild_permissions.administrator

class PokeTCG(MyCog):
	def __init__(self, bot):
		self.bot = bot
		self.store = self.generate_store()
		self.date = dt.now().date()
		if not os.path.exists(f'{BASE_PATH}/poketcg.db'):
			log.info('Initialising database.')
			initialise_db()
		migrate_db(version)
		self.refresh_daily_packs.start()

	# Utilities

	def generate_store(self):
		ret = {}
		sets = Sets.get_sets()
		set_weights = [s.release_date.year - 1998 for s in sets]
		store_sets = choices(sets, weights=set_weights, k=10)
		for i, set_ in enumerate(store_sets, start=1):
			ret[i] = set_
		ret['reset'] = (dt.now() + td(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
		return ret

	def sell_cards(self, player, player_cards, keep):
		total_sold = 0
		total_cash = 0
		for player_card in player_cards:
			total_sold += player_card.amount - keep
			total_cash += player_card.price * (player_card.amount - keep)
			player_card.amount = keep
		Card.add_or_update_cards_from_player_cards(player, player_cards)
		player.cash += total_cash
		player.total_cash += total_cash
		player.cards_sold += total_sold
		player.update()
		return total_sold, total_cash

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
					brief='',
					aliases=['mc'])
	async def get_player_cards(self, ctx, sort_by: typing.Optional[str] = 'name'):
		player = Player.get_player(ctx.author.id)
		player_cards = Card.get_player_cards(player)
		if not player_cards:
			return await ctx.send('You have no cards')
		sort_by = 'name' if sort_by not in ['id', 'amount', 'price', 'name'] else sort_by
		if sort_by == 'id':
			player_cards.sort(key=lambda x: x.id)
		elif sort_by == 'price':
			player_cards.sort(key=lambda x: x.price, reverse=True)
		elif sort_by == 'name':
			player_cards.sort(key=lambda x: x.name)
		else:
			player_cards.sort(key=lambda x: x.amount, reverse=True)
		return await self.paginated_embeds(ctx, [pc.page for pc in player_cards])

	@commands.group(name='sell',
					pass_context=True,
					invoke_without_command=True,
					description='',
					brief='')
	async def sell_main(self, ctx):
		msg = 'Here are the available selling commands:\n'
		msg += '**.sell card <card id> [amount - Default: _1_]** to sell a specific card.\n'
		msg += '**.sell under [value - Default: _1.00_] [rares - Default: _false_]** to sell all cards worth less than the value entered.\n'
		msg += '**.sell dups [rares - Default: _false_]** to sell all duplicate cards until 1 remains. Doesn\'t sell rares by default.\n'
		msg += '**.sell all [rares - Default: _false_]** to sell all cards. Doesn\'t sell rares by default.'
		return await ctx.send(msg)

	@sell_main.command(name='card',
					pass_context=True,
					description='',
					brief='')
	async def sell_card(self, ctx, card_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		player_card = Card.get_player_card(player, card_id)
		if not player_card:
			return await ctx.send('You don\'t have a card with that ID \\:(')
		amt = 1 if amt < 1 else amt
		sold = min(amt, player_card.amount)
		player_card.amount -= sold
		player.cards_sold += sold
		player.cash += player_card.price * sold
		player.total_cash += player_card.price * sold
		await ctx.send(f'You sold {sold} **{player_card.name}** for ${player_card.price * sold:.2f}')
		player.update()
		player_card.update()

	@sell_main.command(name='under',
					pass_context=True,
					description='',
					brief='')
	async def sell_under(self, ctx, value: typing.Optional[float] = 1.00, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		value = 0.00 if value < 0 else value
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		player_cards = Card.get_player_cards(player)
		cards_to_sell = [c for c in player_cards if c.price < value]
		if rares == 'false':
			cards_to_sell = [c for c in cards_to_sell if c.rarity in ['Common', 'Uncommon']]
		total_sold, total_cash = self.sell_cards(player, cards_to_sell, 0)
		return await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')

	@sell_main.command(name='dups',
					pass_context=True,
					description='',
					brief='')
	async def sell_dups(self, ctx, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		player_cards = Card.get_player_cards(player)
		cards_to_sell = [c for c in player_cards if c.amount > 1]
		if rares == 'false':
			cards_to_sell = [c for c in cards_to_sell if c.rarity in ['Common', 'Uncommon']]
		total_sold, total_cash = self.sell_cards(player, cards_to_sell, 1)
		return await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')

	@sell_main.command(name='all',
					pass_context=True,
					description='',
					brief='')
	async def sell_all(self, ctx, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		cards_to_sell = Card.get_player_cards(player)
		if rares == 'false':
			cards_to_sell = [c for c in cards_to_sell if c.rarity in ['Common', 'Uncommon']]
		total_sold, total_cash = self.sell_cards(player, cards_to_sell, 0)
		return await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')

	@commands.command(name='search',
					pass_context=True,
					description='',
					brief='')
	async def search_cards(self, ctx, *query):
		query = ' '.join(query) if isinstance(query, tuple) else query
		cards = Card.get_cards_with_query(query)
		if not cards:
			msg = 'I couldn\'t find any cards, perhaps try using the following resources:\n'
			msg += '**Basic searching:** https://pokemontcg.guru/\n'
			msg += '**Advanced searching:** https://pokemontcg.guru/advanced\n'
			msg += '**Searching syntax:** http://www.lucenetutorial.com/lucene-query-syntax.html'
			return await ctx.send(msg)
		return await self.paginated_embeds(ctx, [c.page for c in cards])

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
		player = Player.get_player(ctx.author.id)
		desc = f'You have **{player.daily_packs}** packs left to open today\n'
		desc += 'Use **.openpack <set_id> (amount)** to open packs\n'
		for set_id, amount in player.packs.items():
			desc += f'**{set_id}** - {amount}\n'
		return await self.paginated_embeds(ctx, Page('Your packs', desc))

	@commands.command(name='openpack',
					pass_context=True,
					description='',
					brief='',
					aliases=['op'])
	async def open_pack(self, ctx, set_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		if player.daily_packs == 0:
			return await ctx.send('You\'re out of packs for today!')
		set_id = set_id.lower()
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_id not in player.packs:
			return await ctx.send(f"Looks like you don't have any **{set_.name}** packs.")
		amt = 1 if amt < 1 else amt
		opened = min(amt, player.packs[set_id], player.daily_packs)
		pack = Packs.generate_packs(set_.id, opened)
		Card.add_or_update_cards_from_pack(player, pack)
		player.daily_packs -= opened
		player.packs[set_id] -= opened
		if player.packs[set_id] == 0:
			del player.packs[set_id]
		player.packs_opened += opened
		player.total_cards += len(pack)
		player.update()
		return await self.paginated_embeds(ctx, pack.pages)

	## store
	@commands.command(name='store',
					pass_context=True,
					description='',
					brief='')
	async def card_store(self, ctx, slot: typing.Optional[int] = 0, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		slot = slot if 1 <= slot <= 10 else 0
		if not self.store:
			self.store = self.generate_store()
		if self.store.get('reset') < dt.now():
			self.store = self.generate_store()
		if slot:
			if slot <= 4:
				price_mult = 1
				pack_count = 1
				promo_count = 0
			elif 5 <= slot <= 7:
				price_mult = 2.5
				pack_count = 4
				promo_count = 1
			elif 8 <= slot <= 9:
				price_mult = 10
				pack_count = 12
				promo_count = 1
			else:
				price_mult = 30
				pack_count = 36
				promo_count = 0
			s = self.store.get(slot)
			if player.cash < s.pack_price * price_mult:
				return await ctx.send(f'You don\'t have enough... You need **${s.pack_price * price_mult - player.cash:.2f}** more.')
			bought = 0
			promos = []
			if promo_count:
				cards = Card.get_cards_with_query(f'set.id:{s.id} -rarity:common AND -rarity:uncommon')
			else:
				cards = []
			while player.cash >= s.pack_price * price_mult and bought < amt:
				player.cash -= s.pack_price * price_mult
				bought += 1
				if promo_count:
					promos.append(choice(cards))
			if s.id not in player.packs:
				player.packs[s.id] = 0
			player.packs[s.id] += bought * pack_count
			player.total_cards += len(promos)
			player.update()
			await ctx.send(f'You bought {bought} **{s.name}** packs!')
			if promos:
				Card.add_or_update_cards_from_pack(player, Packs.Pack(s.id, promos))
				return await self.paginated_embeds(ctx, [p.page for p in promos])
			return
		header = 'Welcome to the Card Store! Here you can spend cash for Packs of cards\n'
		header += f'You have **${player.cash:.2f}**\n'
		header += 'Here are the packs available today. To purchasae one, use **.store <slot no.> (amount)**\n\n'
		set_list = [(i, s) for i, s in self.store.items() if i != 'reset']
		set_list.sort(key=lambda x: x[0])
		desc = ''
		for i, s in set_list:
			if i <= 4:
				type_ = 'Pack'
				price_mult = 1
			elif 5 <= i <= 7:
				type_ = 'Collection'
				price_mult = 2.5
			elif 8 <= i <= 9:
				type_ = 'Trainer Box'
				price_mult = 10
			else:
				type_ = 'Booster Box'
				price_mult = 30
			desc += f'**{i}:** {s.name} {type_} (_{s.id}_) - ${s.pack_price * price_mult:.2f}\n'
		page = Page('Card Store - Booster Boxes', f'{header}\n{desc}', footer=f'Resets in {format_remaining_time(self.store.get("reset"))}')
		return await self.paginated_embeds(ctx, page)

	## player
	@commands.command(name='stats',
					pass_context=True,
					description='',
					brief='')
	async def player_stats(self, ctx):
		player = Player.get_player(ctx.author.id)
		return await self.paginated_embeds(ctx, Page(ctx.author.display_name, player.stats_desc))

	## claimables
	@commands.command(name='daily',
					pass_context=True,
					description='',
					brief='')
	async def daily(self, ctx):
		player = Player.get_player(ctx.author.id)
		if player.daily_reset > dt.now():
			return await ctx.send(f'Your next daily reward is in **{format_remaining_time(player.daily_reset)}**')
		if random() < .1:
			set_ = choice(Sets.get_sets())
			if s.id not in player.packs:
				player.packs[s.id] = 0
			player.packs[s.id] += 1
			await ctx.send(f'You got a{"n" if s.name[0] in "aeiou" else ""} **{s.name}** pack!')
		else:
			cash = randint(1, 10)
			player.cash += cash
			player.total_cash += cash
			await ctx.send(f'You got **${cash:.2f}**!')
		player.daily_reset = dt.now() + td(days=1)
		return player.update()

	# Tasks
	@tasks.loop(seconds=60)
	async def refresh_daily_packs(self):
		if self.date < dt.now().date():
			log.info('Refreshing daily packs')
			sql('poketcg', 'update players set daily_packs = 50')

	# Test Functions

	@commands.command(name='testpack',
					pass_context=True,
					description='',
					brief='')
	@commands.check(admin_check)
	async def test_pack(self, ctx, set_id):
		pack = packs.Pack.from_set(set_id)
		return await self.paginated_embeds(ctx, pack.pages)

	@commands.command(name='addcash',
					pass_context=True,
					description='',
					brief='')
	@commands.check(admin_check)
	async def add_cash(self, ctx, amt: typing.Optional[int] = 100):
		player = Player.get_player(ctx.author.id)
		player.cash += amt
		player.total_cash += amt
		await ctx.send(f'{ctx.author.display_name} now has **${player.cash:.2f}**')
		return player.update()