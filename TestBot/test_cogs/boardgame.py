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
	def __init__(self, bot):
		super().__init__(bot)
		self.game = None

	# Functions

	# Commands
	@commands.command(name='game',
					pass_context=True,
					description='Initiate a board game',
					brief='Initiate a board game')
	async def game_main(self, ctx, game_name):
		...