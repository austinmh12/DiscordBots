from . import sql, log, BASE_PATH, Page, MyCog, chunk
import json
from datetime import datetime as dt, timedelta as td
from discord import File
from discord.ext import commands, tasks
from discord.errors import HTTPException as ImageToLargeException
import asyncio
import requests as r
import os, sys
from os.path import getmtime, isfile, join as pjoin
from praw import Reddit
from PIL import Image
from io import BytesIO
from time import sleep, perf_counter as pc
from random import choice
import typing
from multiprocessing.pool import ThreadPool
from multiprocessing import get_logger

# Version
version = '1.0.5'

# Constants
with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

# Functions
def initialise_db():
	sql('anime', 'create table subreddits (name text)')
	sql('anime', 'create table posts (id text, img_data text, nsfw integer)')
	sql('anime', 'create table last_upload (date text)')
	sql('anime', 'create table channels (id integer, nsfw integer)')

def get_subreddits():
	df = sql('anime', 'select * from subreddits')
	if df.empty:
		return []
	return list(df.name)

def add_subreddit(name):
	return sql('anime', 'insert into subreddits values (?)', (name,))

def delete_subreddit(name):
	return sql('anime', 'delete from subreddits where name = ?', (name,))

def get_last_upload():
	df = sql('anime', 'select * from last_upload limit 1')
	if df.empty:
		return dt(1999, 1, 1)
	return dt.strptime(df.date[0], '%Y-%m-%d')

def update_last_upload():
	sql('anime', 'delete from last_upload')
	return sql('anime', 'insert into last_upload values (?)', (dt.now().strftime('%Y-%m-%d'),))

def get_posts_from_db():
	df = sql('anime', 'select * from posts')
	if df.empty:
		return []
	return [RedditPost(**d) for d in df.to_dict('records')]

def get_post_from_db(nsfw=0):
	df = sql('anime', 'select * from posts where nsfw = ?', (nsfw,))
	if df.empty:
		return None
	return choice([RedditPost(**d) for d in df.to_dict('records')])

def add_post_to_db(post):
	sql('anime', 'insert into posts values (?,?,?)', post.to_row)

def add_posts_to_db(posts):
	chunks = chunk(posts, 249)
	for ch in chunks:
		vals = []
		sql_str = 'insert into posts values '
		for rp in ch:
			if rp:
				sql_str += ' (?,?,?),'
				vals.extend(rp.to_row)
		sql('anime', sql_str[:-1], vals)

def get_channels():
	df = sql('anime', 'select * from channels')
	if df.empty:
		return []
	return [Channel(**d) for d in df.to_dict('records')]

def get_sfw_channels():
	return [c for c in get_channels() if not c.nsfw]

def get_nsfw_channels():
	return [c for c in get_channels() if c.nsfw]

def add_channel(channel):
	sql('anime', 'insert into channels values (?,?)', channel.to_row)

def delete_channel(channel):
	sql('anime', 'delete from channels where id = ?', (channel.id,))

def sfw_check(ctx):
	return ctx.channel.id in get_sfw_channels()

def nsfw_check(ctx):
	return ctx.channel.id in get_nsfw_channels()

