from discord.ext import commands
import asyncio
from . import sql
import logging
from discord import Member

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

class GMCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	#### CHANNELS ####

	def get_user_channel(self, user_id):
		df = sql('SELECT * FROM channel_mapping WHERE user_id = ?', (user_id,))
		if df.empty:
			return None
		return df['channel_id'][0]

	def register(self, user_id, channel_id):
		sql('INSERT INTO channel_mapping VALUES (?,?)', (user_id, channel_id))

	def unregister(self, user_id):
		sql('DELETE FROM channel_mapping WHERE user_id = ?', (user_id,))

	@commands.command(name='registerchannel',
					pass_context=True,
					description='Registers a user to the current channel',
					brief='Register user to this channel',
					aliases=['rc'])
	async def register_channel(self, ctx, user: Member):
		if 'GM' not in [r.name for r in ctx.author.roles]:
			return
		channel_id = ctx.channel.id
		cur_channel = self.get_user_channel(user.id)
		if cur_channel:
			ch = self.bot.get_channel(int(cur_channel))
			self.unregister(user.id)
			self.register(user.id, ctx.channel.id)
			return await ctx.send(f'{user.name} has been unregistered from {ch.name} and registered to {ctx.channel.name}')
		else:
			self.register(user.id, ctx.channel.id)
			return await ctx.send(f'{user.name} has been registered to {ctx.channel.name}')

	#### DECKS ####

	def get_deck(self, discord_id, name):
		df = sql('SELECT * FROM decks WHERE discord_id = ? AND name = ?', (discord_id, name))
		if df.empty:
			return None
		return df

	@commands.command(name='delete_deck',
					pass_context=True,
					description='Deletes a user\'s deck',
					brief='Delete a deck',
					aliases=['dd'])
	async def delete_deck(self, ctx, user: Member, name):
		if 'GM' not in [r.name for r in ctx.author.roles]:
			return
		if not self.get_deck(user.id, name).empty:

			def _is_same_gm(m):
				return m.author == ctx.author and m.channel == ctx.channel
			
			await ctx.send(f'Do you want to delete <@{user.id}>\'s deck **{name}**? (Y/n)')
			try:
				reply = await self.bot.wait_for('message', check=_is_same_gm, timeout=30)
			except asyncio.TimeoutError:
				return
			if reply.content.lower() == 'y':
				sql('DELETE FROM decks WHERE discord_id = ? AND name = ?', (user.id, name))
				return await ctx.send(f'Deleted **{user.name}**\'s deck **{name}**')


