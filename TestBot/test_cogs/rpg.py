from . import log, BASE_PATH, Page, MyCog, chunk
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint
import typing
import os.path

# Version
version = '0.0.0'

# Constants

# Functions
def initialise_db():
	...

# Classes
class RPGCog(MyCog):
	def __init__(self, bot):
		super().__init__(bot)
		if not os.path.exists(f'{BASE_PATH}/rpg.db'):
			log.info('Initialising database.')
			initialise_db()
