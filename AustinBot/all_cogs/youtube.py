from . import log, BASE_PATH, sql, Page, MyCog
import json
from datetime import datetime as dt, timedelta as td
from discord.ext import commands, tasks
from discord import Member, Embed, Colour, File
import asyncio
import requests as r
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

class YoutubeCog(MyCog):
	def __init__(self, bot):
		self.bot = bot
		if not os.path.exists(f'{BASE_PATH}/youtube.db'):
			initialise_db()
		self.channels = self.initialise_channels()

	def initialise_channels(self):
		...

	# Commands #
	@commands.command(name='subscribe',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['sub'],
					usage='<channel>')
	async def subscribe(self, ctx, *channel):
		"""Searches YouTube for the channel and then returns a list of the top 5 results
		Lets the user then select a channel from the list. If a channel is selected, add
		that to the subscription table and then add the channel to the channels list
		"""
		...

	@commands.command(name='unsubscribe',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['unsub'],
					usage='<channel>')
	async def unsubscribe(self, ctx):
		"""Provides a list of the user's subscriptions and allows them to select channels
		to unsubscribe from using the number next to the name.
		"""
		...

	@commands.command(name='subscriptions',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['subs'])
	async def subscriptions(self, ctx):
		"""Lists the user's subscriptions.
		"""
		...

	# Tasks #
	@tasks.loop(seconds=3600)
	async def check_for_videos(self):
		"""Loops through the channels, calls the channel.get_video_count(). If the returned 
		value is higher than channel.video_count, set the channel.video_count to that and
		then send the channel embed to the channel.
		"""
		...

class Channel:
	def __init__(self, id, name, thumbnail):
		self.id = id
		self.name = name
		self.thumbnail = thumbnail
		self.colour = self.gen_channel_colour()
		self.video_count = self.get_video_count()

	def gen_channel_colour(self):
		resp = r.get(url)
		im = Image.open(BytesIO(resp.content))
		im.thumbnail((1, 1))
		return im.getpixel((0, 0))

	def get_video_count(self):
		"""Calls the YouTube API to get the videoCount statistic for the channel.
		"""
		...

	@property
	def new_video_embed(self):
		"""Returns an embed used for the 
		"""
		return Page(
			f'New {self.name} Video!', 
			f'https://www.youtube.com/channel/{self.id}/videos', 
			colour=self.colour, 
			thumbnail=self.thumbnail,
			footer='This is an automated message based on video count.'
		)
	
	@property
	def info_embed(self):
		return Page(
			self.name, 
			f'https://www.youtube.com/channel/{self.id}/videos', 
			colour=self.colour, 
			image=self.thumbnail
		)
	