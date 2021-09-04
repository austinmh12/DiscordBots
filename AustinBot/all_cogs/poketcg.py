from . import log, BASE_PATH, Page, MyCog, chunk, sql, format_remaining_time, BACK, NEXT
from discord import File, Member
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
from .poketcgFunctions import quiz as Quiz

version = '1.4.0'
SAVE = '\U0001f4be' # 879127873116577823
REMOVE = '\u274c'

def query_builder(q):
	if isinstance(q, tuple):
		q = ' '.join(q)
	if ' ' in q:
		q = f'"{q}"'
	return q

def admin_check(ctx):
	return ctx.message.author.guild_permissions.administrator

def austin_check(ctx):
	return ctx.message.author.id == 223616191246106624

class PokeTCG(MyCog):
	def __init__(self, bot):
		self.bot = bot
		self.cache = {}
		self.cached_store_packs = 0
		self.player_card_chunks = Card.get_player_card_count() // 250 + 1
		self.cached_player_card_chunks = 0
		self.store = self.generate_store()
		self.date = dt.now().date()
		if not os.path.exists(f'{BASE_PATH}/poketcg.db'):
			log.info('Initialising database.')
			initialise_db()
		migrate_db(version)
		self.refresh_daily_packs.start()
		self.cache_store_packs.start()
		self.cache_player_cards.start()

	## Version of paginated embeds that takes cards
	async def card_paginated_embeds(self, ctx, player, cards, content=''):
		added = False
		idx = 0
		content = ''
		emb = cards[idx].page.embed
		if len(cards) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(cards)}')
		msg = await ctx.send(content, embed=emb)
		if len(cards) > 1:
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

			def is_left_right_add_remove(m):
				return all([
					(m.emoji.name in [BACK, NEXT, SAVE, REMOVE]),
					m.user_id != self.bot.user.id,
					m.message_id == msg.id,
					m.user_id == ctx.author.id
				])

			while True:
				if cards[idx].id in player.savelist:
					await msg.remove_reaction(SAVE, self.bot.user)
					await msg.add_reaction(REMOVE)
				else:
					await msg.remove_reaction(REMOVE, self.bot.user)
					await msg.add_reaction(SAVE)
				try:
					if added:
						react = await self.bot.wait_for('raw_reaction_remove', check=is_left_right_add_remove, timeout=60)
						added = False
					else:
						react = await self.bot.wait_for('raw_reaction_add', check=is_left_right_add_remove, timeout=60)
						added = True
				except asyncio.TimeoutError:
					await msg.clear_reactions()
					break
				if react.emoji.name == NEXT:
					idx = (idx + 1) % len(cards)
				elif react.emoji.name == SAVE:
					await msg.clear_reaction(SAVE)
					content = f'**{cards[idx].name}** added to your savelist'
					player.savelist.append(cards[idx].id)
					player.savelist = list(set(player.savelist))
					player.update()
				elif react.emoji.name == REMOVE:
					await msg.clear_reaction(REMOVE)
					content = f'**{cards[idx].name}** removed from your savelist'
					player.savelist.remove(cards[idx].id)
					player.update()
				else:
					idx = (idx - 1) % len(cards)
				emb = cards[idx].page.embed
				emb.set_footer(text=f'{idx + 1}/{len(cards)}')
				await msg.edit(content=content, embed=emb)

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

	def parse_trade_offer_str(self, trade_offer, is_card=True):
		if is_card:
			return self._parse_trade_offer_str_card(trade_offer)
		else:
			return self._parse_trade_offer_str_pack(trade_offer)

	def _parse_trade_offer_str_card(self, trade_offer):
		ret = []
		offers = trade_offer.split('/')
		card_ids = {}
		for offer in offers:
			if ':' in offer:
				card_id, amount = offer.split(':')
				amount = int(amount)
			else:
				card_id = offer
				amount = 1
			log.debug((card_id, amount))
			card = self.cache.get(card_id, None)
			if card:
				ret.append((card, amount))
			else:
				card_ids[card_id.lower()] = amount
		if card_ids:
			q = ' OR '.join([f'id:{card_id}' for card_id in card_ids])
			cards = Card.get_cards_with_query(q)
			for card in cards:
				ret.append((card, card_ids.get(card.id.lower())))
		return ret

	def _parse_trade_offer_str_pack(self, trade_offer):
		ret = []
		offers = trade_offer.split('/')
		set_ids = {}
		for offer in offers:
			if ':' in offer:
				set_id, amount = offer.split(':')
				amount = int(amount)
			else:
				set_id = offer
				amount = 1
			set_ = Sets.get_set(set_id)
			if not set_:
				continue
			ret.append((set_, amount))
		return ret

	# Commands
	## Cards
	@commands.command(name='mycards',
					pass_context=True,
					description='Displays all of your cards',
					brief='Your cards',
					aliases=['mc'],
					usage='[sort_by - Default: name]')
	async def get_player_cards(self, ctx, sort_by: typing.Optional[str] = 'name'):
		player = Player.get_player(ctx.author.id)
		player_cards = Card.get_player_cards(player, self.cache)
		if not player_cards:
			return await ctx.send('You have no cards')
		sort_by = 'name' if not re.match('-?(id|name|amount|price|savelist|rarity)', sort_by) else sort_by
		# sort_by = 'name' if sort_by not in ['id', 'amount', 'price', 'name'] else sort_by
		if 'id' in sort_by:
			player_cards.sort(key=lambda x: x.id, reverse='-' in sort_by)
		elif 'price' in sort_by:
			player_cards.sort(key=lambda x: x.price, reverse=not '-' in sort_by)
		elif 'name' in sort_by:
			player_cards.sort(key=lambda x: x.name, reverse='-' in sort_by)
		elif 'amount' in sort_by:
			player_cards.sort(key=lambda x: x.amount, reverse=not '-' in sort_by)
		elif 'savelist' in sort_by:
			if '-' in sort_by:
				player_cards = [pc for pc in player_cards if pc.card.id not in player.savelist]
			else:
				player_cards = [pc for pc in player_cards if pc.card.id in player.savelist]
			player_cards.sort(key=lambda x: x.name)
		elif 'rarity' in sort_by:
			player_cards.sort(key=lambda x: Packs.rarity_mapping.get(x.rarity, 100), reverse='-' in sort_by)
		else:
			return
		return await self.card_paginated_embeds(ctx, player, player_cards)

	@commands.group(name='sell',
					pass_context=True,
					invoke_without_command=True,
					description='Lets you sell your cards',
					brief='Sell cards')
	async def sell_main(self, ctx):
		msg = 'Here are the available selling commands:\n'
		msg += '**.sell card <card id> [amount - Default: _1_]** to sell a specific card.\n'
		msg += '**.sell under [value - Default: _1.00_] [rares - Default: _false_]** to sell all cards worth less than the value entered.\n'
		msg += '**.sell dups [rares - Default: _false_]** to sell all duplicate cards until 1 remains. Doesn\'t sell rares by default.\n'
		msg += '**.sell all [rares - Default: _false_]** to sell all cards. Doesn\'t sell rares by default.\n'
		msg += '**.sell packs <set id> [amount - Default: 1]** to sell a pack.'
		return await ctx.send(msg)

	@sell_main.command(name='card',
					pass_context=True,
					description='Sells a specific card',
					brief='Sells a card',
					usage='<card id> [amount - Default: 1]')
	async def sell_card(self, ctx, card_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		player_card = Card.get_player_card(player, card_id)
		if not player_card:
			return await ctx.send('You don\'t have a card with that ID \\:(')
		self.cache.update({player_card.card.id: player_card.card})
		if player_card.id in player.savelist:
			return await ctx.send(f'You sold 0 **{player_card.name}** for ${0:.2f}')
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
					description='Sells card that are worth less than a given amount',
					brief='Sells cards under a specific value',
					usage='[value - Default: 1.00] [rares - Default: false]')
	async def sell_under(self, ctx, value: typing.Optional[float] = 1.00, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		value = 0.00 if value < 0 else value
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		player_cards = Card.get_player_cards(player, self.cache)
		cards_to_sell = [c for c in player_cards if c.price < value]
		cards_to_sell = [c for c in cards_to_sell if c.id not in player.savelist]
		if rares == 'false':
			cards_to_sell = [c for c in cards_to_sell if c.rarity in ['Common', 'Uncommon']]
		total_sold, total_cash = self.sell_cards(player, cards_to_sell, 0)
		return await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')

	@sell_main.command(name='dups',
					pass_context=True,
					description='Sells all of your duplicate cards',
					brief='Sells duplicate cards',
					aliases=['dupes', 'dup'],
					usage='[rares - Default: false]')
	async def sell_dups(self, ctx, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		cards_to_sell = Card.get_duplicate_player_cards(player, self.cache)
		cards_to_sell = [c for c in cards_to_sell if c.id not in player.savelist]
		if rares == 'false':
			cards_to_sell = [c for c in cards_to_sell if c.rarity in ['Common', 'Uncommon']]
		total_sold, total_cash = self.sell_cards(player, cards_to_sell, 1)
		return await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')

	@sell_main.command(name='all',
					pass_context=True,
					description='Sells all your cards',
					brief='Sell all cards',
					usage='[rares - Default: false]')
	async def sell_all(self, ctx, rares: typing.Optional[str] = 'false'):
		player = Player.get_player(ctx.author.id)
		rares = 'false' if rares.lower() not in ['false', 'true'] else rares
		cards_to_sell = Card.get_player_cards(player, self.cache)
		cards_to_sell = [c for c in cards_to_sell if c.id not in player.savelist]
		if rares == 'false':
			cards_to_sell = [c for c in cards_to_sell if c.rarity in ['Common', 'Uncommon']]
		total_sold, total_cash = self.sell_cards(player, cards_to_sell, 0)
		return await ctx.send(f'You sold **{total_sold}** cards for **${total_cash:.2f}**')

	@sell_main.command(name='packs',
					pass_context=True,
					description='Sells packs that you have',
					brief='Sells packs',
					usage='<set id> [amount - Default: 1]')
	async def sell_packs(self, ctx, set_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		set_ = Sets.get_set(set_id.lower())
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_.id not in player.packs:
			return await ctx.send(f"Looks like you don't have any **{set_.name}** packs.")
		amt = 1 if amt < 1 else amt
		sold = min(amt, player.packs[set_.id])
		player.packs[set_.id] -= sold
		if player.packs[set_.id] == 0:
			del player.packs[set_.id]
		player.cash += (set_.pack_price / 3) * sold
		player.total_cash += (set_.pack_price / 3) * sold
		player.update()
		return await ctx.send(f'You sold **{sold} {set_.name}** packs for **${(set_.pack_price / 3) * sold:.2f}**')

	@commands.command(name='search',
					pass_context=True,
					description='Search for cards',
					brief='Search for cards')
	async def search_cards(self, ctx, *query):
		msg = 'I couldn\'t find any cards, perhaps try using the following resources:\n'
		msg += '**Basic searching:** https://pokemontcg.guru/\n'
		msg += '**Advanced searching:** https://pokemontcg.guru/advanced\n'
		msg += '**Searching syntax:** http://www.lucenetutorial.com/lucene-query-syntax.html'
		query = ' '.join(query) if isinstance(query, tuple) else query
		if not query:
			return await ctx.send(msg)
		cards = Card.get_cards_with_query(query)
		if not cards:
			return await ctx.send(msg)
		self.cache.update({c.id: c for c in cards})
		return await self.card_paginated_embeds(ctx, Player.get_player(ctx.author.id), cards)

	## sets
	@commands.command(name='sets',
					pass_context=True,
					description='Show all of the sets',
					brief='Show all sets')
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
					description='Show the details of a set',
					brief='Show set details',
					usage='<set id>')
	async def get_set(self, ctx, set_id):
		player = Player.get_player(ctx.author.id)
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		cards = Card.get_player_cards(player, self.cache)
		set_cards = len([c for c in cards if c.card.set == set_])
		page = set_.page(set_cards)
		return await self.paginated_embeds(ctx, page)

	## packs
	@commands.command(name='packs',
					pass_context=True,
					description='Show the packs that you own',
					brief='Your packs',
					aliases=['p'])
	async def get_player_packs(self, ctx):
		player = Player.get_player(ctx.author.id)
		desc = f'You have **{player.daily_packs}** packs left to open today\n'
		desc += 'Use **.openpack <set_id> (amount)** to open packs\n'
		for set_id, amount in player.packs.items():
			desc += f'**{set_id}** - {amount}\n'
		return await self.paginated_embeds(ctx, Page('Your packs', desc))

	@commands.command(name='openpack',
					pass_context=True,
					description='Open packs that you own',
					brief='Open packs',
					aliases=['op'],
					usage='<set id> [amount - Default: 1]')
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
		pack = Packs.generate_packs(set_.id, opened, self.cache)
		self.cache.update({c.id: c for c in pack.cards})
		Card.add_or_update_cards_from_pack(player, pack, self.cache)
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
					description='The store, shows available items for purchase',
					brief='The store',
					usage='[slot - Default: 0] [amount - Default: 1]')
	async def card_store(self, ctx, slot: typing.Optional[int] = 0, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		slot = slot if 1 <= slot <= 10 else 0
		if not self.store:
			self.store = self.generate_store()
			self.cached_store_packs = 0
		if self.store.get('reset') < dt.now():
			self.store = self.generate_store()
			self.cached_store_packs = 0
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
			while player.cash >= s.pack_price * price_mult and bought < amt:
				player.cash -= s.pack_price * price_mult
				bought += 1
			if s.id not in player.packs:
				player.packs[s.id] = 0
			player.packs[s.id] += bought * pack_count
			await ctx.send(f'You bought {bought * pack_count} **{s.name}** packs!')
			if promo_count:
				cards = Card.get_cards_with_query(f'set.id:{s.id} -rarity:common AND -rarity:uncommon')
				self.cache.update({c.id: c for c in cards})
				promos = choices(cards, weights=[Packs.rarity_mapping.get(c.rarity, 50) for c in cards], k=bought)
				player.total_cards += len(promos)
				Card.add_or_update_cards_from_pack(player, Packs.Pack(s.id, promos), self.cache)
				player.update()
				return await self.card_paginated_embeds(ctx, Player.get_player(ctx.author.id), promos)
			return player.update()
		header = 'Welcome to the Card Store! Here you can spend cash for Packs of cards\n'
		header += f'You have **${player.cash:.2f}**\n'
		header += 'Here are the packs available today. To purchase one, use **.store <slot no.> (amount)**\n\n'
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
					description='Shows your stats',
					brief='Your stats')
	async def player_stats(self, ctx):
		player = Player.get_player(ctx.author.id)
		return await self.paginated_embeds(ctx, Page(ctx.author.display_name, player.stats_desc))

	## claimables
	@commands.command(name='daily',
					pass_context=True,
					description='A daily reward',
					brief='A daily reward')
	async def daily(self, ctx):
		player = Player.get_player(ctx.author.id)
		if player.daily_reset > dt.now():
			return await ctx.send(f'Your next daily reward is in **{format_remaining_time(player.daily_reset)}**')
		chance = random()
		if chance < .01:
			player.daily_packs = 100
			await ctx.send(f'***WOAH!!*** Your daily packs were reset! \\:D')
		elif chance < .15:
			set_ = choice(Sets.get_sets())
			if set_.id not in player.packs:
				player.packs[set_.id] = 0
			player.packs[set_.id] += 1
			await ctx.send(f'You got a{"n" if set_.name[0] in "aeiou" else ""} **{set_.name}** pack!')
		else:
			cash = randint(1, 10)
			player.cash += cash
			player.total_cash += cash
			await ctx.send(f'You got **${cash:.2f}**!')
		player.daily_reset = dt.now() + td(days=1)
		return player.update()

	## quizzes
	@commands.command(name='quiz',
					pass_context=True,
					description='Who\'s that Pokemon!',
					brief='Who\'s that Pokemon!')
	async def quiz(self, ctx):
		player = Player.get_player(ctx.author.id)
		if player.quiz_reset < dt.now():
			player.quiz_questions = 5
			player.current_multiplier = 1
		if player.quiz_questions == 0:
			return await ctx.send(f'You\'ve used up all your quiz attempts. Resets in **{format_remaining_time(player.quiz_reset)}**')

		def is_same_user_channel(m):
			return m.channel == ctx.channel and m.author == ctx.author

		q = Quiz.generate_random_quiz()
		msg = await ctx.send('Who\'s that Pokemon?!', file=q.silhouette)
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=15)
		except asyncio.TimeoutError:
			await msg.delete()
			await ctx.send(f'You ran out of time, it\'s **{q.guess_name.capitalize()}** from **Gen {q.gen}**', file=q.revealed)
			player.quiz_questions -= 1
			if player.quiz_reset < dt.now():
				player.quiz_reset = dt.now() + td(hours=2)
			return player.update()
		guess = reply.content.lower() if reply else None
		if guess == q.guess_name:
			all_five = False
			mult = player.current_multiplier + player.permanent_mult
			reward = .1 * mult
			player.cash += reward
			player.total_cash += reward
			if player.current_multiplier == 5:
				player.permanent_mult += 1
				all_five = True
			player.current_multiplier = min(player.current_multiplier + 1, 5)
			player.quiz_correct += 1
			content = f'Correct! It\'s **{q.guess_name.capitalize()}**\n'
			content += f'You earned **${reward:.2f}** and your multiplier is now **{player.current_multiplier}**'
			if all_five:
				content += f'\n**You got all 5 correct!** Your multiplier is permanently increased by **{player.permanent_mult}**'
			await msg.delete()
			await ctx.send(content, file=q.revealed)
		elif guess == q.gen:
			mult = player.current_multiplier + player.permanent_mult
			reward = .1 * mult
			player.cash += reward
			player.total_cash += reward
			content = f'Sure, it\'s from **Gen {q.gen}**. It\'s **{q.guess_name.capitalize()}**\n'
			content += f'You earned **${reward:.2f}**'
			await msg.delete()
			await ctx.send(content, file=q.revealed)
		elif guess == 'pikachu' and q.guess_name == 'clefairy':
			player.cash += 100
			player.total_cash += 100
			content = f'It\'s **{q.guess_name.capitalize()}**\n***FUCK***\n'
			await msg.delete()
			await ctx.send(content, file=q.revealed)
		else:
			await msg.delete()
			await ctx.send(f'Wrong! It\'s **{q.guess_name.capitalize()}** from **Gen {q.gen}**', file=q.revealed)
		player.quiz_questions -= 1
		if player.quiz_reset < dt.now():
			player.quiz_reset = dt.now() + td(hours=2)
		return player.update()

	## savelist
	@commands.group(name='savelist',
					pass_context=True,
					invoke_without_command=True,
					description='Add specific cards to your savelist to avoid selling them',
					brief='Save cards from selling',
					aliases=['sl'])
	async def savelist_main(self, ctx):
		player = Player.get_player(ctx.author.id)
		if not player.savelist:
			return await ctx.send('You have no cards in your savelist, use **.savelist add <card id>** to add a card')
		cards = []
		cards_not_in_cache = []
		for card_id in player.savelist:
			card = self.cache.get(card_id, None)
			if not card:
				cards_not_in_cache.append(card_id)
				continue
			cards.append(card)
		q = ' OR '.join([f'id:{card_id}' for card_id in cards_not_in_cache])
		cards_not_in_cache = Card.get_cards_with_query(f'({q})')
		cards.extend(cards_not_in_cache)
		self.cache.update({c.id: c for c in cards_not_in_cache})
		return await self.card_paginated_embeds(ctx, Player.get_player(ctx.author.id), cards)

	@savelist_main.command(name='add',
						pass_context=True,
						description='Add a card to your savelist',
						brief='Add card to savelist',
						usage='<card id>')
	async def savelist_add(self, ctx, card_id):
		player = Player.get_player(ctx.author.id)
		card = Card.get_card_by_id(card_id)
		if card is None:
			return await ctx.send('I couldn\'t find a card with that ID \\:(')
		player.savelist.append(card.id)
		player.savelist = list(set(player.savelist))
		player.update()
		return await ctx.send(f'**{card.name}** (_{card.id}_) added to your savelist')

	@savelist_main.command(name='remove',
						pass_context=True,
						description='Remove a card from your savelist',
						brief='Remove card from savelist',
						usage='<card id>')
	async def savelist_remove(self, ctx, card_id):
		player = Player.get_player(ctx.author.id)
		card = Card.get_card_by_id(card_id)
		if card is None:
			return await ctx.send('I couldn\'t find a card with that ID \\:(')
		try:
			player.savelist.remove(card.id)
			player.update()
			return await ctx.send(f'**{card.name}** (_{card.id}_) removed from your savelist')
		except ValueError:
			return await ctx.send(f'**{card.name}** (_{card.id}_) isn\'t in your savelist')

	@savelist_main.command(name='clear',
						pass_context=True,
						description='Clears your savelist',
						brief='Clears your savelist')
	async def savelist_clear(self, ctx):
		player = Player.get_player(ctx.author.id)
		player.savelist = []
		player.update()
		return await ctx.send('Your savelist has been cleared')

	## Trading
	@commands.group(name='trade',
					pass_context=True,
					invoke_without_command=True,
					description='Trade cards with another player',
					brief='Trade cards')
	async def trade_main(self, ctx):
		msg = 'Here are the available trading commands:\n'
		msg += '**.trade card <@player> <trade offer>** to trade for cards\n'
		msg += '**.trade pack <@player> <trade offer>** to trade for packs\n\n'
		msg += 'The **trade offer** is written as **cardID:amount/cardID:amount**\n'
		msg += 'E.g. to trade a **Jigglypuff** for a **Magikarp** player 1 would use:\n'
		msg += '**.trade @player2 bwp-bw65**, player 2 would reply **xyp-xy143**\n'
		msg += 'Trading multiple would make the trade offer: **bwp-bw65/dp2-108:2**\n'
		msg += 'Which would offer a Jigglypuff and two Zubats.\n\n'
		msg += 'For trading packs, replace the **card ID** with the **set ID**'
		return await ctx.send(msg)

	@trade_main.command(name='card',
					pass_context=True,
					description='Trade cards with another player',
					brief='Trade cards')
	async def trade_card(self, ctx, _tradee: Member, trade_offer: str):
		player = Player.get_player(ctx.author.id)
		tradee = Player.get_player(_tradee.id)
		cards = self.parse_trade_offer_str(trade_offer.lower())
		if not cards:
			return await ctx.send('I couldn\'t find any cards with that trade offer \\:(')
		player_cards = Card.get_player_cards(player, self.cache)
		player_cards = {pc.card: pc for pc in player_cards}
		player_trade_cards = []
		for card, amount in cards:
			pc = player_cards.get(card, None)
			if pc is None:
				return await ctx.send(f'You don\'t have any **{card.id}** cards')
			if amount <= pc.amount:
				player_trade_cards.append((pc, amount))
			else:
				return await ctx.send(f'You don\'t have that many **{card.id}** (you have _{pc.amount}_)')

		def is_player_same_channel(msg):
			return msg.channel == ctx.channel and msg.author == ctx.author

		def is_tradee_same_channel(msg):
			return msg.channel == ctx.channel and msg.author == _tradee

		card_to_trade_msg = ', '.join([f'{tc[0].name}x{tc[1]}' for tc in player_trade_cards])
		await ctx.send(f'<@{_tradee.id}>, what card do you want to trade for **{card_to_trade_msg}**')
		try:
			reply = await self.bot.wait_for('message', check=is_tradee_same_channel, timeout=60)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		trade_cards = self.parse_trade_offer_str(reply.content)
		if not trade_cards:
			return await ctx.send('I couldn\'t find any cards with that trade offer \\:(')
		tradee_cards = Card.get_player_cards(tradee, self.cache)
		tradee_cards = {pc.card: pc for pc in tradee_cards}
		tradee_trade_cards = []
		for card, amount in trade_cards:
			tc = tradee_cards.get(card, None)
			if tc is None:
				return await ctx.send(f'You don\'t have any **{card.id}** cards')
			if amount <= tc.amount:
				tradee_trade_cards.append((tc, amount))
			else:
				return await ctx.send(f'You don\'t have that many **{card.id}** (you have _{tc.amount}_)')
		tradee_card_to_trade_msg = ', '.join([f'{tc[0].name}x{tc[1]}' for tc in tradee_trade_cards])
		await ctx.send(f'**{ctx.author.display_name}** traded **{card_to_trade_msg}** to **{_tradee.display_name}** for **{tradee_card_to_trade_msg}**')
		player_pack = []
		tradee_cards_updated = []
		for ttc, amt in tradee_trade_cards:
			player_pack.extend([ttc.card] * amt)
			ttc.amount -= amt
			tradee_cards_updated.append(ttc)
		Card.add_or_update_cards_from_pack(player, Packs.Pack('', player_pack), self.cache)
		Card.add_or_update_cards_from_player_cards(tradee, tradee_cards_updated)
		tradee_pack = []
		player_cards_updated = []
		for ptc, amt in player_trade_cards:
			tradee_pack.extend([ptc.card] * amt)
			ptc.amount -= amt
			player_cards_updated.append(ptc)
		Card.add_or_update_cards_from_pack(tradee, Packs.Pack('', tradee_pack), self.cache)
		Card.add_or_update_cards_from_player_cards(player, player_cards_updated)

	@trade_main.command(name='pack',
					pass_context=True,
					description='Trade packs with another player',
					brief='Trade packs')
	async def trade_pack(self, ctx, _tradee: Member, trade_offer: str):
		player = Player.get_player(ctx.author.id)
		tradee = Player.get_player(_tradee.id)
		sets = self.parse_trade_offer_str(trade_offer.lower(), False)
		if not sets:
			return await ctx.send('I couldn\'t find any sets with that trade offer \\:(')
		player_trade_packs = []
		for set_, amount in sets:
			if not set_.id in player.packs:
				return await ctx.send(f'You don\'t have any of packs from **{set_.name}**')
			if amount <= player.packs.get(set_.id, 0):
				player_trade_packs.append((set_, amount))
			else:
				return await ctx.send(f'You don\'t have enough of packs from **{set_.name}** (you have _{player.packs.get(set_.id, 0)}_)')

		def is_player_same_channel(msg):
			return msg.channel == ctx.channel and msg.author == ctx.author

		def is_tradee_same_channel(msg):
			return msg.channel == ctx.channel and msg.author == _tradee

		pack_to_trade_msg = ', '.join([f'{tp[0].name}x{tp[1]}' for tp in player_trade_packs])
		await ctx.send(f'<@{_tradee.id}>, what card do you want to trade for **{pack_to_trade_msg}**')
		try:
			reply = await self.bot.wait_for('message', check=is_tradee_same_channel, timeout=60)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		trade_sets = self.parse_trade_offer_str(reply.content.lower(), False)
		if not trade_sets:
			return await ctx.send('I couldn\'t find any sets with that trade offer \\:(')
		tradee_trade_packs = []
		for set_, amount in trade_sets:
			if not set_.id in tradee.packs:
				return await ctx.send(f'You don\'t have any of packs from **{set_.name}**')
			if amount <= tradee.packs.get(set_.id, 0):
				tradee_trade_packs.append((set_, amount))
			else:
				return await ctx.send(f'You don\'t have enough of packs from **{set_.name}** (you have _{tradee.packs.get(set_.id, 0)}_)')
		tradee_pack_to_trade_msg = ', '.join([f'{tp[0].name}x{tp[1]}' for tp in tradee_trade_packs])
		await ctx.send(f'**{ctx.author.display_name}** traded **{pack_to_trade_msg}** to **{_tradee.display_name}** for **{tradee_pack_to_trade_msg}**')
		for tts, amt in tradee_trade_packs:
			if not tts.id in player.packs:
				player.packs[tts.id] = 0
			player.packs[tts.id] += amt
			tradee.packs[tts.id] -= amt
			if tradee.packs[tts.id] == 0:
				del tradee.packs[tts.id]
		for pts, amt in player_trade_packs:
			if not pts.id in tradee.packs:
				tradee.packs[pts.id] = 0
			tradee.packs[pts.id] += amt
			player.packs[pts.id] -= amt
			if player.packs[pts.id] == 0:
				del player.packs[pts.id]
		player.update()
		tradee.update()

	# Tasks
	@tasks.loop(seconds=60)
	async def refresh_daily_packs(self):
		if self.date < dt.now().date():
			log.info('Refreshing daily packs')
			sql('poketcg', 'update players set daily_packs = 100')
			self.date = dt.now().date()

	@tasks.loop(seconds=30)
	async def cache_store_packs(self):
		if self.cached_store_packs < 10:
			set_ = self.store[self.cached_store_packs + 1]
			log.info(f'Caching cards for set: {set_.id}')
			cards = Card.get_cards_with_query(f'set.id:{set_.id}')
			self.cache.update({c.id: c for c in cards})
			self.cached_store_packs += 1

	@tasks.loop(seconds=60, count=Card.get_player_card_count() // 250 + 1)
	async def cache_player_cards(self):
		start = 250 * self.cached_player_card_chunks
		end = 250 * (self.cached_player_card_chunks + 1)
		log.info(f'Caching player cards {start} to {end}')
		Card.get_player_card_chunk(start, end, self.cache)
		self.cached_player_card_chunks += 1

	## TMP
	# @commands.command(name='cache',
	# 				pass_context=True)
	# async def showcache(self, ctx):
	# 	if self.cache:
	# 		return await self.paginated_embeds(ctx, [c.page for c in self.cache.values()])
	# 	return await ctx.send('Cache is empty.')

	# @commands.command(name='addcash',
	# 				pass_context=True)
	# async def addcash(self, ctx, amt: int):
	# 	player = Player.get_player(ctx.author.id)
	# 	player.cash += amt
	# 	player.update()
	# 	return await ctx.send(f'{player.cash}')

	# @commands.command(name='resetpacks',
	# 				pass_context=True)
	# async def resetpacks(self, ctx):
	# 	player = Player.get_player(ctx.author.id)
	# 	player.daily_packs = 50
	# 	player.update()
	# 	return await ctx.send('Packs reset')

	# @commands.command(name='resetquiz',
	# 				pass_context=True)
	# async def resetquiz(self, ctx):
	# 	player = Player.get_player(ctx.author.id)
	# 	player.quiz_reset = dt(1999, 1, 1)
	# 	player.update()