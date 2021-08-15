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
	async def get_player_cards(self, ctx, sort_by: typing.Optional[str] = 'id'):
		player = Player.get_player(ctx.author.id)
		player_cards = Card.get_player_cards(player)
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

	@commands.command(name='sellcard',
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
					brief='')
	async def open_pack(self, ctx, set_id, amt: typing.Optional[int] = 1):
		player = Player.get_player(ctx.author.id)
		set_id = set_id.lower()
		set_ = Sets.get_set(set_id)
		if set_ is None:
			return await ctx.send('I couldn\'t find a set with that ID \\:(')
		if set_id not in player.packs:
			return await ctx.send('Looks like you don\'t have a pack from that set')
		packs = []
		opened = 0
		while opened < player.packs[set_id] and opened < amt:
			pack = Packs.Pack.from_set(set_id)
			packs.extend(pack)
			opened += 1
		pack = Packs.Pack(set_id, packs)
		Card.add_or_update_cards_from_pack(player, pack)
		player.packs[set_id] -= opened
		if player.packs[set_id] == 0:
			del player.packs[set_id]
		player.packs_opened += opened
		player.total_cards += 10 * opened
		player.update()
		return await self.paginated_embeds(ctx, pack.pages)

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
			s = self.store.get(slot)
			if player.cash < s.pack_price:
				return await ctx.send(f'You don\'t have enough... You need **${s.pack_price - player.cash}** more.')
			bought = 0
			while player.cash >= s.pack_price and bought < amt:
				player.cash -= s.pack_price
				bought += 1
			if s.id not in player.packs:
				player.packs[s.id] = 0
			player.packs[s.id] += bought
			player.packs_bought += bought
			await ctx.send(f'You bought {bought} **{s.name}** packs!')
			return player.update()
		desc = 'Welcome to the Card Store! Here you can spend cash for Packs of cards\n'
		desc += f'You have **${player.cash:.2f}**\n'
		desc += 'Here are the packs available today. To purchasae one, use **.store <slot no.> (amount)**\n\n'
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