from . import log, BASE_PATH, sql, Page, MyCog, chunk
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
version = '0.4.1'

# Constants
with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

def yt_check(ctx):
	return ctx.channel.id == 623291442726436884

# Utility Functions
def initialise_db():
	sql('youtube', 'create table channels (id text, name text, thumbnail text, video_count integer)')
	sql('youtube', 'create table subscriptions (discord_id integer, channel_id text)')

def generate_subscribe_embed(channels):
	desc = 'Here are the results of your search, reply with a number to make a selection.\n'
	for idx, channel in channels.items():
		log.debug(f'{idx}: {channel.name}')
		if idx > 5:
			break
		desc += f'**{idx}:** [{channel.name}]({channel.url})\n'
	page = Page('Search Results', desc, colour=channels[1].colour, thumbnail=channels[1].thumbnail)
	return page.embed

def get_channels():
	df = sql('youtube', 'select * from channels')
	if df.empty:
		return []
	return [Channel(**d) for d in df.to_dict('records')]

def get_channel(id):
	df = sql('youtube', 'select * from channels where id = ?', (id,))
	if df.empty:
		return None
	return Channel(**df.to_dict('records')[0])

def add_channel(channel):
	return sql('youtube', 'insert into channels values (?,?,?,?)', channel.to_row)

def delete_channel(channel):
	return sql('youtube', 'delete from channels where id = ?', (channel.id,))

def update_channel(channel):
	return sql('youtube', 'update channels set video_count = ? where id = ?', (channel.video_count, channel.id))

def get_subscriptions_for_channel(channel):
	df = sql('youtube', 'select * from subscriptions where channel_id = ?', (channel.id,))
	if df.empty:
		return []
	return list(df.discord_id)

def get_subscriptions_for_user(discord_id):
	df = sql('youtube', 'select * from subscriptions where discord_id = ?', (discord_id, ))
	if df.empty:
		return []
	return [get_channel(c) for c in df.channel_id]

def add_subscription(discord_id, channel):
	return sql('youtube', 'insert into subscriptions values (?,?)', (discord_id, channel.id))

def delete_subscription(discord_id, channel):
	return sql('youtube', 'delete from subscriptions where discord_id = ? and channel_id = ?', (discord_id, channel.id))

def check_for_existing_subscription(discord_id, channel):
	subs = get_subscriptions_for_user(discord_id)
	try:
		return channel in subs
	except AttributeError:
		return False

