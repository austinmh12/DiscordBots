from datetime import datetime as dt, timedelta as td
from discord.ext import commands
import asyncio
from . import *
import logging
import re
import pandas as pd

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

class Waifus(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.claim_reset = self.get_claim_reset()
		self.roll_reset = self.get_roll_reset()

	# Utilities
	def get_claim_reset(self):
		df = sql('SELECT MAX(claim_reset) as claim_reset FROM waifu_info', ())
		claim_reset = df.claim_reset[0]
		if not claim_reset:
			tmp = dt(2020, 10, 8, 22, 58)
			while tmp < dt.now():
				tmp += td(seconds=3600*3)
			return tmp
		while claim_reset < dt.now():
			claim_reset += td(seconds=3600*3)
		return claim_reset

	def get_roll_reset(self):
		df = sql('SELECT MAX(rolls_reset) as roll_reset FROM waifu_info', ())
		roll_reset = df.roll_reset[0]
		if not roll_reset:
			tmp = dt(2020, 10, 8, 22, 58)
			while tmp < dt.now():
				tmp += td(seconds=3600*1)
			return tmp
		while roll_reset < dt.now():
			roll_reset += td(seconds=3600*1)
		return roll_reset

	def format_remaining_time(self, time):
		hrs, rem = divmod(time.total_seconds(), 3600)
		min_ = rem // 60 + 1
		if hrs:
			return f'{int(hrs)}h {int(min_)}min'
		return f'{int(min_)}min'

	def parse_tu(self, tu):
		claim_sent, _, rolls_sent, daily_sent, _, react_sent, _, _, _, kakera_sent = tu.split('\n')
		if 'can claim right now' in claim_sent:
			claim_reset = dt.now().replace(second=0, microsecond=0)
		else:
			*_, time_remaining, _ = claim_sent.split('**')
			if 'h' in time_remaining:
				hrs, min_ = time_remaining.split('h ')
			else:
				hrs = 0
				min_ = time_remaining
			claim_reset = (dt.now() + td(seconds=int(hrs)*3600 + int(min_)*60)).replace(second=0, microsecond=0)
		_, time_remaining, _ = rolls_sent.split('**')
		roll_reset = (dt.now() + td(seconds=int(time_remaining)*60)).replace(second=0, microsecond=0)
		if 'available' in daily_sent:
			daily_reset = dt.now().replace(second=0, microsecond=0)
		else:
			_, time_remaining, _ = daily_sent.split('**')
			if 'h' in time_remaining:
				hrs, min_ = time_remaining.split('h ')
			else:
				hrs = 0
				min_ = time_remaining
			daily_reset = (dt.now() + td(seconds=int(hrs)*3600 + int(min_)*60)).replace(second=0, microsecond=0)
		if 'can react' in react_sent:
			react_reset = dt.now().replace(second=0, microsecond=0)
		else:
			_, time_remaining, _ = react_sent.split('**')
			if 'h' in time_remaining:
				hrs, min_ = time_remaining.split('h ')
			else:
				hrs = 0
				min_ = time_remaining
			react_reset = (dt.now() + td(seconds=int(hrs)*3600 + int(min_)*60)).replace(second=0, microsecond=0)
		if 'ready' in kakera_sent:
			kakera_reset = dt.now().replace(second=0, microsecond=0)
		else:
			_, time_remaining, _ = kakera_sent.split('**')
			if 'h' in time_remaining:
				hrs, min_ = time_remaining.split('h ')
			else:
				hrs = 0
				min_ = time_remaining
			kakera_reset = (dt.now() + td(seconds=int(hrs)*3600 + int(min_)*60)).replace(second=0, microsecond=0)
		return (claim_reset, roll_reset, daily_reset, react_reset, kakera_reset)

	def parse_mu(self, mu):
		if 'can claim' in mu:
			_, claim_sent = mu.split('\n')
			_, time_remaining, _ = claim_sent.split('**')
		else:
			*_, time_remaining, _ = mu.split('**')
		if 'h' in time_remaining:
			hrs, min_ = time_remaining.split('h ')
		else:
			hrs = 0
			min_ = time_remaining
		return (dt.now() + td(seconds=int(hrs)*3600 + int(min_)*60)).replace(second=0, microsecond=0)	

	# Listeners
	@commands.Cog.listener()
	async def on_message(self, m):
		if m.channel.id != waifu_channel and m.author == self.bot.user:
			return

		def is_mudae_reply(msg):
			return m.channel.id == msg.channel.id and msg.author.id == mudae_id

		if not get_user_id(m.author.id) and m.author.id != mudae_id and m.author != self.bot.user:
			add_user(m.author.id, m.author.name)

		log.debug(f'{m.author.name} <{m.author.id}>: {m.content}')

		# User claimed a waifu/husbando
		if re.match('.* and .* are now married!.*', m.content):
			user_name = m.content.split(' ')[1]
			if dt.now() > self.claim_reset:
				self.claims_reset = self.get_claim_reset()
			if get_timer(user_name, 'claim_reset', 'waifu_info') != self.claim_reset:
				update_user_timer(user_name, 'claim_reset', 'waifu_info', self.claim_reset)
			return

		# For when user is out of rolls


		# User used the $tu command
		if m.content == '$tu':
			try:
				tu_reply = await self.bot.wait_for('message', check=is_mudae_reply, timeout=300)
			except asyncio.TimeoutError:
				tu_reply = None
			if tu_reply:
				claim_reset, roll_reset, daily_reset, react_reset, kakera_reset = self.parse_tu(tu_reply.content)
				update_waifu_timers(m.author.id, claim_reset, roll_reset, daily_reset, react_reset, kakera_reset)
				return

		# User used the $mu command
		if m.content in ('$mu', '$marryup'):
			try:
				tu_reply = await self.bot.wait_for('message', check=is_mudae_reply, timeout=300)
			except asyncio.TimeoutError:
				tu_reply = None
			if tu_reply:
				claim_reset = self.parse_mu(tu_reply.content)
				if self.claim_reset < claim_reset:
					self.claim_reset = claim_reset
				update_user_timer(m.author.id, 'claim_reset', 'waifu_info', self.claim_reset)

	# Tasks
	async def reminders(self):
		# TODO: Improve the reminders
		'''
			The claims and pokeslots timers reset for every at the same time
			Once it generates the claims and poke_timers it only needs to @ people who can claim/roulette
		'''
		await self.bot.wait_until_ready()
		waifu = await self.bot.fetch_channel(waifu_channel)
		while not self.bot.is_closed():
			resets = get_user_resets()
			if resets.empty:
				continue
			reminder = ''
			if ((self.roll_reset - dt.now()).total_seconds() // 60) < 0:
				self.roll_reset = self.get_roll_reset()
			if le_minutes(self.roll_reset) and ((self.roll_reset - dt.now()).total_seconds() // 60) % 5 == 0:
				for user, claim_reset, _, daily_reset, react_reset, kakera_reset, poke_reset in resets.values.tolist():
					sub_str = ''
					adding = any([
						not pd.isnull(claim_reset), 
						not pd.isnull(daily_reset), 
						not pd.isnull(react_reset), 
						not pd.isnull(kakera_reset), 
						not pd.isnull(poke_reset)
					])
					if not pd.isnull(claim_reset):
						if claim_reset < dt.now():
							sub_str += ' You can claim now!'
						elif le_minutes(claim_reset):
							time_remaining = self.format_remaining_time(claim_reset - dt.now())
							sub_str += f' You can claim in **{time_remaining}**.'
					if not pd.isnull(daily_reset):
						if daily_reset < dt.now():
							sub_str += ' You can use your daily now!'
						elif le_minutes(daily_reset):
							time_remaining = self.format_remaining_time(daily_reset - dt.now())
							sub_str += f' Your daily is up in **{time_remaining}**.'
					if not pd.isnull(react_reset):
						if react_reset < dt.now():
							sub_str += ' You can react now!'
						elif le_minutes(react_reset):
							time_remaining = self.format_remaining_time(react_reset - dt.now())
							sub_str += f' You can react in **{time_remaining}**.'
					if not pd.isnull(kakera_reset):
						if kakera_reset < dt.now():
							sub_str += ' You can use your daily kakera now!'
						elif le_minutes(kakera_reset):
							time_remaining = self.format_remaining_time(kakera_reset - dt.now())
							sub_str += f' Your daily kakera is up in **{time_remaining}**.'
					if not pd.isnull(poke_reset):
						if poke_reset < dt.now():
							sub_str += ' You can play the pokeslots now!'
						elif le_minutes(poke_reset):
							time_remaining = self.format_remaining_time(poke_reset - dt.now())
							sub_str += f' Your pokeslot is ready in **{time_remaining}**.'
					if adding and sub_str:
						reminder += f'<@{user}>:'
						reminder += sub_str
						reminder += '\n'
				reminder += f'Rolls reset in **{self.format_remaining_time(self.roll_reset - dt.now())}**'
				if reminder:
					await waifu.send(reminder)
			await asyncio.sleep(60)