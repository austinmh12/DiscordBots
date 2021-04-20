from datetime import datetime as dt, timedelta as td
from discord.ext import commands
import asyncio
from . import *
import logging
import re
import typing
from discord import Member, Embed, Colour

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

class Pokemons(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.poke_reset = self.get_poke_reset()

	# Utilities
	def get_poke_reset(self):
		df = sql('SELECT MAX(poke_reset) as poke_reset FROM poke_info', ())
		poke_reset = df.poke_reset[0]
		if not poke_reset:
			tmp = dt(2020, 10, 8, 23)
			while tmp < dt.now():
				tmp += td(seconds=3600*2)
			return tmp
		while poke_reset < dt.now():
			poke_reset += td(seconds=3600*2)
		return poke_reset

	def update_boofs(self, user, amt=1):
		user_id = get_user_id(user)
		boofs = self.get_boofs(user)
		return sql('UPDATE poke_info SET boofs = %s WHERE user_id = %s', (boofs + amt, user_id,))

	def get_boofs(self, user):
		user_id = get_user_id(user)
		df = sql('SELECT boofs FROM poke_info WHERE user_id = %s', (user_id,))
		if df.empty:
			return 0
		return int(df.boofs[0])

	def get_leaderboard(self):
		return sql('SELECT u.user_name, pi.boofs FROM users u INNER JOIN poke_info pi ON pi.user_id = u.id WHERE pi.boofs is not null AND pi.boofs != 0', ())

	# Listeners
	@commands.Cog.listener()
	async def on_message(self, m):
		if m.channel.id != waifu_channel and m.author == self.bot.user:
			return

		if not get_user_id(m.author.id) and m.author.id != mudae_id and m.author != self.bot.user:
			add_user(m.author.id, m.author.name)

		def is_mudae_reply(msg):
			return m.channel.id == msg.channel.id and msg.author.id == mudae_id

		if m.content == '$p' or m.content == '$pokemon':
			try:
				tu_reply = await self.bot.wait_for('message', check=is_mudae_reply, timeout=300)
			except asyncio.TimeoutError:
				tu_reply = None
			if tu_reply:
				if 'One try' in tu_reply.content: # Timer not ready
					_, time_remaining, _ = tu_reply.content.split('**')
					if 'h' in time_remaining:
						hrs, min_ = time_remaining.split('h ')
					else:
						hrs = 0
						min_ = time_remaining
					poke_reset = (dt.now() + td(seconds=int(hrs)*3600 + int(min_)*60)).replace(second=0, microsecond=0)
					if self.poke_reset < poke_reset:
						self.poke_reset = poke_reset
					update_user_timer(m.author.id, 'poke_reset', 'poke_info', self.poke_reset)
				emoji_str = tu_reply.content.encode('unicode_escape').decode()
				if '<:filmframe' in tu_reply.content or '\u274c' in tu_reply.content or '\U0001f514' in tu_reply.content: # Player Rolled
					self.poke_reset = self.get_poke_reset()
					update_user_timer(m.author.id, 'poke_reset', 'poke_info', self.poke_reset)
					try:
						tu_reply = await self.bot.wait_for('message', check=is_mudae_reply, timeout=300)
					except asyncio.TimeoutError:
						tu_reply = None
					if tu_reply:
						if 'nothing' in tu_reply.content: # Player got nothing, bOof
							await m.channel.send('bOof')
							self.update_boofs(m.author.id)

		if m.author.id == mudae_id and m.embeds:
			await asyncio.sleep(.3)
			if not m.reactions:
				await m.add_reaction('\u2764')

	# Commands
	@commands.command(name='mudaeboofs',
					pass_context=True,
					description='See your total pokeboofs',
					brief='Total pokeboofs',
					aliases=['mb','boof','bOof','bOofs'])
	async def mudae_boofs(self, ctx, user: typing.Optional[Member] = None):
		boofs = self.get_boofs(user.id) if user else self.get_boofs(ctx.message.author.id)
		return await ctx.channel.send(f'<@{user.id if user else ctx.message.author.id}> has {boofs} Mudae PokebOofs.{" Nice." if boofs == 69 else ""}')

	@commands.command(name='mudaeboofleaderboard',
					pass_context=True,
					description='The leaderboards for pokeboofs',
					brief='Pokeboof leaderboard',
					aliases=['mbl', 'pblb', 'bOofleaderboard', 'bOoflb', 'bOofl'])
	async def mudae_boof_leaderboard(self, ctx):
		df = self.get_leaderboard()
		df.sort_values(by='boofs', inplace=True, ascending=False)
		desc = ''
		for i, (user, boofs) in enumerate(df.values.tolist(), start=1):
			if i == 1:
				i = ':first_place:'
			elif i == 2:
				i = ':second_place:'
			elif i == 3:
				i = ':third_place:'
			else:
				i = f'**#{i}**'
			desc += f'{i}: {user} - {boofs}{" Nice." if boofs == 69 else ""}\n'
		emb = Embed(
				title='Mudae PokebOof Leaderboard',
				description=desc,
				colour=Colour.from_rgb(255, 50, 50)
			)
		try:
			rank = list(df['user_name']).index(ctx.author.name) + 1
		except ValueError:
			rank = 0
		if rank:
			emb.set_footer(text=f'You are ranked #{rank}')
		return await ctx.channel.send(embed=emb)

	@commands.command(name='add_boofs',
					pass_context=True,
					description='See your total pokeboofs',
					brief='Total pokeboofs',
					aliases=['ab'])
	async def add_boofs(self, ctx, amt, user: typing.Optional[Member] = None):
		if ctx.message.author.id != 223616191246106624 or ctx.message.author == self.bot.user:
			return
		user_id = user.id if user else ctx.message.author.id
		self.update_boofs(user_id, int(amt))
		boofs = self.get_boofs(user_id)
		return await ctx.send(f'<@{user_id}> now has {boofs} PokebOofs.{" Nice." if boofs == 69 else ""}')

	@commands.command(name='remove_boofs',
					pass_context=True,
					description='See your total pokeboofs',
					brief='Total pokeboofs',
					aliases=['rb'])
	async def remove_boofs(self, ctx, amt, user: typing.Optional[Member] = None):
		if ctx.message.author.id != 223616191246106624 or ctx.message.author == self.bot.user:
			return
		user_id = user.id if user else ctx.message.author.id
		self.update_boofs(user_id, -int(amt))
		boofs = self.get_boofs(user_id)
		return await ctx.send(f'<@{user_id}> now has {boofs} PokebOofs.{" Nice." if boofs == 69 else ""}')