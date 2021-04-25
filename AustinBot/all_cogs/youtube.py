from . import log, BASE_PATH, sql
import json
from datetime import datetime as dt, timedelta as td
from discord.ext import commands, tasks
from discord import Member, Embed, Colour, File
import asyncio
import requests as r
import os, sys
import os.path
from PIL import Image
from io import BytesIO

# Version
version = '0.0.0'

# Constants
with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

# Utility Functions
def initialise_db():
	sql('youtube', 'create table channels (channel_id text, name text, thumbnail text)')
	sql('youtube', 'create table subscriptions (discord_id integer, channel_id text)')

class YoutubeCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		if not os.path.exists(f'{BASE_PATH}/youtube.db'):
			initialise_db()

	@commands.command(name='subscribe',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['sub'],
					usage='<channel>')
	async def subscribe(self, ctx, *channel):
		...

	@commands.command(name='unsubscribe',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['sub'],
					usage='<channel>')
	async def unsubscribe(self, ctx, *channel):
		...

	@commands.command(name='subscriptions',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['subs'])
	async def subscriptions(self, ctx):
		...

class Channel:
	def __init__(self, id, name, thumbnail):
		self.id = id
		self.name = name
		self.thumbnail = thumbnail
		self.colour = self.gen_channel_colour()

	def gen_channel_colour(self):
		resp = r.get(url)
		im = Image.open(BytesIO(resp.content))
		im.thumbnail((1, 1))
		return im.getpixel((0, 0))

	@property
	def embed(self):
		ret = Embed(
			title=f'New {self.name} Video!',
			url=f'https://www.youtube.com/channel/{self.id}/videos',
			description='Go check it out!',
			color=discord.Colour.from_rgb(self.colour)
		)
		ret.set_thumbnail(url=self.thumbnail)
		ret.set_footer(text='This is an automated message based on video count.')
		return ret
	