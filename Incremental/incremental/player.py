from datetime import datetime as dt, timedelta as td
from discord import Embed, Colour
from discord.ext import commands
import asyncio
import logging
import sys
from . import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

class Player(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Utilities
	def add_player(self, user):
		sql('INSERT INTO users (discord_id) VALUES (%s)', (user,))
		user_id = get_user_id(user)
		sql('INSERT INTO user_resources (user_id, resource_id, amount) VALUES (%s, %s, %s)', (user_id, get_resource_id('money'), 10))
		sql('INSERT INTO user_resources (user_id, resource_id, amount, cost) VALUES (%s, %s, %s)', (user_id, get_resource_id('jobs'), 10))

	def get_player_resources(self, user):
		return sql('SELECT r.name, ur.amount FROM resources r INNER JOIN user_resources ur ON r.id = ur.resource_id WHERE user_id = %s', (get_user_id(user),))

	def gen_resource_embed(self, user):
		ret = Embed(
			title='Resources',
			description='Here is everything in your storage',
			colour=Colour.from_rgb(128, 128, 128)
		)
		resources = self.get_player_resources(user)
		val = ''
		for name, amount in resources.values.tolist()[1:]:
			val += f'{name}: {amount}\n'
		ret.add_field(name=f'{resources.name[0]}: {resources.amount[0]}', value=val)
		return ret

	# Commands
	@commands.command(name='join',
					pass_context=True,
					description='Join the incremental game',
					brief='Join the game',
					aliases=['j'])
	async def join(self, ctx):
		if get_user_id(ctx.author.id):
			return await ctx.send('You are playing already.')
		self.add_player(ctx.author.id)
		return await ctx.send('You are now playing the game. You have 10 money. Buy a job with I.buy to get more.')

	@commands.command(name='myresources',
					pass_context=True,
					description='Displays your resources',
					brief='Your resources',
					aliases=['mr', 'resources'])
	async def player_resources(self, ctx):
		await ctx.send(embed=self.gen_resource_embed(ctx.author.id))