# Classes
class AnimeCog(MyCog):
	def __init__(self, bot):
		super().__init__(bot)
		if not os.path.exists(f'{BASE_PATH}/anime.db'):
			log.info('Initialising database.')
			initialise_db()
		self.reddit = Reddit('bot1')
		self.get_anime_pics.start()

	# Utilities
	def need_to_download(self):
		if dt.now().hour < 12:
			return False
		if get_last_upload().date() < dt.now().date():
			return True
		return False

	def get_posts(self, sub):
		posts = self.reddit.subreddit(sub).hot(limit=50)
		existing_post_ids = [p.id for p in self.posts]
		return [p for p in posts if p.id not in existing_post_ids]

	def downloader(self, post):
		try:
			resp = r.get(post.url)
		except r.exceptions.MissingSchema:
			log.error(f'Missing Schema: {post.permalink}')
			return
		except r.exceptions.ConnectionError:
			log.error(f'Couldn\'t connect to {post.url}: {post.permalink}')
			return
		except TimeoutError:
			log.error(f'Couldn\'t connect to {post.url}: {post.permalink}')
			return
		try:
			Image.open(BytesIO(resp.content))
			nsfw = 1 if post.over_18 else 0
			return RedditPost(post.id, resp.content.hex(), nsfw)
		except OSError as e:
			log.error(f'Not an Image: {post.permalink}')
			return
		except ValueError:
			log.error(f'Not an Image: {post.permalink}')
			return

	async def upload_pic(self, pic):
		if not pic:
			return
		file = pic.to_file()
		channel = self.nsfw_channel if pic.nsfw else self.sfw_channel
		try:
			await channel.send(file=file)
		except ImageToLargeException:
			log.error(f'{pic.id} is too large. Upload by hand.')
		file.close()


	# Commands
	@commands.command(name='subreddits',
					pass_context=True,
					description='List the subreddits',
					breif='List the subreddits',
					aliases=[''])
	async def subreddits(self, ctx):
		...

	@commands.command(name='addsubreddits',
					pass_context=True,
					description='Add subreddits to the list of source materials',
					breif='Add subreddits to the list',
					aliases=['asub'])
	async def add_subreddits(self, ctx, *subs):
		...

	@commands.command(name='animepic',
					pass_context=True,
					description='Provides a SFW anime pic',
					breif='SFW anime pic',
					aliases=['sfw', 'ap'])
	# SFW Check
	async def anime_pic(self, ctx, amount: typing.Optional[int] = 1):
		...

	@commands.command(name='ecchipic',
					pass_context=True,
					description='Provides a NSFW anime pic',
					breif='NSFW anime pic',
					aliases=['nsfw', 'ep'])
	# NFSW check
	async def ecchi_pic(self, ctx, amount: typing.Optional[int] = 1):
		...

	# Tasks
	@tasks.loop(seconds=1800)
	async def get_anime_pics(self):
		if self.need_to_download():
			log.info('Starting the downloading process')
			reddit = Reddit('bot1')
			subs = get_subreddits()
			posts = get_posts_from_db()
			with ThreadPool(1) as p:
				log.info('Getting existing posts')
				self.posts = get_posts_from_db()
				posts = []
				log.info('Getting new posts')
				_posts = p.map_async(self.get_posts, subs).get()
				for post_list in _posts:
					posts.extend(post_list)
				log.info('Got posts, downloading...')
				img_posts = p.map_async(self.downloader, posts).get()
				log.info('Downloaded, uploading...')
			for img_post in img_posts:
				await self.upload_pic(img_post)
			log.info('Uploaded.')
			add_posts_to_db(img_posts)
			update_last_upload()

	@get_anime_pics.before_loop
	async def before_get_anime_pics(self):
		await self.bot.wait_until_ready()
		self.sfw_channel = await self.bot.fetch_channel(SFW_CHANNEL)
		self.nsfw_channel = await self.bot.fetch_channel(NSFW_CHANNEL)

class RedditPost:
	def __init__(self, id, img_data, nsfw):
		self.id = id
		self.img_data = img_data
		self.nsfw = nsfw

	@property
	def to_row(self):
		return (self.id, self.img_data, self.nsfw)

	def to_file(self):
		im = Image.open(BytesIO(bytes.fromhex(self.img_data)))
		ext = im.format
		im.close()
		return File(BytesIO(bytes.fromhex(self.img_data)), filename=f'{self.id}.{ext}')
	
	def __eq__(self, rp):
		return self.id == rp.id

class Channel:
	def __init__(self, id, nsfw):
		self.id = id
		self.nsfw = nsfw

	@property
	def to_row(self):
		return (self.id, self.nfsw)
	
	def __eq__(self, c):
		return self.id == c.id