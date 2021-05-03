from . import log, BASE_PATH, Page, MyCog, chunk
from discord import File
from discord.ext import commands, tasks
import asyncio
from PIL import Image, ImageDraw, ImageFont
from random import randint
import typing

# Version
version = '0.0.0'

# Constants

# Functions

# Classes
class BoardGameCog(MyCog):
	available_games = ['Yahtzee']

	def __init__(self, bot):
		super().__init__(bot)
		self.game = None

	# Functions

	# Commands
	@commands.group(name='game',
					pass_context=True,
					invoke_without_command=True,
					description='Initiate a board game',
					brief='Initiate a board game')
	async def game_main(self, ctx):
		desc = 'Welcome to the Board Game Plaza! Here you can view all the available\n'
		desc += 'board games. To initiate, or join, a board game, use **.game <name>**\n'
		desc += 'Once all the players who want to play have joined, the **owner** of\n'
		desc += 'the game instance can start the game with **.game <name> start**\n\n'
		for game in __class__.available_games:
			desc += f'***{game}***\n'
		return await self.paginated_embeds(ctx, Page('Board Games Plaza', desc))