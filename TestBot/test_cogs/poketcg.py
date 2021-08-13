from datetime import datetime as dt, timedelta as td
from discord.ext import commands
import asyncio
import logging
import re
import typing
from discord import Member, Embed, Colour, File
from random import random, choices, choice
from .poketcgFunctions import api_call

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

version = '0.0.0'


class PokeTCG(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.store = None

	@commands.command(name='cards',
					pass_context=True,
					description='',
					brief='')
	async def get_cards(self, ctx, *name):
		name = ' '.join(name) if isinstance(name, tuple) else name
		params = {'q': f'name:{name}'}
		data = api_call('cards', params)
		cards = data['data']
		await ctx.send(cards[0].get('images').get('large'))