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

	