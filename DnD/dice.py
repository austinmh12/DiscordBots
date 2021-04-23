from discord.ext import commands
import discord
import logging
from random import randint

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

class DiceCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.value = 3

	@commands.command()
	async def roll(self, ctx):
		await ctx.channel.send(f'You rolled {randint(1, self.value)}')