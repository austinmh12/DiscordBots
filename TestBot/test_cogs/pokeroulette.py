from datetime import datetime as dt, timedelta as td
from discord.ext import commands
import asyncio
import logging
import re
import typing
from discord import Member, Embed, Colour, File
from random import random, choices, choice
from collections import Counter
from . import pokerouletteFunctions as PRF
from .pokerouletteFunctions import user as User
from .pokerouletteFunctions import pokemon as Pokemon
from .pokerouletteFunctions import battling as Battling

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)


##############
#THIS IS TEST#
##############
PRF.BASE_PATH = './test_cogs'
# Copy everything below this line
# Update between shadow and prod
version = '3.1.3'

# Utility Functions
def gen_rollall_embed(user, results, total_rolls, total_caught, total_boofs, avatar):
	results.sort(key=lambda x: x[0].name)
	results.sort(key=lambda x: x[1], reverse=True)
	results.sort(key=lambda x: x[2], reverse=True)
	results.sort(key=lambda x: x[0].rarity, reverse=True)
	result_chunks = list(PRF.chunk(results, 12))
	pages = []
	for rc in PRF.chunk(results, 12):
		desc = f'**Total Rolls:** {total_rolls}\n**Total Caught:** {total_caught}\n**Total bOofs:** {total_boofs}\n'
		for pkmn, amt, new in rc:
			desc += f'{"***" if new else ""}{pkmn.name}{" x" + str(amt) if amt > 1 else ""}{"***" if new else ""} {":star:" * pkmn.rarity}\n'
		pages.append(PRF.Page(user.username, desc, icon=avatar))
	return pages

def gen_pokedex_embed(ctx, user, pkdxs, total, avatar):
	pages = []
	chunks = PRF.chunk(pkdxs, 15)
	for ch in chunks:
		desc = ''
		for pkdx in ch:
			in_party = pkdx in user._party
			if in_party:
				desc += '***'
			desc += f'{pkdx.name} {"x" + str(pkdx.amount) if pkdx.amount > 1 else ""} {":star:"*pkdx.rarity}'
			desc += '***\n' if in_party else '\n'
		pages.append(PRF.Page(f'{user.username}\'s PokeDex - {total}/946', desc, icon=avatar))
	return pages

def gen_pokemon_emb(user, pkmn, level=0):
	if level:
		pkbt = Pokemon.PokeBattle.from_id(pkmn.id, level)
		return pkbt.embed(user)
	return pkmn.embed(user)

def gen_party_embed(user, party, title='Party', icon=None):
	desc = f'**Average Party Lvl:** _{sum([pkbt.level for pkbt in party]) // len(party)}_\n\n'
	for slot, pkbt in enumerate(party, start=1):
		if pkbt:
			desc += f'**{slot}:** {pkbt.name} - _{pkbt.level}_\n'
	return PRF.Page(f'{user.username}\'s {title}', desc, icon=icon)

def get_raid_reset():
	df = PRF.sql('select * from raid_timer')
	if df.empty:
		return dt.now() - td(hours=1)
	return dt.strptime(df.to_dict('records')[0]['raid_reset'], '%Y-%m-%d %H:%M:%S')

def update_raid_reset():
	PRF.sql('delete from raid_timer')
	PRF.sql('insert into raid_timer values (?)', ((dt.now() + td(days=1)).strftime('%Y-%m-%d %H:%M:%S'),))

