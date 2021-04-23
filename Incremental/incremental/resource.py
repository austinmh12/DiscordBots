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

class Resource(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Utilities
	def get_resource(self, user, resource):
		user_id = get_user_id(user)
		resource_id = get_resource_id(resource)
		df = sql('SELECT r.id, ur.amount, ur.cost, r.unlock_name FROM resources r INNER JOIN user_resources ur ON r.id = ur.resource_id WHERE ur.user_id = %s AND r.id = %s', (user_id, resource_id))
		return df

	def get_resource_amount(self, user, resource):
		user_id = get_user_id(user)
		resource_id = get_resource_id(resource)
		df = sql('SELECT amount, cost FROM user_resources WHERE user_id = %s AND resource_id = %s', (user_id, resource_id))
		if df.empty:
			return 0
		return df.amount[0]

	def get_unlocked_resources(self, user):
		user_id = get_user_id(user)
		df = sql('SELECT r.name, r.unlock_amount, r.unlock_name, ur.cost, ur.amount FROM resources r LEFT JOIN user_resources ur ON r.id=ur.resource_id WHERE ur.user_id = %s', (user_id,))
		df['unlocked'] = df.apply(lambda x: x[1] <= self.get_resource_amount(user, x[2]), axis=1)
		return df

	def add_update_resource(self, user, resource, amount):
		user_id = get_user_id(user)
		resource_id = get_resource_id(resource)
		resources = self.get_resource(user, resource)
		log.info(f'\n{resources.head()}')
		if resources.empty:
			return self.add_resource(user_id, resource_id, amount)
		if resource_id == resources.id[0]:
			amount += resources.amount[0]
			log.info(amount)
			return self.update_resource(user_id, resource_id, int(amount), resources.cost[0], resources.unlock_name[0])

	def add_resource(self, user_id, resource_id, amount):
		sql('INSERT INTO user_resources (user_id, resource_id, amount) VALUES (%s, %s, %s)', (user_id, resource_id, amount))

	def update_resource(self, user_id, resource_id, amount, cost, resource_spent):
		resource_spent_id = get_resource_id(resource_spent)
		sql('UPDATE user_resources SET amount = %s WHERE user_id = %s AND resource_id = %s', (amount, user_id, resource_id))
		sql('UPDATE user_resources SET amount = %s WHERE user_id = %s AND resource_id = %s', (self.get_resource_amount))

	def gen_buy_embed(self, user):
		ret = Embed(
			title='Shop',
			description='Browse the wares. Reply with one of the numbers or "None" to make a selection.',
			colour=Colour.from_rgb(50, 255, 0)
		)
		for i, (name, unlock_amount, unlock_name, cost, amt, unlocked) in enumerate(self.get_unlocked_resources(user).values.tolist()):
			if i == 0:
				ret.add_field(name=f'{name}', value=f'You have {amt} money', inline=False)
				continue
			if unlocked:
				ret.add_field(name=f'{i}. {name} - {amt}', value=f'Costs: {cost if cost else unlock_amount} {unlock_name}', inline=False)
		return ret


	# Commands
	@commands.command(name='buy',
					pass_context=True,
					description='Buys a resource of the requested type',
					brief='Buys a resource',
					aliases=['b'])
	async def buy(self, ctx):
		unlocked = self.get_unlocked_resources(ctx.author.id)
		choices = [i for i in range(len(unlocked.values.tolist()))]
		await ctx.send(embed=self.gen_buy_embed(ctx.author.id))

		def same_user_and_channel(msg):
			return ctx.author == msg.author and ctx.channel == msg.channel

		try:
			choice_reply = await self.bot.wait_for('message', check=same_user_and_channel, timeout=60)
			choice = reply_to_choice(choice_reply.content)
		except asyncio.TimeoutError:
			choice = None
		if choice in choices:
			self.add_update_resource(ctx.author.id, unlocked.name[choice], 1)
			await ctx.send(f'You bought 1 {unlocked.name[choice]}, you now have {self.get_resource_amount(ctx.author.id, unlocked.name[choice])}.')
		elif not choice:
			await ctx.send('You did not make a selection.')
		else:
			await ctx.send(f'{choice} was an invalid selection.')



