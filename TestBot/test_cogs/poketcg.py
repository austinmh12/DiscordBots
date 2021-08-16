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

version = '1.0.0'

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
		if not os.path.exists(f'{BASE_PATH}/poketcg.db'):
			log.info('Initialising database.')
			initialise_db()
		migrate_db(version)

	# Utilities

	def generate_store(self):
		ret = {}
		sets = Sets.get_sets()
		store_sets =[]
		store_collections = []
		store_trainers = []
		store_boosters = []
		while len(store_sets) < 5:
			s = choice(sets)
			if s in store_sets:
				s = choice(sets)
			store_sets.append(s)
		while len(store_collections) < 5:
			s = choice(sets)
			if s in store_collections:
				s = choice(sets)
			store_collections.append(s)
		while len(store_trainers) < 5:
			s = choice(sets)
			if s in store_trainers:
				s = choice(sets)
			store_trainers.append(s)
		while len(store_boosters) < 5:
			s = choice(sets)
			if s in store_boosters:
				s = choice(sets)
			store_boosters.append(s)
		for i, s in enumerate(store_sets, start=1):
			ret[i] = s
		for i, s in enumerate(store_collections, start=6):
			ret[i] = s
		for i, s in enumerate(store_trainers, start=11):
			ret[i] = s
		for i, s in enumerate(store_boosters, start=16):
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
					brief='',
					aliases=['mc'])
	async def get_player_cards(self, ctx, sort_by: typing.Optional[str] = 'id'):
		player = Player.get_player(ctx.author.id)
		player_cards = Card.get_player_cards(player)
		if not player_cards:
			return await ctx.send('You have no cards')
		sort_by = 'id' if sort_by not in ['id', 'amount', 'price'] else sort_by
		if sort_by == 'id':
			player_cards.sort(key=lambda x: x.card)
		if sort_by == 'price':
			q = ' OR '.join([f'id:{p.card}' for p in player_cards])
			cards = Card.get_cards_with_query(f'({q})')
			log.debug(len(cards))
			cards.sort(key=lambda x: x.price, reverse=True)
			card_ids = {c.id: cards.index(c) for c in cards}
			player_cards.sort(key=lambda x: card_ids.get(x.card, 999))
		else:
			player_cards.sort(key=lambda x: x.amount, reverse=True)
		idx = 0
		page = Card.get_card_by_id(player_cards[idx].card).page
		page.desc += f'Owned: {player_cards[idx].amount}'
		if len(player_cards) > 1:
			page.footer = f'{idx + 1}/{len(player_cards)}'
		msg = await ctx.send(embed=page.embed)
		if len(player_cards) > 1:
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

		def is_left_right(m):
			return all([
				m.emoji.name in [BACK, NEXT],
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		while True:
			try:
				react = await self.bot.wait_for('raw_reaction_add', check=is_left_right, timeout=60)
			except asyncio.TimeoutError:
				log.debug('Timeout, breaking')
				await msg.clear_reactions()
				break
			if react.emoji.name == NEXT:
				await msg.remove_reaction(NEXT, react.member)
				idx = (idx + 1) % len(player_cards)
			else:
				await msg.remove_reaction(BACK, react.member)
				idx = (idx - 1) % len(player_cards)
			page = Card.get_card_by_id(player_cards[idx].card).page
			page.desc += f'**Owned:** {player_cards[idx].amount}'
			if len(player_cards) > 1:
				page.footer = f'{idx + 1}/{len(player_cards)}'
			await msg.edit(embed=page.embed)

	@commands.group(name='sell',
					pass_context=True,
					invoke_without_command=True,
					description='',
					brief='')
	async def sell_main(self, ctx):
		msg = 'Here are the available selling commands:\n'
		msg += '**.sell card <card id> [amount - Default: _1_]** to sell a specific card.\n'
		msg += '**.sell under [value - Default: _1.00_]** to sell all cards worth less than the value entered.\n'
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
		card = Card.get_card_by_id(player_card.card)
		sold = min(amt, player_card.amount)
		player_card.amount -= sold
		player.cards_sold += sold
		player.cash += card.price * sold
		player.total_cash += card.price * sold
		await ctx.send(f'You sold {sold} **{card.name}** for ${card.price * sold:.2f}')
		player.update()
		player_card.update()

	@sell_main.command(name='under',
					pass_context=True,
					description='',
					brief='')
	async def sell_under(self, ctx, value: typing.Optional[float] = 1.00):
		player = Player.get_player(ctx.author.id)
		value = 0.00 if value < 0 else value
		player_cards = Card.get_player_cards(player)
		q = ' OR '.join([f'id:{pc.card}' for pc in player_cards])
		cards = Card.get_cards_with_query(f'({q})')
		card_ids = {c.id: c.price for c in cards}
		cards_to_sell = [c for c in player_cards if card_ids.get(c.card) < value]
		total_sold = 0
		total_cash = 0
		for player_card in cards_to_sell:
			total_sold += player_card.amount
			total_cash += card_ids.get(player_card.card) * player_card.amount
			player_card.amount = 0
		Card.add_or_update_cards_from_player_cards(player, cards_to_sell)
		player.cash += total_cash
		player.total_cash += total_cash
		player.cards_sold += total_sold
		await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')
		return player.update()

	@sell_main.command(name='dups',
					pass_context=True,
					description='',
					brief='')
	async def sell_dups(self, ctx, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		player_cards = Card.get_player_cards(player)
		q = ' OR '.join([f'id:{pc.card}' for pc in player_cards])
		cards = Card.get_cards_with_query(f'({q})')
		card_ids = {c.id: c for c in cards}
		cards_to_sell = [c for c in player_cards if c.amount > 1]
		total_sold = 0
		total_cash = 0
		for player_card in cards_to_sell:
			if rares == 'false' and card_ids.get(player_card.card).rarity not in ['Common', 'Uncommon']:
				continue
			total_sold += player_card.amount - 1
			total_cash += card_ids.get(player_card.card).price * (player_card.amount - 1)
			player_card.amount = 1
		Card.add_or_update_cards_from_player_cards(player, cards_to_sell)
		player.cash += total_cash
		player.total_cash += total_cash
		player.cards_sold += total_sold
		await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')
		return player.update()

	@sell_main.command(name='all',
					pass_context=True,
					description='',
					brief='')
	async def sell_all(self, ctx, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		player_cards = Card.get_player_cards(player)
		q = ' OR '.join([f'id:{pc.card}' for pc in player_cards])
		cards = Card.get_cards_with_query(f'({q})')
		card_ids = {c.id: c for c in cards}
		total_sold = 0
		total_cash = 0
		for player_card in player_cards:
			if rares == 'false' and card_ids.get(player_card.card).rarity not in ['Common', 'Uncommon']:
				continue
			total_sold += player_card.amount
			total_cash += card_ids.get(player_card.card).price * player_card.amount
			player_card.amount = 0
		Card.add_or_update_cards_from_player_cards(player, player_cards)
		player.cash += total_cash
		player.total_cash += total_cash
		player.cards_sold += total_sold
		await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')
		return player.update()

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
		desc = 'Use **.openpack <set_id> (amount)** to open packs\n'
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
		set_id = set_id.lower()
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_id not in player.packs:
			return await ctx.send(f"Looks like you don't have any **{set_.name}** packs.")
		amt = 1 if amt < 1 else amt
		opened = min(amt, player.packs[set_id])
		pack = Packs.generate_packs(set_.id, opened)
		Card.add_or_update_cards_from_pack(player, pack)
		player.packs[set_id] -= opened
		if player.packs[set_id] == 0:
			del player.packs[set_id]
		player.packs_opened += opened
		player.total_cards += len(pack)
		player.update()
		return await self.paginated_embeds(ctx, pack.pages)

	## boxes
	@commands.command(name='boosterboxes',
					pass_context=True,
					description='',
					brief='')
	async def get_player_boosters(self, ctx):
		player = Player.get_player(ctx.author.id)
		desc = 'Use **.openbooster <set_id> (amount)** to open booster boxes\n'
		for set_id, amount in player.boosters.items():
			desc += f'**{set_id}** - {amount}\n'
		return await self.paginated_embeds(ctx, Page('Your Booster Boxes', desc))

	@commands.command(name='openbooster',
					pass_context=True,
					description='',
					brief='',
					aliases=['ob'])
	async def open_booster(self, ctx, set_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		set_id = set_id.lower()
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_id not in player.trainers:
			return await ctx.send(f"Looks like you don't have any **{set_.name}** booster boxes.")
		amt = 1 if amt < 1 else amt
		opened = min(amt, player.trainers[set_id])
		pack = Packs.generate_boosters(set_.id, opened)
		Card.add_or_update_cards_from_pack(player, pack)
		player.trainers[set_id] -= opened
		if player.trainers[set_id] == 0:
			del player.trainers[set_id]
		player.packs_opened += opened * 36
		player.total_cards += len(pack)
		player.update()
		return await self.paginated_embeds(ctx, pack.pages)

	@commands.command(name='trainerboxes',
					pass_context=True,
					description='',
					brief='')
	async def get_player_trainers(self, ctx):
		player = Player.get_player(ctx.author.id)
		desc = 'Use **.opentrainer <set_id> (amount)** to open trainer boxes\n'
		for set_id, amount in player.trainers.items():
			desc += f'**{set_id}** - {amount}\n'
		return await self.paginated_embeds(ctx, Page('Your Trainer Boxes', desc))

	@commands.command(name='opentrainer',
					pass_context=True,
					description='',
					brief='',
					aliases=['ot'])
	async def open_trainer(self, ctx, set_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		set_id = set_id.lower()
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_id not in player.trainers:
			return await ctx.send(f"Looks like you don't have any **{set_.name}** trainer boxes.")
		amt = 1 if amt < 1 else amt
		opened = min(amt, player.trainers[set_id])
		pack = Packs.generate_trainers(set_.id, opened)
		Card.add_or_update_cards_from_pack(player, pack)
		player.trainers[set_id] -= opened
		if player.trainers[set_id] == 0:
			del player.trainers[set_id]
		player.packs_opened += opened * 12
		player.total_cards += len(pack)
		player.update()
		return await self.paginated_embeds(ctx, pack.pages)

	@commands.command(name='collections',
					pass_context=True,
					description='',
					brief='')
	async def get_player_collections(self, ctx):
		player = Player.get_player(ctx.author.id)
		desc = 'Use **.opencollection <set_id> (amount)** to open collections\n'
		for set_id, amount in player.collections.items():
			desc += f'**{set_id}** - {amount}\n'
		return await self.paginated_embeds(ctx, Page('Your Collections', desc))

	@commands.command(name='opencollection',
					pass_context=True,
					description='',
					brief='',
					aliases=['oc'])
	async def open_collection(self, ctx, set_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		set_id = set_id.lower()
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_id not in player.collections:
			return await ctx.send(f"Looks like you don't have any **{set_.name}** collections.")
		amt = 1 if amt < 1 else amt
		opened = min(amt, player.collections[set_id])
		pack = Packs.generate_collections(set_.id, opened)
		Card.add_or_update_cards_from_pack(player, pack)
		player.collections[set_id] -= opened
		if player.collections[set_id] == 0:
			del player.collections[set_id]
		player.packs_opened += opened * 4
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
		slot = slot if 1 <= slot <= 20 else 0
		if not self.store:
			self.store = self.generate_store()
		if self.store.get('reset') < dt.now():
			self.store = self.generate_store()
		if slot:
			if 6 <= slot <= 10:
				price_mult = 2.5
			elif 11 <= slot <= 15:
				price_mult = 10
			elif 16 <= slot <= 20:
				price_mult = 30
			else:
				price_mult = 1
			s = self.store.get(slot)
			if player.cash < s.pack_price * price_mult:
				return await ctx.send(f'You don\'t have enough... You need **${s.pack_price * price_mult - player.cash:.2f}** more.')
			bought = 0
			while player.cash >= s.pack_price * price_mult and bought < amt:
				player.cash -= s.pack_price * price_mult
				bought += 1
			if 6 <= slot <= 10:
				if s.id not in player.collections:
					player.collections[s.id] = 0
				player.collections[s.id] += bought
				player.collections_bought += bought
			elif 11 <= slot <= 15:
				if s.id not in player.trainers:
					player.trainers[s.id] = 0
				player.trainers[s.id] += bought
				player.trainers_bought += bought
			elif 16 <= slot <= 20:
				if s.id not in player.boosters:
					player.boosters[s.id] = 0
				player.boosters[s.id] += bought
				player.boosters_bought += bought
			else:
				if s.id not in player.packs:
					player.packs[s.id] = 0
				player.packs[s.id] += bought
				player.packs_bought += bought
			if 6 <= slot <= 10:
				type_ = 'collections'
			elif 11 <= slot <= 15:
				type_ = 'trainer boxes'
			elif 16 <= slot <= 20:
				type_ = 'booster boxes'
			else:
				type_ = 'packs'
			await ctx.send(f'You bought {bought} **{s.name}** {type_}!')
			return player.update()
		header = 'Welcome to the Card Store! Here you can spend cash for Packs of cards\n'
		header += f'You have **${player.cash:.2f}**\n'
		header += 'Here are the packs available today. To purchasae one, use **.store <slot no.> (amount)**\n\n'
		set_list = [(i, s) for i, s in self.store.items() if i != 'reset']
		set_list.sort(key=lambda x: x[0])
		pages = []
		desc = ''
		for i, s in set_list[:5]:
			desc += f'**{i}:** {s.name} (_{s.id}_) - ${s.pack_price:.2f}\n'
		page = Page('Card Store - Packs', f'{header}\n{desc}', footer=f'Resets in {format_remaining_time(self.store.get("reset"))}')
		pages.append(page)
		desc = ''
		for i, s in set_list[5:10]:
			desc += f'**{i}:** {s.name} (_{s.id}_) - ${s.pack_price * 2.5:.2f}\n'
		page = Page('Card Store - Collections', f'{header}\n{desc}', footer=f'Resets in {format_remaining_time(self.store.get("reset"))}')
		pages.append(page)
		desc = ''
		for i, s in set_list[10:15]:
			desc += f'**{i}:** {s.name} (_{s.id}_) - ${s.pack_price * 10:.2f}\n'
		page = Page('Card Store - Trainer Boxes', f'{header}\n{desc}', footer=f'Resets in {format_remaining_time(self.store.get("reset"))}')
		pages.append(page)
		desc = ''
		for i, s in set_list[15:]:
			desc += f'**{i}:** {s.name} (_{s.id}_) - ${s.pack_price * 30:.2f}\n'
		page = Page('Card Store - Booster Boxes', f'{header}\n{desc}', footer=f'Resets in {format_remaining_time(self.store.get("reset"))}')
		pages.append(page)
		return await self.paginated_embeds(ctx, pages)

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