class PokeRoulette(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.store = self.generate_store()
		self.raid = {'difficulty': None, 'players': [], 'initaitor': None}
		self.raid_reset = get_raid_reset()

	# Utilities
	def generate_store(self):
		ret = {}
		for j, i in enumerate([1, 3, 5], start=1):
			if random() < .90:
				pkmn = Pokemon.get_random_pokemon_by_rarity(i)
			else:
				pkmn = Pokemon.get_random_pokemon_by_rarity(i+1)
			ret[j] = pkmn
		ret['reset'] = (dt.now() + td(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
		return ret

	def update_raid(self, timer=True):
		self.raid = {'difficulty': None, 'players': [], 'initaitor': None}
		if timer:
			update_raid_reset()
			self.raid_reset = get_raid_reset()

	async def paginated_embeds(self, ctx, pages, content=''):
		idx = 0
		if not isinstance(pages, list):
			pages = [pages]
		emb = pages[idx].embed
		if len(pages) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
		msg = await ctx.send(content, embed=emb)
		if len(pages) > 1:
			await msg.add_reaction(PRF.BACK)
			await msg.add_reaction(PRF.NEXT)

			def is_left_right(m):
				return all([
					(m.emoji.name == PRF.BACK or m.emoji.name == PRF.NEXT),
					m.member.id != self.bot.user.id,
					m.message_id == msg.id
				])

			while True:
				try:
					react = await self.bot.wait_for('raw_reaction_add', check=is_left_right, timeout=60)
				except asyncio.TimeoutError:
					log.debug('Timeout, breaking')
					break
				if react.emoji.name == PRF.NEXT:
					idx = (idx + 1) % len(pages)
					await msg.remove_reaction(PRF.NEXT, react.member)
				else:
					idx = (idx - 1) % len(pages)
					await msg.remove_reaction(PRF.BACK, react.member)
				emb = pages[idx].embed
				emb.set_footer(text=f'{idx + 1}/{len(pages)}')
				await msg.edit(content=content, embed=emb)

	# Listeners
	# @commands.Cog.listener()
	# async def on_command_error(self, ctx, error):
	# 	log.debug(ctx.message.content)
	# 	if isinstance(error, commands.CommandNotFound):
	# 		return await self.pkmn_dex(ctx, ctx.message.content[1:])
	# 	log.error(error, exc_info=True)
	# 	return

	# Commands
	@commands.command(name='boofs',
					pass_context=True,
					description='See your total pokeboofs',
					brief='Total pokeboofs',
					aliases=['b'],
					usage='[user]')
	async def boofs(self, ctx, user: typing.Optional[Member] = None):
		user = User.get_user(user.id) if user else User.get_user(ctx.author.id)
		return await ctx.send(f'<@{user.id}> has {user.boofs} PokebOofs.{" Nice." if user.boofs == 69 else ""}')

	# PAGE THIS
	@commands.command(name='boofleaderboard',
					pass_context=True,
					description='The leaderboards for pokeboofs',
					brief='Pokeboof leaderboard',
					aliases=['bl'])
	async def boof_leaderboard(self, ctx):
		users = User.get_all_users()
		users.sort(key=lambda x: x.boofs)
		users.reverse()
		desc = ''
		for i, user in enumerate(users, start=1):
			if i == 1:
				i = ':first_place:'
			elif i == 2:
				i = ':second_place:'
			elif i == 3:
				i = ':third_place:'
			else:
				i = f'**#{i}**'
			desc += f'{i}: {user.username} - {user.boofs}{" Nice." if user.boofs == 69 else ""}\n'
		emb = Embed(
				title='PokebOof Leaderboard',
				description=desc,
				colour=Colour.from_rgb(255, 50, 50)
			)
		try:
			rank = list([user.username for user in users]).index(ctx.author.name) + 1
		except ValueError:
			rank = 0
		if rank:
			emb.set_footer(text=f'You are ranked #{rank}')
		return await ctx.channel.send(embed=emb)

	@commands.command(name='pokeroll',
					pass_context=True,
					description='Roll the pokemon roulette',
					brief='Roll the PokeRoulette',
					aliases=['p'])
	async def poke_roll(self, ctx):
		user = User.get_user(ctx.author.id)
		if not user:
			user = User.add_user(ctx.author.id, ctx.author.name)
		if dt.now() < user._roll_reset and user.stored_rolls < 1:
			return await ctx.send(f'Your next roll is in **{PRF.format_remaining_time(user._roll_reset)}**')
		elif dt.now() < user._roll_reset and user.stored_rolls >= 1:
			if random() < .02 * user.get_upgrade('rollrefund'):
				refunded = True
			else:
				refunded = False
				user.stored_rolls -= 1
			user.total_rolls += 1
			pkmn_rolls = Pokemon.roll_pokemon(user)
			result_pic = Pokemon.gen_result_pic(pkmn_rolls)
			file = File(f'{PRF.BASE_PATH}/rsc/tmp.png')
			if not pkmn_rolls:
				user.boofs += 1
				await ctx.send('bOof', file=file)
				file.close()
			else:
				result_text = f'**{user.username}** rolled:\n'
				pkdxs = []
				for pkmn in pkmn_rolls:
					if pkmn:
						pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
						if not pkdx:
							pkdx = Pokemon.PokedexEntry(user.id, -1, **pkmn.to_dict())
						else:
							pkdx.amount += 1
						if pkdx.id == user._hunting['poke_id']:
							user._hunting['caught'] += 1
						pkdxs.append(pkdx)
						result_text += f'{"***" if pkdx.amount <= 0 else ""}{pkmn.name}{"***" if pkdx.amount <= 0 else ""} {"Streak ***" + str(user._hunting["caught"]) + "***" if pkdx.id == user._hunting["poke_id"] else ""}\n'
				user.total_caught += len([p for p in pkmn_rolls if p])
				await ctx.send(result_text, file=file)
				file.close()
				Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, pkdxs)
			if refunded:
				await ctx.send(f'Your roll was refunded! (**{user.stored_rolls}** stored).')
		else:
			if random() < .02 * user.get_upgrade('rollrefund'):
				refunded = True
			else:
				refunded = False
				user._roll_reset = dt.now() + td(minutes=max(120 - (user.get_upgrade('rollcooldown') * 10), 30))
			user.total_rolls += 1
			pkmn_rolls = Pokemon.roll_pokemon(user)
			result_pic = Pokemon.gen_result_pic(pkmn_rolls)
			file = File(f'{PRF.BASE_PATH}/rsc/tmp.png')
			if not pkmn_rolls:
				user.boofs += 1
				await ctx.send('bOof', file=file)
				file.close()
			else:
				result_text = f'**{user.username}** rolled:\n'
				pkdxs = []
				for pkmn in pkmn_rolls:
					if pkmn:
						pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
						if not pkdx:
							pkdx = Pokemon.PokedexEntry(user.id, -1, **pkmn.to_dict())
						else:
							pkdx.amount += 1
						if pkdx.id == user._hunting['poke_id']:
							user._hunting['caught'] += 1
						pkdxs.append(pkdx)
						result_text += f'{"***" if pkdx.amount <= 0 else ""}{pkmn.name}{"***" if pkdx.amount <= 0 else ""} {"Streak ***" + str(user._hunting["caught"]) + "***" if pkdx.id == user._hunting["poke_id"] else ""}\n'
				user.total_caught += len([p for p in pkmn_rolls if p])
				await ctx.send(result_text, file=file)
				file.close()
				Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, pkdxs)
			if refunded:
				await ctx.send(f'Your roll was refunded!')
		reward_str = user.reward_achievements('boofs', 'rolls', 'pokemon')
		if reward_str:
			await ctx.send(reward_str)
		user.update()

	@commands.command(name='pokecashrelease',
					pass_context=True,
					description='Release a specific pokemon for Pokecash',
					brief='Release a pokemon for Pokecash',
					aliases=['pr', 'r'],
					usage='<pkmn>')
	async def cash_release(self, ctx, *pokemon):
		user = User.get_user(ctx.author.id)
		pkmn = Pokemon.get_pokemon(pokemon)
		if not pkmn:
			return await ctx.send('No pokemon with that name.')
		pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
		pkdx.amount -= 1
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, [pkdx])
		user.total_released += 1
		cash_earned = PRF.rarity_info[pkmn.rarity]['cash'] * (2 ** user.get_upgrade('doublecash'))
		user.pokecash += cash_earned
		user.total_pokecash += cash_earned
		await ctx.send(f'You released a **{pkmn.name}** for **{cash_earned}** pokecash (**{user.pokecash}** in your wallet).')
		if pkdx in user._party and pkdx.amount == 0:
			user._party.pop(user._party.index(pkdx))
		reward_str = user.reward_achievements('released', 'pokecash')
		if reward_str:
			await ctx.send(reward_str)
		user.update()

	@commands.command(name='pokecashautorelease',
					pass_context=True,
					description='Automatically release duplicate pokemon of a specific rarity or lower for Pokecash',
					brief='Release duplicate pokemon automatically for Pokecash',
					aliases=['parl', 'arl'],
					usage='[rarity]')
	async def cash_autorelease(self, ctx, rarity: typing.Optional[int] = 3):
		user = User.get_user(ctx.author.id)
		pkmn_to_release = Pokemon.get_duplicate_pokedex_extries(user, rarity)
		if not pkmn_to_release:
			return await ctx.send(f'You have no duplicates of rarity {rarity} or less')
		total_released = 0
		total_earned = 0
		for pkdx in pkmn_to_release:
			if pkdx.id in user._savelist or pkdx.id == user._hunting.get('poke_id', 0):
				continue
			cash_earned = PRF.rarity_info[pkdx.rarity]['cash'] * (2 ** user.get_upgrade('doublecash'))
			total_released += pkdx.amount - 1
			total_earned += cash_earned * (pkdx.amount - 1)
			pkdx.amount = 1
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, pkmn_to_release)
		user.total_released += total_released
		user.pokecash += total_earned
		user.total_pokecash += total_earned
		await ctx.send(f'You released **{total_released}** pokemon for **{total_earned}** pokecash (**{user.pokecash}** in your wallet).')
		reward_str = user.reward_achievements('released', 'pokecash')
		if reward_str:
			await ctx.send(reward_str)
		user.update()

	# Abstract the sorting and make it user, sorting
	@commands.command(name='pokedex',
					pass_context=True,
					description='Show your Pokedex',
					brief='Show your Pokedex',
					aliases=['pd'],
					usage='[sort] [user]')
	async def pokedex(self, ctx, user: typing.Optional[Member] = None, *sorting):
		if not sorting:
			sorting = ['id']
		sorting = list(sorting)
		sorting.reverse()
		avatar = user.avatar_url if user else ctx.author.avatar_url
		user = User.get_user(user.id) if user else User.get_user(ctx.author.id)
		pkdxs = Pokemon.get_user_pokedex(user)
		for sort in sorting:
			if sort not in ['name', 'id', 'double', 'rare', 'shiny']:
				continue
			if sort == 'name':
				pkdxs.sort(key=lambda x: x.name)
			if sort == 'id':
				pkdxs.sort(key=lambda x: x.id)
			if sort == 'double':
				pkdxs.sort(key=lambda x: x.amount, reverse=True)
			if sort == 'rare':
				pkdxs.sort(key=lambda x: x.rarity, reverse=True)
			if sort == 'shiny':
				pkdxs = [p for p in pkdxs if p.shiny]
		total = len(pkdxs)
		if not pkdxs:
			return await ctx.send('No pokemon')
		pages = gen_pokedex_embed(ctx, user, pkdxs, total, avatar)
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='pokeserver',
					pass_context=True,
					description='The server leaderboard',
					brief='The server leaderboard',
					aliases=['ps'],
					usage='[leaderboard]')
	async def poke_server(self, ctx, compare: typing.Optional[str] = 'unique'):
		user = User.get_user(ctx.author.id)
		users = User.get_all_users()
		if compare not in ['unique', 'total', 'rolls', 'shiny', 'cash', 'bought', 'trade', 'release', 'achievements', 'battles', 'levels']:
			compare = 'unique'
		if compare == 'unique':
			ret = [(u, len(Pokemon.get_user_pokedex(u))) for u in users]
		if compare == 'shiny':
			ret = []
			for u in users:
				pkdx = Pokemon.get_user_pokedex(u)
				ret.append((u, len([p for p in pkdx if p.shiny])))
		if compare == 'total':
			ret = [(u, u.total_caught) for u in users]
		if compare == 'rolls':
			ret = [(u, u.total_rolls) for u in users]
		if compare == 'cash':
			ret = [(u, u.total_pokecash) for u in users]
		if compare == 'bought':
			ret = [(u, u.total_bought) for u in users]
		if compare == 'trade':
			ret = [(u, u.total_traded) for u in users]
		if compare == 'release':
			ret = [(u, u.total_released) for u in users]
		if compare == 'achievements':
			ret = [(u, sum([max(ach) for ach in u._achievements.values()])) for u in users]
		if compare == 'battles':
			ret = [(u, u.total_battles) for u in users]
		if compare == 'levels':
			ret = [(u, Pokemon.get_user_total_level(u.id)) for u in users]
		ret.sort(key=lambda x: x[1], reverse=True)
		ret_chunks = PRF.chunk(ret, 15)
		rank = [u for u, amt in ret].index(user) + 1
		pages = []
		for rc in ret_chunks:
			desc = ''
			for i, (u, amt) in enumerate(ret, start=1):
				if i == 1:
					i = ':first_place:'
				elif i == 2:
					i = ':second_place:'
				elif i == 3:
					i = ':third_place:'
				else:
					i = f'**#{i}**'
				desc += f'{i}: {u.username} - {amt}{" Nice." if amt == 69 else ""}\n'
			pages.append(PRF.Page('', desc, title=f'{compare.capitalize()} Server Leaderboard', footer=f'You are ranked #{rank}'))
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='stats',
					pass_context=True,
					description='Shows the player stats',
					brief='Shows the player stats',
					aliases=['s'],
					usage='[user]')
	async def stats(self, ctx, user: typing.Optional[Member] = None):
		avatar = user.avatar_url if user else ctx.author.avatar_url
		user = User.get_user(user.id) if user else User.get_user(ctx.author.id)
		log.debug(str(user._achievements))
		pages = []
		if dt.now() >= user._roll_reset:
			remaining = 'You __can__ roll now!'
		else:
			remaining = PRF.format_remaining_time(user._roll_reset)
		page_one_desc = f'**Stored rolls:** {user.stored_rolls} **|** {remaining}\n\n'
		page_one_desc += f'**Pokedex:** {len(Pokemon.get_user_pokedex(user))} Pokemon\n'
		if user._hunting['poke_id']:
			page_one_desc += f'**Hunting:** {Pokemon.get_pokemon_by_id(user._hunting["poke_id"]).name}\n\n'
		else:
			page_one_desc += '\n\n'
		page_one_desc += '__**Pokemon Stats**__\n'
		page_one_desc += f'**Rolls:** {user.total_rolls} | **Released:** {user.total_released}\n'
		page_one_desc += f'**Caught:** {user.total_caught} | **bOofs:** {user.boofs}{" Nice." if user.boofs == 69 else ""}\n'
		page_one_desc += f'**Trades:** {user.total_traded} | **Bought:** {user.total_bought}\n\n'
		page_one_desc += '__**PokeCash Stats**__\n'
		page_one_desc += f'**Wallet:** {user.pokecash} | **Total:** {user.total_pokecash}\n'
		page_one_desc += f'**Gifts:** {user.total_gifts}\n\n'
		page_one_desc += f'__**Battle Stats**__\n'
		page_one_desc += f'**Total Level:** {Pokemon.get_user_total_level(user)}\n'
		page_one_desc += f'**Battles:** {user.total_battles}\n'
		page_one_desc += f'**Raids:** {user.total_raids} | **Raids Completed:** {user.raid_completions}\n'
		if user.favourite:
			fav = Pokemon.get_pokemon_by_id(user.favourite)
			pages.append(PRF.Page('Overall', page_one_desc, icon=avatar, thumbnail=fav.url))	
		else:
			pages.append(PRF.Page('Overall', page_one_desc, icon=avatar))
		
		page_two_desc = ''
		if user.has_party:
			page_two_desc = f'**Average Party Lvl:** _{sum([pkbt.level for pkbt in user._party]) // len(user._party)}_\n\n'
		for slot, pkbt in enumerate(user._party, start=1):
			if pkbt:
				page_two_desc += f'**{slot}:** {pkbt.name} - _{pkbt.level}_\n'
		if not page_two_desc:
			page_two_desc = 'No pokemon in party'
		pages.append(PRF.Page('Party', page_two_desc, icon=avatar))

		page_three_desc = ''
		for gym in user._gyms:
			page_three_desc += f'**{gym}:** {Battling.gym_leaders[gym]().name}\n'
		page_three_desc += f'**Elite Four Completions:** {user.e4_completions}'
		pages.append(PRF.Page('Gyms', page_three_desc, icon=avatar))

		badges = Pokemon.get_badges(user)
		badges_desc = ''
		badges.sort(key=lambda x: x.id)
		badges.sort(key=lambda x: x.level, reverse=True)
		badges.sort(key=lambda x: x.amount, reverse=True)
		badge_displays = [b.display for b in badges]
		badge_chunks = list(PRF.chunk(badge_displays, 15))
		pages.extend([PRF.Page('Badges', bc, colour=(58, 92, 168), icon=avatar) for bc in badge_chunks])
		achievements = []
		for cat, ach in user._achievements.items():
			if max(ach):
				achievements.append(f'**{"bOofs" if cat == "boofs" else cat.capitalize()}** {max(ach)}')
		achievement_chunks = list(PRF.chunk(achievements, 15))
		pages.extend([PRF.Page('Achievements', ac, colour=(255, 203, 5), icon=avatar) for ac in achievement_chunks])
		upgrades = []
		for upgrade, level in user._upgrades.items():
			if level:
				upgrades.append(f'**{upgrade.replace("_","")}:** {level}')
		upgrade_chunks = list(PRF.chunk(upgrades, 15))
		pages.extend([PRF.Page('Upgrades', uc, colour=(85, 151, 212), icon=avatar) for uc in upgrade_chunks])
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='timers',
					pass_context=True,
					description='Shows the time until the next roll reset',
					brief='Time until next roll reset',
					aliases=['t'])
	async def timers(self, ctx):
		user = User.get_user(ctx.author.id)
		ret = ''
		next_roll = user._roll_reset > dt.now()
		next_daily = user._daily_reward > dt.now()
		next_ditto = user._ditto_reset > dt.now()
		next_battle = user._battle_reset > dt.now()
		next_gym = user._gym_reset > dt.now()
		next_e4 = user._e4_reset > dt.now()
		next_wt = user._wt_reset > dt.now()
		if next_roll:
			ret += f'Your next roll is in **{PRF.format_remaining_time(user._roll_reset)}**\n'
		else:
			ret += 'You can roll now!\n'
		if next_daily:
			ret += f'Your next daily is in **{PRF.format_remaining_time(user._daily_reward)}**\n'
		else:
			ret += 'You can claim your daily now!\n'
		if next_ditto:
			ret += f'Ditto can duplicate in **{PRF.format_remaining_time(user._ditto_reset)}**\n'
		else:
			ret += 'Ditto can duplicate now!\n'
		if next_battle:
			ret += f'You can battle again in **{PRF.format_remaining_time(user._battle_reset)}**\n'
		else:
			ret += 'You can battle now!\n'
		if 8 not in user._gyms:
			if next_gym:
				ret += f'You can challenge gyms again in **{PRF.format_remaining_time(user._gym_reset)}**\n'
			else:
				ret += 'You can challenge gyms now!\n'
		if 8 in user._gyms:
			if next_e4:
				ret += f'You can challenge the Elite Four again in **{PRF.format_remaining_time(user._e4_reset)}**\n'
			else:
				ret += 'You can challenge the Elite Four now!\n'
		if next_wt:
			ret += f'Your next WonderTrade is in **{PRF.format_remaining_time(user._wt_reset)}**'
		else:
			ret += 'You can WonderTrade now!'
		return await ctx.send(ret)

	@commands.command(name='pokemart',
					pass_context=True,
					description='The PokeMart for buying upgrades',
					brief='PokeMart',
					aliases=['pm', 'mart'],
					usage='[upgrade]')
	async def pokemart(self, ctx, slot: typing.Optional[int] = 0, all_: typing.Optional[str] = ''):
		user = User.get_user(ctx.author.id)
		slot = slot if 1 <= slot <= max(PRF.upgrade_info.keys()) else 0
		has_discount = .75 if user.get_upgrade('upgradediscount') else 1
		if slot:
			upgrade = PRF.upgrade_info[slot]
			upgrade_level = user.get_upgrade(upgrade['name'])
			upgrade_cost = upgrade['cost'](upgrade_level, has_discount)
			if user.pokecash < upgrade_cost:
				return await ctx.send(f'You don\'t have enough PokeCash... You need **{upgrade_cost - user.pokecash}** more PokeCash')
			if upgrade_level >= upgrade['max_level']:
				return await ctx.send(f'Your **{upgrade["name"]}** is max level already!')
			if all_:
				amt = 0
				while user.pokecash >= upgrade_cost and upgrade_level < upgrade['max_level']:
					user._upgrades[upgrade['name']] += 1
					user.pokecash -= upgrade_cost
					upgrade_level = user.get_upgrade(upgrade['name'])
					upgrade_cost = upgrade['cost'](upgrade_level, has_discount)
					amt += 1
			else:
				amt = 1
				user._upgrades[upgrade['name']] += 1
				user.pokecash -= upgrade_cost
			await ctx.send(f'You upgraded **{upgrade["name"]}**, it is now level ***{user.get_upgrade(upgrade["name"])}*** (**{user.pokecash}** left in wallet).')
			if upgrade['category'] == 'Cooldown':
				user.refresh_cooldowns(upgrade['name'])
			if upgrade['name'] == 'fullreset':
				user.cooldowns_now()
			if upgrade['name'] == 'safarirefresh':
				self.store = self.generate_store()
			if upgrade['name'] == 'raidreset':
				self.raid_reset = dt.now() - td(hours=1)
			reward_str = user.reward_achievements('upgrades')
			if reward_str:
				await ctx.send(reward_str)
			return user.update()
		header = 'Welcome to the PokeMart! Here you can spend your hard-earned PokeCash on upgrades for the roulette.\n'
		header += f'You currently have **{user.pokecash}** PokeCash\nHere is the list of upgrades. To purchase an upgrade, use **.pokemart <slot no.>**\n\n'
		upgrade_categories = {c: [] for c in list(set([v['category'] for v in PRF.upgrade_info.values()]))}
		for slot, upgrade in PRF.upgrade_info.items():
			upgrade_categories[upgrade['category']].append([slot, upgrade])
		ordered = []
		ordered.append(['Rolls', upgrade_categories['Rolls']])
		ordered.append(['Cooldown', upgrade_categories['Cooldown']])
		ordered.append(['Battle', upgrade_categories['Battle']])
		ordered.append(['Misc', upgrade_categories['Misc']])
		pages = []
		for category, upgrades in ordered:
			desc = ''
			for slot, upgrade in upgrades:
				if user.get_upgrade(upgrade['name']) >= upgrade['max_level']:
					continue
				desc += f'**{slot}: {upgrade["name"]}** (_{user.get_upgrade(upgrade["name"])}_) - {upgrade["description"]} | ***{upgrade["cost"](user.get_upgrade(upgrade["name"]), has_discount)}***\n'
			full_desc = f'{header}{desc}'
			pages.append(PRF.Page(category, header+desc, colour=(85, 151, 212), icon='https://cdn.bulbagarden.net/upload/9/9b/Poké_Mart_FRLG.png'))
		return await self.paginated_embeds(ctx, pages)

	# Add roll refunds back into this
	@commands.command(name='pokerollall',
					pass_context=True,
					description='Rolls all your available stored poke rolls',
					brief='All your stored rolls',
					aliases=['pa'])
	async def roll_all(self, ctx):
		log.debug('Rolling')
		user = User.get_user(ctx.author.id)
		if not user:
			user = User.add_user(ctx.author.id, ctx.author.name)
		if user.stored_rolls < 1:
			return await ctx.send(f'You need __at least 1__ stored roll, you have **{user.stored_rolls}**.')
		total_boofs = 0
		total_rolls = 0
		caught = []
		while user.stored_rolls >= 1:
			total_rolls += int(user.stored_rolls)
			df = Pokemon.roll_all_pokemon(user)
			caught.extend(list(filter(None, df.caught)))
			for c in PRF.chunk(df.caught, 6):
				if not any(list(c)):
					total_boofs += 1
			for _ in range(int(user.stored_rolls)):
				if random() < .02 * user.get_upgrade('rollrefund'):
					pass
				else:
					user.stored_rolls -= 1
		log.debug('Done rolling')
		user.total_rolls += total_rolls
		user.total_caught += len(caught)
		user.boofs += total_boofs
		user.update()
		caught_counter = Counter(caught)
		Pokemon.add_or_update_user_pokedex_entry_from_pokemon(user, caught, caught_counter)
		log.debug('Db updated')
		results = []
		user_pkdx = Pokemon.get_user_pokedex(user)
		pkdx_map = {pkdx.id: pkdx for pkdx in user_pkdx}
		for p in list(set(caught)):
			pkdx = pkdx_map.get(p.id, None)
			amt = caught_counter[p]
			if pkdx:
				results.append((p, amt, pkdx.amount <= amt))
			else:
				results.append((p, amt, True))
		pages = gen_rollall_embed(user, results, total_rolls, len(caught), total_boofs, ctx.author.avatar_url)
		log.debug('Done')
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='trade',
					pass_context=True,
					description='Trade a pokemon you have for a pokemon someone else has',
					brief='Trade pokemon',
					aliases=['tr'],
					usage='<user> [pkmn]')
	async def trade(self, ctx, trade_user_: Member, *pkmn):
		user = User.get_user(ctx.author.id)
		trade_user = User.get_user(trade_user_.id)

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
		
		if not pkmn:
			await ctx.send('What Pokemon would you like to trade?')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			pkmn = reply.content
		pkmn = Pokemon.get_pokemon(pkmn)
		if not pkmn:
			return await ctx.send('No pokemon with that name.')
		pkdx = Pokemon.get_user_pokedex_entry(user.id, pkmn)
		if not pkdx:
			return await ctx.send('You don\'t own that Pokemon.')
		
		def is_trade_user_same_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == trade_user_.id

		await ctx.send(f'<@{trade_user_.id}>, who do you want to trade for **{pkmn.name}**?')
		try:
			reply = await self.bot.wait_for('message', check=is_trade_user_same_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		trade_pkmn = Pokemon.get_pokemon(reply.content)
		if not trade_pkmn:
			return await ctx.send('No pokemon with that name.')
		trade_pkdx = Pokemon.get_user_pokedex_entry(trade_user.id, trade_pkmn)
		if not trade_pkdx:
			return await ctx.send('You don\'t own that Pokemon.')
		await ctx.send(f'**{ctx.author.name}**, do you accept this trade? (y/n)')
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		if reply.content.lower() == 'n':
			return await ctx.send('The trade has been declined.')
		await ctx.send(f'**{ctx.author.name}** traded **{trade_user_.name}** **{pkmn.name}** for **{trade_pkmn.name}**')
		user_get_pkdx = Pokemon.get_user_pokedex_entry(user, trade_pkmn)
		trade_user_get_pkdx = Pokemon.get_user_pokedex_entry(trade_user, pkmn)
		if not user_get_pkdx:
			user_get_pkdx =Pokemon.PokedexEntry(user.id, -1, **trade_pkmn.to_dict())
		else:
			user_get_pkdx.amount += 1
		if not trade_user_get_pkdx:
			trade_user_get_pkdx = Pokemon.PokedexEntry(trade_user.id, -1, **pkmn.to_dict())
		else:
			trade_user_get_pkdx.amount += 1
		pkdx.amount -= 1
		trade_pkdx.amount -= 1
		if pkdx in user._party and pkdx.amount == 0:
			user._party.pop(user._party.index(pkdx))
		if trade_pkdx in trade_user._party and trade_pkdx.amount == 0:
			trade_user._party.pop(trade_user._party.index(trade_pkdx))
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, [pkdx, user_get_pkdx])
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(trade_user, [trade_pkdx, trade_user_get_pkdx])
		user.total_traded += 1
		trade_user.total_traded += 1
		reward_str = user.reward_achievements('trades', 'pokemon')
		if reward_str:
			await ctx.send(reward_str)
		user.update()
		return trade_user.update()

	@commands.command(name='safarizone',
					pass_context=True,
					description='A store holding 3 random pokemon each day',
					brief='Pokemon store',
					aliases=['sz'],
					usage='[slot]')
	async def safarizone(self, ctx, slot: typing.Optional[int] = 0, amt: typing.Optional[int] = 1):
		amt_ = amt
		user = User.get_user(ctx.author.id)
		slot = slot if 1 <= slot <= 3 else 0
		if not self.store:
			self.store = self.generate_store()
		if self.store.get('reset') < dt.now():
			self.store = self.generate_store()
		if slot:
			pkmn = self.store.get(slot)
			cost = PRF.rarity_info[pkmn.rarity]['cash'] * 3
			if user.pokecash < cost:
				return await ctx.send(f'You don\'t have enough... You need **{cost - user.pokecash}** more PokeCash.')
			pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
			while user.pokecash >= cost and amt:
				user.pokecash -= cost
				user.total_bought += 1
				if pkdx:
					pkdx.amount += 1
				else:
					pkdx = Pokemon.PokedexEntry(user.id, -1, **pkmn.to_dict())
				amt -= 1
			Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, [pkdx])
			await ctx.send(f'You bought {"a" if amt_ == 1 else "**" + str(amt_ - amt) + "**"} **{pkmn.name}**! (**{user.pokecash}** left in wallet).')
			reward_str = user.reward_achievements('safari', 'pokemon')
			if reward_str:
				await ctx.send(reward_str)
			return user.update()
		desc = 'Welcome to the Safari Zone! Here you can spend your hard-earned PokeCash on more Pokemon!\n'
		desc += f'You currently have **{user.pokecash}** PokeCash\nHere are the available Pokemon today. To purchase one, use **.safarizone <slot no.>**\n\n'
		pkmn_list = [(pkmn.rarity, pkmn) for pkmn in self.store.values() if not isinstance(pkmn, dt)]
		pkmn_list.sort(key=lambda x: x[0])
		for i, (_, pkmn) in enumerate(pkmn_list, start=1):
			if Pokemon.get_user_pokedex_entry(user, pkmn):
				desc += f'**{i}:** {pkmn.name} | ***{PRF.rarity_info[pkmn.rarity]["cash"] * 3}***\n'
			else:
				desc += f'**{i}:** ***{pkmn.name}*** | ***{PRF.rarity_info[pkmn.rarity]["cash"] * 3}***\n'
		page = PRF.Page('Safari Zone', desc, colour=(72, 144, 96), icon='https://www.serebii.net/itemdex/sprites/safariball.png', footer=f'Resets in {PRF.format_remaining_time(self.store.get("reset"))}')
		return await self.paginated_embeds(ctx, [page])

	@commands.command(name='daily',
					pass_context=True,
					description='A daily reward the gives either extra rolls or PokeCash',
					brief='Daily reward',
					aliases=['d'])
	async def daily(self, ctx):
		user = User.get_user(ctx.author.id)
		if not user:
			user = User.add_user(ctx.author.id, ctx.author.name)
		if user._daily_reward > dt.now():
			return await ctx.send(f'Your next daily reward is in **{PRF.format_remaining_time(user._daily_reward)}**')
		reward = round(random(), 0)
		reward_amount = choices(range(1, 11), weights=[25, 20, 15, 10, 5, 5, 5, 5, 2.5, 1], k=1)[0]
		stored = user.has_achievement('stored', 1)
		if reward:
			value = 200 * reward_amount if stored else 100 * reward_amount
			user.pokecash += value
			user.total_pokecash += value
			await ctx.send(f'You got **{value}** PokeCash! Spend it wisely! (**{user.pokecash}** in wallet).')
		else:
			value = 1 * reward_amount if stored else .5 * reward_amount
			user.stored_rolls += value
			await ctx.send(f'You got **{value}** extra rolls! (**{user.stored_rolls}** stored).')
		user._daily_reward = dt.now() + td(hours=16 - user.get_upgrade('dailycooldown'))
		reward_str = user.reward_achievements('stored', 'pokecash')
		if reward_str:
			await ctx.send(reward_str)
		user.update()
	
	@commands.command(name='pkmn',
					pass_context=True,
					description='Search for a Pokemon.',
					brief='Search for a Pokemon',
					usage='<pkmn>')
	async def pkmn_dex(self, ctx, *name):
		user = User.get_user(ctx.author.id)
		if not user:
			user = User.add_user(ctx.author.id, ctx.author.name)
		name = ' '.join(name)
		if '/' in name:
			name, level = name.split('/')
			try:
				level = int(level)
			except ValueError:
				level = 0
		else:
			level = 0
		pkmn = Pokemon.get_pokemon(name)
		if not pkmn:
			return await ctx.send('No pokemon with that name or id.')
		return await self.paginated_embeds(ctx, [gen_pokemon_emb(user, pkmn, level)])

	@commands.command(name='reminder',
					pass_context=True,
					description='DM\'s you a reminder when you can roll again',
					brief='DM a roll reminder',
					aliases=['rd'],
					usage='[reminder]')
	async def reminder(self, ctx, timer: typing.Optional[str] = 'roll'):
		user = User.get_user(ctx.author.id)
		if timer.lower() not in ['roll', 'battle', 'daily', 'ditto', 'gym', 'elite4', 'wtrade']:
			return await ctx.send('Must be one of the following: [roll, battle, daily, ditto, gym, elite4, wtrade]')
		if timer.lower() == 'gym' and 8 in user._gyms:
			return await ctx.send('You beat all the gyms.')
		if timer.lower() == 'elite4' and 8 not in user._gyms:
			return await ctx.send('You can\'t challenge the Elite Four yet.')
		sleep_times = {
			'roll': user._roll_reset,
			'battle': user._battle_reset,
			'daily': user._daily_reward,
			'ditto': user._ditto_reset,
			'gym': user._gym_reset,
			'elite4': user._e4_reset,
			'wtrade': user._wt_reset
		}
		sleep_time = (sleep_times.get(timer) - dt.now()).total_seconds()
		if sleep_time > 0:
			await ctx.send(f'Okay, I\'ll remind you in **{PRF.format_remaining_time(sleep_times.get(timer))}**')
			await asyncio.sleep(sleep_time)
			return await ctx.author.send(content=f'Your {timer} reminder is up!')
		else:
			return await ctx.send(f'Your {timer} reminder is up!')

	# Add ability to gift pokemon
	@commands.command(name='gift',
					pass_context=True,
					description='Gift another player rolls or PokeCash',
					brief='Gift players rolls or PokeCash',
					aliases=['g'],
					usage='<user> [gift]')
	async def gift(self, ctx, giftee: Member, gift: typing.Optional[str] = ''):
		user = User.get_user(ctx.author.id)
		gift_user = User.get_user(giftee.id)
		if user == gift_user:
			return await ctx.send('You can\'t gift yourself.')

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

		def is_gift_user_same_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == giftee.id

		if not gift:
			await ctx.send('Would you like to gift extra rolls or PokeCash? ')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() == 'rolls' or reply.content.lower() == 'r':
				gift = 'rolls'
			elif reply.content.lower() == 'pokecash' or reply.content.lower() == 'pc' or reply.content.lower() == 'cash' or reply.content.lower() == 'c':
				gift = 'cash'
			else:
				return await ctx.send('Can only gift rolls or cash.')

		await ctx.send(f'How {"many" if gift == "rolls" else "much"} {gift} would you like to gift?')
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		amt = float(reply.content)
		if gift == 'rolls':
			if user.stored_rolls < amt:
				return await ctx.send(f'You don\'t have that many to give (**{user.stored_rolls}** stored).')
			await ctx.send(f'<@{giftee.id}>, do you accept this gift? (y/n)')
			try:
				reply = await self.bot.wait_for('message', check=is_gift_user_same_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			user.stored_rolls -= amt
			gift_user.stored_rolls += amt
			user.total_gifts += 1
			await ctx.send(f'**{user.username}** gave **{gift_user.username}** ***{amt}*** rolls!')
			reward_str = user.reward_achievements('gifts')
			if reward_str:
				await ctx.send(reward_str)
			reward_str_tr = user.reward_achievements('stored')
			if reward_str_tr:
				await ctx.send(reward_str_tr)
			user.update()
			gift_user.update()
		if user.pokecash < amt:
			return await ctx.send(f'You don\'t have that many to give (**{user.pokecash}** in your wallet).')
		await ctx.send(f'<@{giftee.id}>, do you accept this gift? (y/n)')
		try:
			reply = await self.bot.wait_for('message', check=is_gift_user_same_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		user.pokecash -= amt
		gift_user.pokecash += amt
		gift_user.total_pokecash += amt
		user.total_gifts += 1
		await ctx.send(f'**{user.username}** gave **{gift_user.username}** ***{amt}*** PokeCash!')
		reward_str = user.reward_achievements('gifts')
		if reward_str:
			await ctx.send(reward_str)
		reward_str_tr = user.reward_achievements('pokecash')
		if reward_str_tr:
			await ctx.send(reward_str_tr)
		user.update()
		gift_user.update()

	@commands.group(name='badge',
					pass_context=True,
					invoke_without_command=True,
					description='Trade in 10 of a single Pokemon for a badge on your stats page',
					brief='Trade 10 of a pokemon for a badge',
					usage='<pkmn>')
	async def badge_main(self, ctx, *name):
		user = User.get_user(ctx.author.id)
		if not name:
			badges = Pokemon.get_badges(user)
			badges.sort(key=lambda x: x.id)
			badges.sort(key=lambda x: x.level, reverse=True)
			badges.sort(key=lambda x: x.amount, reverse=True)
			badge_displays = [b.display for b in badges]
			badge_chunks = list(PRF.chunk(badge_displays, 15))
			pages = [PRF.Page('Badges', '\n'.join(bc), colour=(58, 92, 168), icon=ctx.author.avatar_url) for bc in badge_chunks]
			return await self.paginated_embeds(ctx, pages)
		pkmn = Pokemon.get_pokemon(name)
		if not pkmn:
			return await ctx.send('No pokemon with that name or id.')
		pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
		if not pkdx:
			return await ctx.send('You don\'t own that pokemon.')
		user_badge = Pokemon.get_badge(user, pkmn.id)
		if not user_badge:
			user_badge = Pokemon.Badge(user.id, 0, 0, **pkmn.to_dict())
			badge_amount = 10 - user.get_upgrade('fasterbadge')
			badge_level = 'Bronze'
		elif user_badge.level == 1:
			badge_amount = 15 - user.get_upgrade('fasterbadge')
			badge_level = 'Silver'
		elif user_badge.level == 2:
			badge_amount = 20 - user.get_upgrade('fasterbadge')
			badge_level = 'Gold'
		else:
			badge_amount = 25 - user.get_upgrade('fasterbadge')
			badge_level = 'Gold+'
		if pkdx.amount < badge_amount:
			return await ctx.send(f'You need **{badge_amount}** for the **{badge_level} {pkmn.name}** badge, you have **{pkdx.amount}**')
		user_badge.level += 1
		if user_badge.level > 4: # level 4 is 1 Gold+ badge
			user_badge.amount += 1
		else:
			user_badge.amount = 1
		pkdx.amount -= badge_amount
		if user_badge.level == 3:
			cash_value = PRF.rarity_info[pkmn.rarity]['cash'] * 25
			roll_value = PRF.rarity_info[pkmn.rarity]['rolls'] * 25
			user.pokecash += cash_value
			user.total_pokecash += cash_value
			user.stored_rolls += roll_value
			await ctx.send(f'You got the **{badge_level} {pkmn.name}** badge, **{roll_value}** rolls, and **{cash_value}** PokeCash!\n(**{user.stored_rolls}** stored and **{user.pokecash}** in your wallet).')
		elif user_badge.level == 4:
			cash_value = PRF.rarity_info[pkmn.rarity]['cash'] * 40
			roll_value = PRF.rarity_info[pkmn.rarity]['rolls'] * 40
			user.pokecash += cash_value
			user.total_pokecash += cash_value
			user.stored_rolls += roll_value
			await ctx.send(f'You got the **{badge_level} {pkmn.name}** badge, **{roll_value}** rolls, and **{cash_value}** PokeCash!\n(**{user.stored_rolls}** stored and **{user.pokecash}** in your wallet).')
		else:
			await ctx.send(f'You got the **{badge_level} {pkmn.name}** badge!')
		if user_badge.level == 1:
			Pokemon.add_badge(user, pkmn.id)
		else:
			user_badge.update()
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, [pkdx])
		reward_str = user.reward_achievements('badges', 'pokecash', 'stored')
		if reward_str:
			await ctx.send(reward_str)

	@badge_main.command(name='all',
					pass_context=True,
					description='Trade in 10 of a single Pokemon for a badge on your stats page',
					brief='Trade 10 of a pokemon for a badge')
	async def badge_all(self, ctx):
		user = User.get_user(ctx.author.id)
		pkmn_to_release = Pokemon.get_duplicate_pokedex_extries(user, 9)
		if not pkmn_to_release:
			return await ctx.send(f'You have no duplicate pokemon')
		total_cash = 0
		total_rolls = 0
		total_badges = 0
		for pkdx in pkmn_to_release:
			user_badge = Pokemon.get_badge(user, pkdx.id)
			if not user_badge:
				user_badge = Pokemon.Badge(user.id, 0, 0, id=pkdx.id, name=pkdx.name, rarity=pkdx.rarity)
				badge_amount = 10 - user.get_upgrade('fasterbadge')
				badge_level = 'Bronze'
			elif user_badge.level == 1:
				badge_amount = 15 - user.get_upgrade('fasterbadge')
				badge_level = 'Silver'
			elif user_badge.level == 2:
				badge_amount = 20 - user.get_upgrade('fasterbadge')
				badge_level = 'Gold'
			else:
				badge_amount = 25 - user.get_upgrade('fasterbadge')
				badge_level = 'Gold+'
			if pkdx.amount < badge_amount:
				continue
			user_badge.level += 1
			total_badges += 1
			if user_badge.level > 4: # level 4 is 1 Gold+ badge
				user_badge.amount += 1
			else:
				user_badge.amount = 1
			pkdx.amount -= badge_amount
			if user_badge.level == 3:
				total_cash += PRF.rarity_info[pkdx.rarity]['cash'] * 25
				total_rolls += PRF.rarity_info[pkdx.rarity]['rolls'] * 25
			elif user_badge.level == 4:
				total_cash += PRF.rarity_info[pkdx.rarity]['cash'] * 40
				total_rolls += PRF.rarity_info[pkdx.rarity]['rolls'] * 40
			if user_badge.level == 1:
				Pokemon.add_badge(user, pkdx.id)
			else:
				user_badge.update()
		user.stored_rolls += total_rolls
		user.pokecash += total_cash
		user.total_pokecash += total_cash
		user.update()
		await ctx.send(f'You earned **{total_badges}** badges, **{total_rolls}** rolls, and **{total_cash}** pokecash! (**{user.pokecash}** in wallet and **{user.stored_rolls}** stored).')
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, pkmn_to_release)
		reward_str = user.reward_achievements('badges', 'pokecash', 'stored')
		if reward_str:
			await ctx.send(reward_str)
		return await self.badge_main(ctx)

	@commands.command(name='ditto',
					pass_context=True,
					description='Gives you a random pokemon that you already own',
					brief='Gives you a pokemon you own')
	async def ditto(self, ctx):
		user = User.get_user(ctx.author.id)
		if user._ditto_reset > dt.now():
			return await ctx.send(f'Ditto can duplicate a Pokemon in **{PRF.format_remaining_time(user._ditto_reset)}**')
		pkdxs = Pokemon.get_user_pokedex(user)
		pkdx = choice(pkdxs)
		ditto_ = Pokemon.get_user_pokedex_entry(user, Pokemon.get_pokemon_by_name('Ditto'))
		pkdx.amount += 1 + 1 if ditto_ else 1
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, [pkdx])
		user._ditto_reset = dt.now() + td(hours=16 - user.get_upgrade('dittocooldown'))
		user.update()
		return await self.paginated_embeds(ctx, [pkdx.embed(user)], content=f'You got another **{pkdx.name}**')

	@commands.command(name='achievements',
					pass_context=True,
					description='Shows all the achievements and their requirements',
					brief='Achievements',
					aliases=['a', 'ach'],
					usage='[user] [category]')
	async def achievements(self, ctx, user: typing.Optional[Member] = None, *category):
		avatar = user.avatar_url if user else ctx.author.avatar_url
		user = User.get_user(user.id) if user else User.get_user(ctx.author.id)
		reward_str = user.reward_achievements(*list(User.default_achievements.keys()))
		if reward_str:
			if len(reward_str) >= 2000:
				await ctx.send('You got a lot of achievements and rewards!')
			else:
				await ctx.send(reward_str)
		log.debug(user.username)
		log.debug(str(user._achievements))
		category = ' '.join(category).lower()
		if category:
			if category not in PRF.achievement_requirements.keys():
				return await ctx.send('That isn\'t a category')
			tmp = f'{PRF.achievement_descriptions[category]}\n\n'
			for rank, req in PRF.achievement_requirements[category].items():
				tmp += f'{":white_check_mark: " if user.has_achievement(category, rank) else ":heavy_minus_sign: "}{"bOofs" if category == "boofs" else category.capitalize()} {rank}: {req}\n'
			page = PRF.Page(f'{user.username}\'s Achievements', tmp, colour=(255, 203, 5), title="bOofs" if category == "boofs" else category.capitalize(), icon=avatar)
			return await self.paginated_embeds(ctx, page)
		pages = []
		for category, ach in PRF.achievement_requirements.items():
			tmp = f'{PRF.achievement_descriptions[category]}\n\n'
			for rank, req in ach.items():
				tmp += f'{":white_check_mark: " if user.has_achievement(category, rank) else ":heavy_minus_sign: "}{"bOofs" if category == "boofs" else category.capitalize()} {rank}: {req}\n'
			pages.append(PRF.Page(f'{user.username}\'s Achievements', tmp, colour=(255, 203, 5), title="bOofs" if category == "boofs" else category.capitalize(), icon=avatar))
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='pokehunt',
					pass_context=True,
					description='Hunt a pokemon to increase the chance you catch it',
					brief='Hunt a specific pokemon',
					aliases=['ph', 'hunt'],
					usage='<pkmn>')
	async def pokehunt(self, ctx, *name):
		user = User.get_user(ctx.author.id)
		name = ' '.join(name)
		hunting = Pokemon.get_pokemon(user._hunting['poke_id'])
		if hunting and not name:
			return await ctx.send(f'You are currently hunting **{hunting.name}** and your streak is ***{user._hunting["caught"]}***')
		if not name:
			return await ctx.send('You are not hunting a pokemon, use **.pokehunt <name>** to hunt a pokemon')
		pkmn = Pokemon.get_pokemon(name)
		if not pkmn:
			return await ctx.send('No pokemon with that name or id.')
		if hunting:
			if pkmn == hunting:
				return await ctx.send(f'You are already hunting **{pkmn.name}**')
			await ctx.send(f'You are currently hunting **{hunting.name}**, do you want to hunt **{pkmn.name}** instead? (y/n)')

			def is_same_user_channel(msg):
				return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() != 'y':
				return await ctx.send(f'You keep hunting **{hunting.name}**')
		user._hunting = {'poke_id': pkmn.id, 'caught': 0}
		await ctx.send(f'You are now hunting **{pkmn.name}**')
		user.update()

	@commands.command(name='options',
					pass_context=True,
					description='Sets or shows your options',
					brief='Sets or shows your options',
					usage='[option] [value]')
	async def options(self, ctx, setting: typing.Optional[str] = '', value: typing.Optional[str] = ''):
		user = User.get_user(ctx.author.id)
		setting = setting.lower()
		value = value.lower()
		if not setting or setting not in ['wtconfirm']:
			return await ctx.send(f'Your current settings are\nWTConfirm: **{user._options["wtconfirm"]}**')
		if setting and not value:
			return await ctx.send(f'Your current setting is **{user._options[setting]}**')
		if setting == 'wtconfirm':
			if value == 'y':
				user._options['wtconfirm'] = 'y'
			elif value == 'n':
				user._options['wtconfirm'] = 'n'
			else:
				return await ctx.send('That is not a valid option (**y** or **n**).')
			await ctx.send(f'Set WTConfirm to **{value}**')
			user.update()

	@commands.command(name='stars',
					pass_context=True,
					description='Shows the rarity of a pokemon',
					brief='Shows rarity',
					usage='<pkmn>')
	async def stars(self, ctx, *name):
		pkmn = Pokemon.get_pokemon(name)
		if not pkmn:
			return await ctx.send('No pokemon with that name or id.')
		return await ctx.send(f'**{pkmn.name}** {":star:" * pkmn.rarity}')

	@commands.group(name='party',
					pass_context=True,
					invoke_without_command=True,
					description='Shows or sets your current party',
					brief='Shows or sets your current party',
					usage='<pkmn>/<pkmn>/...')
	async def party_main(self, ctx, *pkmn_names):
		user = User.get_user(ctx.author.id)
		pkmn_names = ' '.join(pkmn_names)
		if not pkmn_names:
			user.refresh_party()
			log.debug(f'in party command: {str(user._party)}')
			desc = ''
			if user.has_party:
				pages = [gen_party_embed(user, user._party, icon=ctx.author.avatar_url)]
				for pkbt in user._party:
					pages.append(pkbt.embed(user))
			return await self.paginated_embeds(ctx, pages)
		pkmn_list = [(pkmn_name, Pokemon.get_pokemon(pkmn_name)) for pkmn_name in pkmn_names.split('/')]
		adding = []
		removing = []
		for name, pkmn in pkmn_list:
			if not pkmn:
				await ctx.send(f'No pokemon {name} found.')
				continue
			if pkmn in user._party:
				removing.append(pkmn)
			else:
				adding.append(pkmn)
		if removing:
			await ctx.send(f'Do you want to remove **{", ".join([p.name for p in removing])}** from your party? (y/n)')

			def is_same_user_channel(msg):
				return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() != 'y':
				await ctx.send(f'You keep **{", ".join([p.name for p in removing])}** in your party.')
			else:	
				for p in removing:
					idx = user._party.index(p)
					user._party.pop(idx)
		if adding:
			added = []
			for pkmn in adding:
				if pkmn:
					if len(user._party) >= 6:
						break
					if pkmn in user._party:
						continue
					if not Pokemon.get_user_pokedex_entry(user, pkmn):
						await ctx.send(f'You don\'t have {pkmn.name}')
						continue
					pkbt = Pokemon.get_user_poke_battle(user, pkmn.id)
					if not pkbt:
						pkbt = Pokemon.create_user_poke_battle(user, pkmn)
					user._party.append(pkbt)
		user.update()
		user.refresh_party()
		if user.has_party:
			pages = [gen_party_embed(user, user._party, icon=ctx.author.avatar_url)]
			for pkbt in user._party:
				pages.append(pkbt.embed(user))
		return await self.paginated_embeds(ctx, pages)

	@party_main.command(name='clear',
					pass_context=True,
					description='Shows or sets your current party',
					brief='Shows or sets your current party')
	async def party_clear(self, ctx):
		user = User.get_user(ctx.author.id)

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

		await ctx.send('Do you want to clear your entire party? (y/n)')
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		if reply.content.lower() != 'y':
			return await ctx.send(f'You keep your party.')
		user._party = []
		await ctx.send('You cleared your party!')
		return user.update()

	@commands.command(name='battle',
					pass_context=True,
					description='Battles your party against another player or a random user',
					brief='Pokemon battle',
					aliases=['bt'],
					usage='[user]')
	async def battle(self, ctx, opponent: typing.Optional[Member] = None):
		user = User.get_user(ctx.author.id)
		if not user.has_party:
			return await ctx.send('You have to have pokemon in your party to battle (**.party**).')
		if opponent:
			opponent = User.get_user(opponent.id) 
			if not opponent.has_party:
				return await ctx.send(f'{opponent.username} has no pokemon in their party.')
		else:
			if user._battle_reset > dt.now():
				return await ctx.send(f'You can battle again in **{PRF.format_remaining_time(user._battle_reset)}**')
			opponent = Battling.Trainer(len(user._party), user.avg_party_level, user.avg_party_rarity)
			log.debug(str(opponent._party))
		battle = Battling.BattleLog(user, opponent)
		result_str = ''
		if isinstance(opponent, User.User):
			result_str += f'<@{battle.winner.id}> won!'
		else:
			rewards = ''
			user.total_battles += 1
			user_lost = isinstance(battle.winner, Battling.Trainer)
			rewards += f'You lost!\n' if user_lost else f'You won! Your party earned ***{battle.exp}*** exp!\n'
			user.pokecash += battle.cash
			user.total_pokecash += battle.cash
			rewards += f'You got **{battle.cash}** PokeCash! Spend it wisely! (**{user.pokecash}** in wallet).\n'
			user.stored_rolls += battle.rolls
			rewards += f'You got **{battle.rolls}** extra rolls! (**{user.stored_rolls}** stored).'
			level_up_str = user.add_exp_to_party(battle.exp)
			if level_up_str:
				await ctx.send(level_up_str)
			user._battle_reset = dt.now() + td(minutes=(120 - 10 * user.get_upgrade('battlecooldown')))
			user.update()
		reward_str = user.reward_achievements('battles', 'levels')
		if reward_str:
			await ctx.send(reward_str)
		user.update()
		return await self.paginated_embeds(ctx, battle.pages, rewards)

	@commands.group(name='daycare',
					pass_context=True,
					invoke_without_command=True,
					description='Put a pokemon into the daycare for daily rewards',
					brief='Pokemon daycare',
					aliases=['dc'],
					usage='[pkmn or claim]')
	async def daycare_main(self, ctx, *name):
		user = User.get_user(ctx.author.id)
		name = ' '.join(name)
		if not name:
			pkdc = Pokemon.get_user_daycare(user)
			if not pkdc:
				return await ctx.send('You have nothing in the daycare.\nTo add a pokemon use **.daycare <pkmn>**')
			else:
				pkdc.generate_rewards(user.get_upgrade('daycaretime'))
				return await self.paginated_embeds(ctx, pkdc.embed(user))		
		pkmn = Pokemon.get_pokemon(name)
		if not pkmn:
			return await ctx.send('No pokemon with that name or id.')
		pkdc = Pokemon.get_user_daycare(user)
		pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
		if not pkdx:
			return await ctx.send('You can\'t put a pokemon in the daycare that you don\'t own.')
		if pkdc:
			if pkdc == pkdx:
				return await ctx.send(f'**{pkmn.name}** is already in the daycare.')
			await ctx.send(f'**{pkdc.name}** is currently in the daycare, do you want to put **{pkmn.name}** in instead? (y/n)')

			def is_same_user_channel(msg):
				return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() != 'y':
				return await ctx.send(f'You keep **{pkdc.name}** in the daycare')
			else:
				if pkdc:
					pkdc.generate_rewards(user.get_upgrade('daycaretime'))
					daycare_str = ''
					for reward, value in pkdc._rewards.items():
						if reward == 'levels':
							pkbt = Pokemon.get_user_poke_battle(user, pkdc.id)
							if not pkbt:
								pkbt = Pokemon.create_user_poke_battle(user, pkdc)
							for _ in range(value):
								pkbt.level_up()
							pkbt.update()
							daycare_str += f'***{value}*** levels, '
						if reward == 'rolls':
							user.stored_rolls += value
							daycare_str += f'and ***{value}*** rolls.'
						if reward == 'cash':
							user.pokecash += value
							user.total_pokecash += value
							daycare_str += f'***{value}*** PokeCash, '
					user.update()
					await ctx.send(f'You claimed your **{pkdc.name}** and got {daycare_str}')
					reward_str = user.reward_achievements('stored', 'pokecash')
					if reward_str:
						await ctx.send(reward_str)
		Pokemon.delete_user_daycare(user)
		pkdc = Pokemon.create_user_daycare(user, pkmn)
		await ctx.send(f'**{pkmn.name}** is now in the daycare.')
		user.update()

	@daycare_main.command(name='claim',
					pass_context=True,
					description='Put a pokemon into the daycare for daily rewards',
					brief='Pokemon daycare')
	async def daycare_claim(self, ctx):
		user = User.get_user(ctx.author.id)
		pkdc = Pokemon.get_user_daycare(user)
		if not pkdc:
			return await ctx.send('You have nothing in the daycare.')
		pkdc.generate_rewards(user.get_upgrade('daycaretime'))
		daycare_str = ''
		for reward, value in pkdc._rewards.items():
			if reward == 'levels':
				pkbt = Pokemon.get_user_poke_battle(user, pkdc.id)
				if not pkbt:
					pkbt = Pokemon.create_user_poke_battle(user, pkdc)
				for _ in range(value):
					pkbt.level_up()
				pkbt.update()
				daycare_str += f'***{value}*** levels, '
			if reward == 'rolls':
				user.stored_rolls += value
				daycare_str += f'and ***{value}*** rolls.'
			if reward == 'cash':
				user.pokecash += value
				user.total_pokecash += value
				daycare_str += f'***{value}*** PokeCash, '
		user.update()
		await ctx.send(f'You claimed your **{pkdc.name}** and got {daycare_str}')
		reward_str = user.reward_achievements('stored', 'pokecash')
		if reward_str:
			await ctx.send(reward_str)
		return Pokemon.delete_user_daycare(user)

	@commands.group(name='savelist',
					pass_context=True,
					invoke_without_command=True,
					description='Saves pokemon from being released by the autorelease commands',
					brief='Saves pokemon from autorelease',
					aliases=['sl'],
					usage='<pkmn>/<pkmn>/...')
	async def savelist_main(self, ctx, *pkmn_names):
		user = User.get_user(ctx.author.id)
		pkmn_names = ' '.join(pkmn_names)
		if not pkmn_names:
			if not user._savelist:
				return await ctx.send('No pokemon in your savelist.')
			pkmn_names = [Pokemon.get_pokemon_by_id(pksl).name for pksl in user._savelist]
			pkmn_names.sort()
			pages = [PRF.Page(f'{user.username}\'s Save List', pc, icon=ctx.author.avatar_url) for pc in PRF.chunk(pkmn_names, 15)]
			return await self.paginated_embeds(ctx, pages)
		pkmn_list = [Pokemon.get_pokemon(pkmn_name) for pkmn_name in pkmn_names.split('/')]
		adding = []
		removing = []
		for pkmn in pkmn_list:
			if pkmn.id in user._savelist:
				removing.append(pkmn)
			else:
				adding.append(pkmn)
		if adding:
			user._savelist.extend(p.id for p in adding)
			await ctx.send(f'Added **{", ".join([p.name for p in adding])}** to your save list')
			user.update()
		if removing:
			await ctx.send(f'Do you want to remove **{", ".join([p.name for p in removing])}** from your save list? (y/n)')

			def is_same_user_channel(msg):
				return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() != 'y':
				return await ctx.send(f'You keep **{", ".join([p.name for p in removing])}** in your save list.')
			for p in removing:
				idx = user._savelist.index(p.id)
				user._savelist.pop(idx)
			user.update()
			return await ctx.send(f'You removed **{", ".join([p.name for p in removing])}** from your save list')

	@savelist_main.command(name='clear',
					pass_context=True,
					invoke_without_command=True,
					description='Saves pokemon from being released by the autorelease commands',
					brief='Saves pokemon from autorelease')
	async def savelist_clear(self, ctx):
		user = User.get_user(ctx.author.id)

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

		await ctx.send('Do you want to clear your entire savelist? (y/n)')
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		if reply.content.lower() != 'y':
			return await ctx.send(f'You keep your save list.')
		user._savelist = []
		await ctx.send('You cleared your save list!')
		return user.update()

	@commands.command(name='gym',
					pass_context=True,
					description='Challenges gyms for gym badges and rewards',
					brief='Challenge gyms',
					usage='[slot]')
	async def gym(self, ctx, slot: typing.Optional[int] = 0):
		user = User.get_user(ctx.author.id)
		slot = slot if 1 <= slot <= 8 else 0
		if not slot:
			desc = 'Welcome to the Gyms! Here you can challenge a gym for gym badges and rewards.\n'
			desc += 'Here is the list of gyms. To chalenge a gym, use **.gym <slot no.>**\n\n'
			leaders = [(k, v()) for k, v in Battling.gym_leaders.items()]
			leaders.sort(key=lambda x: x[0])
			for slot, leader in leaders:
				desc += f'{"~~" if slot in user._gyms else ""}**{slot}: {leader.name}** - Recommended lvl _{leader.avg_party_level}_{"~~" if slot in user._gyms else ""}\n'
			page = PRF.Page('Gyms', desc, icon='https://cdn.bulbagarden.net/upload/1/15/Gym_Symbol.png')
			return await self.paginated_embeds(ctx, page)
		if not user.has_party:
			return await ctx.send('You have to have pokemon in your party to challenge a gym (**.party**).')
		if slot in user._gyms:
			return await ctx.send('You already beat this gym.')
		beaten = max(user._gyms) if user._gyms else 0
		if slot - beaten > 1:
			return await ctx.send('You have to beat the gym before this one to challenge it.')
		if user._gym_reset > dt.now():
			return await ctx.send(f'You can challenge the gym again in **{PRF.format_remaining_time(user._gym_reset)}**')
		rewards = ''
		leader = Battling.gym_leaders[slot]()
		battle = Battling.BattleLog(user, leader)
		if isinstance(battle.winner, Battling.Trainer):
			rewards += f'You lost to **{leader.name}**\n'
			user._gym_reset = dt.now() + td(hours=16)
			user.update()
		else:
			rewards += f'You beat **{leader.name}**!\n'
			user._gyms.append(slot)
		user.total_pokecash += battle.cash
		user.stored_rolls += battle.rolls
		rewards += f'Your party gained **{battle.exp}** exp and you got **{battle.rolls}** rolls and **{battle.cash}** PokeCash! (**{user.pokecash}** in wallet, **{user.stored_rolls}** rolls stored).'
		user.update()
		level_up_str = user.add_exp_to_party(battle.exp)
		if level_up_str:
			await ctx.send(level_up_str)
		reward_str = user.reward_achievements('stored', 'pokecash', 'gyms', 'levels')
		if reward_str:
			await ctx.send(reward_str)
		return await self.paginated_embeds(ctx, battle.pages, rewards)

	@commands.command(name='elitefour',
					pass_context=True,
					description='Challenges the Elite Four',
					brief='Challenge the Elite Four',
					aliases=['e4'])
	async def elitefour(self, ctx):
		user = User.get_user(ctx.author.id)
		if not user.has_party:
			return await ctx.send('You have to have pokemon in your party to challenge a gym (**.party**).')
		if 8 not in user._gyms:
			return await ctx.send('You must beat all gyms to challenge the Elite Four.')
		if user._e4_reset > dt.now():
			return await ctx.send(f'You can challenge the Elite Four again in **{PRF.format_remaining_time(user._e4_reset)}**')
		total_exp = 0
		total_rolls = 0
		total_cash = 0
		wins = 0
		rewards = ''
		battles = []
		for e4_member_func in Battling.elite_four.values():
			e4_member = e4_member_func()
			battle = Battling.BattleLog(user, e4_member)
			if isinstance(battle.winner, Battling.Trainer):
				rewards += f'You lost to Elite Four **{e4_member.name}**\n'
				battles.append(battle)
				break
			else:
				user.heal_party()
				wins += 1
				battles.append(battle)
		total_exp += sum([battle.exp for battle in battles])
		total_cash += sum([battle.cash for battle in battles])
		total_rolls += sum([battle.rolls for battle in battles])
		user._e4_reset = dt.now() + td(hours=(16 - 1 * user.get_upgrade('e4cooldown')))
		user.pokecash += total_cash
		user.total_pokecash += total_cash
		user.stored_rolls += total_rolls
		user.update()
		win_str = ''
		if wins == 5:
			rewards += 'You beat the Elite Four!\n'
			user.e4_completions += 1
		else:
			rewards += f'For beating {wins}/5 Elite Four members\n'
		rewards += f'Your party earned **{total_exp}** exp, and you earned **{total_rolls}** rolls and **{total_cash}** PokeCash! (**{user.pokecash}** in wallet, **{user.stored_rolls}** rolls stored).'
		level_up_str = user.add_exp_to_party(total_exp)
		if level_up_str:
			await ctx.send(level_up_str)
		reward_str = user.reward_achievements('stored', 'pokecash', 'elite four', 'levels')
		if reward_str:
			await ctx.send(reward_str)
		pages = []
		for battle in battles:
			pages.extend(battle.pages)
		return await self.paginated_embeds(ctx, pages, rewards)

	@commands.command(name='pokebox',
					pass_context=True,
					description='Shows all of the pokemon that you\'ve leveled up.',
					brief='Your battle-ready pokemon',
					aliases=['pb'],
					usage='[level]')
	async def pokebox(self, ctx, level: typing.Optional[int] = 1):
		user = User.get_user(ctx.author.id)
		level = 1 if level <= 0 else level
		pkbts = Pokemon.get_all_user_poke_battle(user, level)
		pkbts = list(set(pkbts))
		pkbts.sort(key=lambda x: x.id)
		pkbts.sort(key=lambda x: x.level, reverse=True)
		pages = []
		for pl_chunk in PRF.chunk(pkbts, 15):
			desc = ''
			for pkbt in pl_chunk:
				in_party = pkbt in user._party
				if in_party:
					desc += '***'
				desc += f'{pkbt.name} - _{pkbt.level}_'
				desc += '***\n' if in_party else '\n'
			pages.append(PRF.Page(f'{user.username}\'s PokeBox', desc, icon=ctx.author.avatar_url))
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='wondertrade',
					pass_context=True,
					description='Trade a pokemon you have for a random pokemon',
					brief='Trade for a random pokemon',
					aliases=['wt'],
					usage='<pkmn>')
	async def wondertrade(self, ctx, *pkmn):
		user = User.get_user(ctx.author.id)

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
		
		if not pkmn:
			await ctx.send('What Pokemon would you like to trade?')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			pkmn = reply.content
		pkmn = Pokemon.get_pokemon(pkmn)
		if not pkmn:
			return await ctx.send('No pokemon with that name.')
		pkdx = Pokemon.get_user_pokedex_entry(user, pkmn)
		if not pkdx:
			return await ctx.send('You don\'t own that Pokemon.')
		
		def is_trade_user_same_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == trade_user_.id

		if user._options['wtconfirm'] == 'y':
			await ctx.send(f'Do you want to wondertrade **{pkmn.name}**? (y/n)')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() == 'n':
				return await ctx.send(f'You do not WonderTrade **{pkmn.name}**.')
		rarity = choices(list(range(pkmn.rarity, 7)), weights=[50 / ((i+1 - pkmn.rarity)**2) for i in range(pkmn.rarity, 7)])[0]
		trade_pkmn = Pokemon.get_random_pokemon_by_rarity(rarity)
		user_get_pkdx = Pokemon.get_user_pokedex_entry(user, trade_pkmn)
		if not user_get_pkdx:
			user_get_pkdx = Pokemon.PokedexEntry(user.id, -1, **trade_pkmn.to_dict())
		else:
			user_get_pkdx.amount += 1
		pkdx.amount -= 1
		Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(user, [pkdx, user_get_pkdx])
		user.total_traded += 1
		user._wt_reset = dt.now() + td(hours=16 - user.get_upgrade('tradecooldown'))
		reward_str = user.reward_achievements('trades', 'pokemon')
		if reward_str:
			await ctx.send(reward_str)
		user.update()
		return await self.paginated_embeds(ctx, user_get_pkdx.embed(user), f'You traded your **{pkmn.name}** for **{trade_pkmn.name}**!')

	@commands.group(name='saveparty',
					pass_context=True,
					invoke_without_command=True,
					description='Save parties for easier party swapping',
					brief='Save parties',
					aliases=['sparty', 'sp'],
					usage='[save, load, or delete] [slot]')
	async def saveparty_main(self, ctx):
		user = User.get_user(ctx.author.id)
		if not user._saved_parties:
			return await ctx.send('You have no saved parties')
		user.refresh_saved_parties()
		pages = []
		for slot, party in user._saved_parties.items():
			pages.append(gen_party_embed(user, user._saved_parties[slot], title=f'Saved Parties - {slot}', icon=ctx.author.avatar_url))
		return await self.paginated_embeds(ctx, pages)

	@saveparty_main.command(name='save',
					pass_context=True,
					invoke_without_command=True,
					description='Save parties for easier party swapping',
					brief='Save parties',
					hidden=True)
	async def saveparty_save(self, ctx, slot: typing.Optional[int] = 0):
		user = User.get_user(ctx.author.id)
		if not slot:
			if len(list(user._saved_parties.keys())) == 0:
				slot = 1
			else:
				slot = max(user._saved_parties.keys()) + 1
		if slot in user._saved_parties.keys():

			def is_same_user_channel(msg):
				return msg.channel.id == ctx.channel.id and msg.author.id == user.id
			
			page = gen_party_embed(user, user._saved_parties[slot], title=f'Saved Parties - {slot}', icon=ctx.author.avatar_url)
			await ctx.send(f'Do you want to overwrite **{slot}**? (y/n)', embed=page.embed)
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() == 'n':
				return await ctx.send(f'You do not overwrite **{slot}**.')
		user._saved_parties[slot] = user._party
		user.update()
		return await self.paginated_embeds(ctx, gen_party_embed(user, user._saved_parties[slot], title=f'Saved Parties - {slot}', icon=ctx.author.avatar_url), content=f'You saved your party to slot **{slot}**')

	@saveparty_main.command(name='load',
					pass_context=True,
					invoke_without_command=True,
					description='Save parties for easier party swapping',
					brief='Save parties',
					hidden=True)
	async def saveparty_load(self, ctx, slot: typing.Optional[int] = 0):
		user = User.get_user(ctx.author.id)
		if not slot:
			return await ctx.send('You need to choose a slot.')
		if slot not in user._saved_parties.keys():
			return await ctx.send('You don\'t have a party saved to that slot.')

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == user.id
		
		page = gen_party_embed(user, user._saved_parties[slot], title=f'Saved Parties - {slot}', icon=ctx.author.avatar_url)
		await ctx.send(f'Do you want to load **{slot}** as your current party? (y/n)', embed=page.embed)
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		if reply.content.lower() == 'n':
			return await ctx.send(f'You do not load **{slot}**.')
		user._party = user._saved_parties[slot]
		user.update()
		return await self.party_main(ctx)

	@saveparty_main.command(name='delete',
					pass_context=True,
					invoke_without_command=True,
					description='Save parties for easier party swapping',
					brief='Save parties',
					hidden=True)
	async def saveparty_delete(self, ctx, slot: typing.Optional[int] = 0):
		user = User.get_user(ctx.author.id)
		if not slot:
			return await ctx.send('You need to choose a slot.')
		if slot not in user._saved_parties.keys():
			return await ctx.send('You don\'t have a party saved to that slot.')

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == user.id
		
		page = gen_party_embed(user, user._saved_parties[slot], title=f'Saved Parties - {slot}', icon=ctx.author.avatar_url)
		await ctx.send(f'Do you want to delete **{slot}**? (y/n)', embed=page.embed)
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('Sorry, you ran out of time.')
		if reply.content.lower() == 'n':
			return await ctx.send(f'You do not delete **{slot}**.')
		del user._saved_parties[slot]
		user.refresh_saved_parties()
		return await self.saveparty_main(ctx)

	@commands.group(name='raid',
					pass_context=True,
					invoke_without_command=True,
					description='Challenge raids of varying difficulties for a chance at a mega-evolved pokemon',
					brief='Raids',
					usage='[easy, medium, or hard]')
	async def raid_main(self, ctx, difficulty: typing.Optional[str] = ''):
		user = User.get_user(ctx.author.id)
		if difficulty:
			if dt.now() < self.raid_reset:
				return await ctx.send(f'The next raid reset is in **{PRF.format_remaining_time(self.raid_reset)}**')
			if not user.has_party:
				return await ctx.send('You must have a party to initiate a raid.')
			if difficulty not in ['e', 'easy', 'm', 'medium', 'h', 'hard']:
				return await ctx.send('Raid difficulty must be one of [easy, medium, hard]')
			if self.raid['difficulty']:
				return await ctx.send(f'Someone already initiated a **{self.raid["difficulty"].capitalize()}** raid.\nUse **.raid join** to join the raid')
			if difficulty in ['e', 'easy']:
				self.raid['difficulty'] = 'easy'
			elif difficulty in ['m', 'medium']:
				self.raid['difficulty'] = 'medium'
			else:
				self.raid['difficulty'] = 'hard'
			self.raid['players'] = [user]
			self.raid['initaitor'] = user
			page = PRF.Page(f'Players in Raid - {self.raid["difficulty"].capitalize()}', user.username)
			return await self.paginated_embeds(ctx, page)
		if self.raid['difficulty']:
			pages = []
			for pc in PRF.chunk(self.raid['players'], 15):
				page = PRF.Page(f'Players in Raid - {self.raid["difficulty"].capitalize()}', [p.username for p in pc])
				pages.append(page)
			return await self.paginated_embeds(ctx, pages)
		desc = 'Welcome to Raids! Here, players can team up to take on Mega-Evolved Pokemon\n'
		desc += 'There are three difficulties: **easy, medium, and hard**. Each one pits you against\n'
		desc += 'different pokemon and gives a higher chance at receiving a Mega-Evolved Pokemon as a reward.\n'
		desc += 'To initiate a raid use **.raid <difficulty>**. If a raid has already been initiated\n'
		desc += 'use **.raid join** to join or **.raid quit** if you need to change your party.\n'
		desc += 'Once everyone who wants to join joins, the initaitor can start the raid with **.raid start**'
		if dt.now() < self.raid_reset:
			footer = f'Next available raid: {PRF.format_remaining_time(self.raid_reset)}'
		else:
			footer = 'The raid is available'
		display_pkmn = choice([p for p in Pokemon.get_all_pokemon() if p.rarity >= 7])
		page = PRF.Page('Raiding', desc, icon='https://cdn.bulbagarden.net/upload/e/e3/Bag_Tyranitarite_Sprite.png', image=display_pkmn.url, footer=footer)
		return await self.paginated_embeds(ctx, page)

	@raid_main.command(name='join',
					pass_context=True,
					description='Join an initiated raid',
					brief='Join a raid',
					usage='[easy, medium, or hard]')
	async def raid_join(self, ctx):
		if not self.raid['difficulty']:
			return await ctx.send('There is no raid going on, initiate one with **.raid <difficulty>**')
		user = User.get_user(ctx.author.id)
		if not user.has_party:
			return await ctx.send('You must have a party to join a raid.')
		if user in self.raid['players']:
			return await ctx.send('You already joined this raid.')
		self.raid['players'].append(user)
		pages = []
		for pc in PRF.chunk(self.raid['players'], 15):
			page = PRF.Page(f'Players in Raid - {self.raid["difficulty"].capitalize()}', [p.username for p in pc])
			pages.append(page)
		return await self.paginated_embeds(ctx, pages, content='You joined the raid!')

	@raid_main.command(name='quit',
					pass_context=True,
					description='Quit an initiated raid',
					brief='Quit a raid',
					usage='[easy, medium, or hard]')
	async def raid_quit(self, ctx):
		if not self.raid['difficulty']:
			return await ctx.send('There is no raid going on, initiate one with **.raid <difficulty>**')
		user = User.get_user(ctx.author.id)
		idx = self.raid['players'].index(user)
		self.raid['players'].pop(idx)
		if user == self.raid['initaitor']:
			if len(self.raid['players']) == 0:
				self.update_raid(False)
				return await ctx.send('All players quit, the raid has been canceled.')
			else:
				self.raid['initaitor'] = self.raid['players'][0]
				await ctx.send(f'{user.username} left the raid, {self.raid["initaitor"].username} is now the initaitor.')
		pages = []
		for pc in PRF.chunk(self.raid['players'], 15):
			page = PRF.Page(f'Players in Raid - {self.raid["difficulty"].capitalize()}', [p.username for p in pc])
			pages.append(page)
		return await self.paginated_embeds(ctx, pages, content='You left the raid')

	@raid_main.command(name='start',
					pass_context=True,
					invoke_without_command=True,
					description='Starts the raid with the players that joined',
					brief='Starts the raid',
					usage='[easy, medium, or hard]')
	async def raid_start(self, ctx):
		if not self.raid['difficulty']:
			return await ctx.send('There is no raid going on, initiate one with **.raid <difficulty>**')
		user = User.get_user(ctx.author.id)
		if user != self.raid['initaitor']:
			return await ctx.send(f'Only <@{self.raid["initaitor"].id}> may start the raid.')
		raid = Battling.Raid(self.raid['players'], self.raid['difficulty'])
		rewards = f'You beat the raid! Everyone earned **{raid.exp}** exp, **{raid.cash}** cash, and **{raid.rolls}** rolls\n' if raid.won else f'You lost, everyone earned **{raid.exp}** exp, **{raid.cash}** cash, and **{raid.rolls}** rolls\n'
		for player in self.raid['players']:
			player.total_raids += 1
			player.pokecash += raid.cash
			player.total_pokecash += raid.cash
			player.stored_rolls += raid.rolls
			level_up_str = player.add_exp_to_party(raid.exp)
			if level_up_str:
				await ctx.send(level_up_str)
			if raid.won:
				player.raid_completions += 1
				random_raid_pkmn = choice(raid.pokemon)
				if random() < PRF.rarity_info[random_raid_pkmn.rarity]['chance'] * (1.2 ** player.get_upgrade('raidchance')):
					pkdx = Pokemon.get_user_pokedex_entry(player, random_raid_pkmn)
					if not pkdx:
						pkdx = Pokemon.PokedexEntry(player.id, -1, id=random_raid_pkmn.id, name=random_raid_pkmn.name, rarity=random_raid_pkmn.rarity)
					else:
						pkdx.amount += 1
					Pokemon.add_or_update_user_pokedex_entry_from_pokedex_entries(player, [pkdx])
					rewards += f'{player.username} got a **{random_raid_pkmn.name}**!!\n'
			player.update()
			reward_str = user.reward_achievements('raids', 'raids complete', 'pokecash', 'stored', 'levels')
			if reward_str:
				await ctx.send(reward_str)
		self.update_raid()
		return await self.paginated_embeds(ctx, raid.pages, content=rewards)

	@commands.command(name='missing',
					pass_context=True,
					description='A list of all the pokemon you\'re missing',
					brief='Your missing pokemon',
					aliases=['m'])
	async def missing(self, ctx):
		user = User.get_user(ctx.author.id)
		pkdxs = Pokemon.get_user_pokedex(user)
		pkmns = Pokemon.get_all_pokemon()
		missing = [pkmn for pkmn in pkmns if pkmn not in pkdxs]
		missing.sort(key=lambda x: x.id)
		missing.sort(key=lambda x: x.rarity, reverse=True)
		pages = []
		for mc in PRF.chunk(missing, 15):
			desc = ''
			for pkmn in mc:
				desc += f'{pkmn.name} {":star:" * pkmn.rarity}\n'
			pages.append(PRF.Page(f'{user.username}\'s Missing Pokemon', desc))
		return await self.paginated_embeds(ctx, pages)

	@commands.command(name='favourite',
					pass_context=True,
					description='Favourite a pokemon to display on your stats pages',
					brief='Set your favourite pokemon',
					aliases=['favorite', 'f', 'fav'])
	async def favourite(self, ctx, *pkmn):
		user = User.get_user(ctx.author.id)
		fav = Pokemon.get_pokemon_by_id(user.favourite)
		if not pkmn:
			if fav:
				return await self.paginated_embeds(ctx, fav.embed(user))
			return await ctx.send('No favourite pokemon.')
		pkmn = Pokemon.get_pokemon(pkmn)
		if not pkmn:
			return await ctx.send('No pokemon with that name.')
		if fav:
			if fav == pkmn:
				return await ctx.send(f'**{pkmn.name}** is your favourite already.')
			def is_same_user_channel(msg):
				return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

			await ctx.send(f'Do you want to replace **{fav.name}** as your favourite? (y/n)')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('Sorry, you ran out of time.')
			if reply.content.lower() != 'y':
				return await ctx.send(f'You keep **{fav.name}** as your favourite.')
		user.favourite = pkmn.id
		user.update()
		return await self.paginated_embeds(ctx, pkmn.embed(user))