class YoutubeCog(MyCog):
	def __init__(self, bot):
		super().__init__(bot)
		if not os.path.exists(f'{BASE_PATH}/youtube.db'):
			log.info('Initialising database.')
			initialise_db()
		self.channels = self.initialise_channels()
		self.check_for_videos.start()

	def initialise_channels(self):
		return get_channels()

	# Commands #
	@commands.command(name='subscribe',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['sub'],
					usage='<channel>')
	@commands.check(yt_check)
	async def subscribe(self, ctx, *channel):
		"""Searches YouTube for the channel and then returns a list of the top 5 results
		Lets the user then select a channel from the list. If a channel is selected, add
		that to the subscription table and then add the channel to the channels list
		"""
		search_channel = '%20'.join(channel)
		resp = r.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={search_channel}&type=channel&key={ENV["YTAPIKEY"]}')
		channels = {i: Channel.from_item(item) for i, item in enumerate(resp.json().get('items', []), start=1)}
		log.debug(channels)
		await ctx.send(embed=generate_subscribe_embed(channels))

		def same_user_and_channel(msg):
			return ctx.author == msg.author and ctx.channel == msg.channel

		try:
			reply = await self.bot.wait_for('message', check=same_user_and_channel, timeout=60)
		except asyncio.TimeoutError:
			return await ctx.send('You didn\'t make a selection.')
		try:
			choice = int(reply.content)
		except ValueError:
			choice = 0
		choice = choice if 1 <= choice <= min(5, len(channels)) else 0
		channel = channels.get(choice, None)
		if not channel:
			return await ctx.send('No channel selected.')
		if check_for_existing_subscription(ctx.author.id, channel):
			return await ctx.send(f'You are already subscribed to **{channel.name}**')
		await ctx.send(f'You are now subscribed to **{channel.name}**!')
		add_subscription(ctx.author.id, channel)
		channel.video_count = channel.get_video_count()
		add_channel(channel)
		if channel not in self.channels:
			self.channels.append(channel)

	@commands.command(name='unsubscribe',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['unsub'],
					usage='<channel>')
	@commands.check(yt_check)
	async def unsubscribe(self, ctx):
		"""Provides a list of the user's subscriptions and allows them to select channels
		to unsubscribe from using the number next to the name.
		"""
		subs = get_subscriptions_for_user(ctx.author.id)
		if not subs:
			return await ctx.send('You have no subscriptions.')
		subs.sort()
		channels = {i: channel for i, channel in enumerate(subs, start=1)}
		pages = []
		idx = 1
		for ch in chunk(subs, 15):
			desc = ''
			for channel in ch:
				desc += f'**{idx}:** [{channel.name}]({channel.url})\n'
				idx += 1
			pages.append(Page(f'{ctx.author.display_name}\'s Subscriptions', desc, colour=(232, 49, 39), icon=ctx.author.avatar_url))
		await self.paginated_embeds(ctx, pages, content='Which channel would you like to unsubscribe from? (type the number)')

		def same_user_and_channel(msg):
			return ctx.author == msg.author and ctx.channel == msg.channel

		try:
			reply = await self.bot.wait_for('message', check=same_user_and_channel, timeout=60)
		except asyncio.TimeoutError:
			return await ctx.send('You didn\'t make a selection.')
		try:
			choice = int(reply.content)
		except ValueError:
			choice = 0
		choice = choice if 1 <= choice <= len(channels) else 0
		channel = channels.get(choice, None)
		if not channel:
			return await ctx.send('No channel selected.')
		await ctx.send(f'You are no longer subscribed to **{channel.name}**')
		delete_subscription(ctx.author.id, channel)
		return await self.subscriptions(ctx)


	@commands.command(name='subscriptions',
					pass_context=True,
					description='Subscribe to a youtube channel',
					brief='Subscribe to a youtube channel',
					aliases=['subs'])
	@commands.check(yt_check)
	async def subscriptions(self, ctx):
		"""Lists the user's subscriptions.
		"""
		subs = get_subscriptions_for_user(ctx.author.id)
		subs.sort()
		pages = []
		for ch in chunk(subs, 15):
			desc = ''
			for channel in ch:
				desc += f'[{channel.name}]({channel.url})\n'
			pages.append(Page(f'{ctx.author.display_name}\'s Subscriptions', desc, colour=(232, 49, 39), icon=ctx.author.avatar_url))
		pages.extend([s.info_embed for s in subs])
		return await self.paginated_embeds(ctx, pages)

	# Tasks #
	@tasks.loop(seconds=3600)
	async def check_for_videos(self):
		"""Loops through the channels, calls the channel.get_video_count(). If the returned 
		value is higher than channel.video_count, set the channel.video_count to that and
		then send the channel embed to the channel.
		"""
		log.info('Checking for new videos.')
		yt_channel = await self.bot.fetch_channel(623291442726436884)
		deleted_channels = []
		for channel in self.channels:
			subscribers = get_subscriptions_for_channel(channel)
			if not subscribers:
				delete_channel(channel)
				deleted_channels.append(channel)
				continue
			video_count = channel.get_video_count()
			if video_count > channel.video_count:
				msg = ', '.join([f'<@{discord_id}>' for discord_id in subscribers])
				await yt_channel.send(msg, embed=channel.new_video_embed.embed)
				channel.video_count = video_count
				update_channel(channel)
		for channel in deleted_channels:
			self.channels.pop(self.channels.index(channel))

	@check_for_videos.before_loop
	async def before_check_for_videos(self):
		await self.bot.wait_until_ready()

class Channel:
	def __init__(self, id, name, thumbnail, video_count=0):
		self.id = id
		self.name = name
		self.thumbnail = thumbnail
		self.url = f'https://www.youtube.com/channel/{self.id}/videos'
		self.colour = self.gen_channel_colour()
		self.video_count = video_count

	def gen_channel_colour(self):
		resp = r.get(self.thumbnail)
		im = Image.open(BytesIO(resp.content))
		im.thumbnail((1, 1))
		return im.getpixel((0, 0))

	def get_video_count(self):
		"""Calls the YouTube API to get the videoCount statistic for the channel.
		"""
		resp = r.get(f'https://www.googleapis.com/youtube/v3/channels?key={ENV["YTAPIKEY"]}&id={self.id}&part=statistics').json()
		video_count = resp.get('items', [{}])[0].get('statistics', {}).get('videoCount', 0)
		return int(video_count)

	@property
	def new_video_embed(self):
		"""Returns an embed used for the 
		"""
		return Page(
			f'New {self.name} Video!', 
			self.url, 
			colour=self.colour, 
			thumbnail=self.thumbnail,
			footer='This is an automated message based on video count.'
		)
	
	@property
	def info_embed(self):
		return Page(
			self.name, 
			f'[Video list]({self.url})', 
			colour=self.colour, 
			image=self.thumbnail
		)

	@property
	def to_row(self):
		return (self.id, self.name, self.thumbnail, self.video_count)

	@classmethod
	def from_item(cls, item):
		snippet = item['snippet']
		return cls(snippet['channelId'], snippet['title'], snippet['thumbnails']['default']['url'])

	def __gt__(self, c):
		return self.name > c.name

	def __eq__(self, c):
		return self.id == c.id

	def __hash__(self):
		return hash(self.id)