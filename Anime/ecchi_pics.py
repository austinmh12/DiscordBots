import discord, logging, json
from datetime import datetime as dt, timedelta as td
from discord.ext.commands import Bot
from discord.ext import commands
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

SCRIPT_PATH = '/home/austinmh12/Documents/Code/Python/discord_bots/Anime/ecchi_pics.py'
SCRIPT_MTIME = getmtime(SCRIPT_PATH)

log = get_logger()
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)



ECCHI_ID = 656320518458441728
Austin_weeb_id = 686702534290964483
Austin_weeb_nsfw_id = 700559731000868904
test_general = 655509540548116480
ANIME_PATH = 'S:/OldPC/Pictures/Anime'
ECCHI_PATH = 'S:/OldPC/Pictures/Ecchi'
ANIME_COUNT = 0
ECCHI_COUNT = 0
sfw_uploaded = 0
nsfw_uploaded = 0

last_pic = ''
too_big = []
posts = []

client = Bot(command_prefix=commands.when_mentioned_or('!', 'A.', 'a.', 'ap'))

@client.event
async def on_ready():
	log.info('Client is ready.') 
	for ch in client.get_all_channels():
		log.debug(f'{ch.name} - {ch.id}')


async def get_anime_pics():
	global ANIME_COUNT
	global ECCHI_COUNT
	global posts
	log.info('Preparing to download...')
	await client.wait_until_ready()
	while not client.is_closed():
		last_upload = get_last_upload('uploads.txt')
		if dt.now().hour < 20 or last_upload:
			log.debug(f'Hour: {dt.now().hour}  Last Upload: {last_upload}  Then: {dt.now().hour >= 20 and not last_upload}')
			log.info('Not downloading.')
			await asyncio.sleep(3600)
			continue
		ANIME_COUNT = 0
		ECCHI_COUNT = 0
		ANIME = [f for f in os.listdir(ANIME_PATH) if isfile(pjoin(ANIME_PATH, f))]
		ECCHI = [f for f in os.listdir(ECCHI_PATH) if isfile(pjoin(ECCHI_PATH, f))]
		reddit = Reddit('bot1')

		def _cb(result):
			global ANIME_COUNT
			global ECCHI_COUNT
			if result == 'A':
				ANIME_COUNT += 1
			if result == 'E':
				ECCHI_COUNT += 1

		def __cb(ret):
			global posts
			if ret:
				posts.extend(ret)

		p1 = ThreadPool(10)
		for sub in get_subs():
			p1.apply_async(get_posts, args=(reddit, sub), callback=__cb)
		p1.close()
		p1.join()
		log.info(len(posts))
		p2 = ThreadPool(10)
		for i, s in enumerate(posts, start=1):
			p2.apply_async(downloader, args=(ANIME, ECCHI, s, i), callback=_cb)
		p2.close()
		p2.join()

		posts = []
		log.info(f'Anime pics downloaded: {ANIME_COUNT}\tEcchi pics downloaded: {ECCHI_COUNT}')
		# await upload_ecchi()
		await asyncio.sleep(3600)

def downloader(a, ec, s, i):
	try:
		resp = r.get(s.url)
	except r.exceptions.MissingSchema:
		log.error(f'{i}: {s.subreddit}')
		return
	except r.exceptions.ConnectionError:
		log.error(f"{i}: Couldn't connect to {s.url}")
		return
	except TimeoutError:
		log.error(f"{i}: Couldn't connect to {s.url}")
		return
	try:
		im = Image.open(BytesIO(resp.content))
		im_name = s.url.split('/')[-1]
		nsfw = s.over_18
		if nsfw:
			if im_name in ec:
				log.debug(f'{i}: Already downloaded.')
				return
		else:
			if im_name in a:
				log.debug(f'{i}: Already downloaded.')
				return
		im.save(f'{ECCHI_PATH if nsfw else ANIME_PATH}/{im_name}')
		log.info(f'{i}: Downloaded {"Ecchi" if nsfw else "Anime"}/{im_name}')
		return 'E' if nsfw else 'A'
	except OSError as e:
		log.error(f'{i}: Not an image. {e}')
		return
	except ValueError:
		log.error(f'{i}: {s.permalink}')
		return


async def upload_ecchi():
	channel = await client.fetch_channel(ECCHI_ID)
	today = dt.now().strftime('%d-%m-%Y')
	ecchi = [(pjoin(ECCHI_PATH, f), channel, True) for f in os.listdir(ECCHI_PATH) if isfile(pjoin(ECCHI_PATH, f)) and dt.fromtimestamp(getmtime(pjoin(ECCHI_PATH, f))).strftime('%d-%m-%Y') == today]
	ret = await asyncio.gather(*(upload_a_pic(*ecc) for ecc in ecchi))
	await channel.send(f"Enjoy today's daily dump! There were {ret.count('nsfw')} pics :)")
	log.info('Uploaded all the ecchi pics from today')
	with open('uploads.txt', 'w') as f:
		f.write(f'{dt.now().strftime("%Y-%m-%d")}')

@client.command(name='animepic',
				pass_context=True,
				description='Provides a (psuedo-)random anime pic.',
				brief='Anime pics bruh.',
				aliases=['ap', 'pic'])
async def anime_pic(ctx, amt: typing.Optional[int]=1):
	if ctx.channel.name not in ['anime-pics', 'austins-bot-channel-nsfw']:
		log.error('Not in the correct channel.')
		return
	pics = list_anime_pics(amt)
	for p in pics:
		file = discord.File(p)
		try:
			await ctx.channel.send(file=file)
			file.close()
		except discord.errors.HTTPException:
			log.debug(p)
			p = list_anime_pics(1)[0]
			while p in pics:
				p = list_anime_pics(1)[0]
			f = discord.File(p)
			await ctx.channel.send(file=f)
			file.close()

@client.command(name='ecchipic',
				pass_context=True,
				description='Provides a (psuedo-)random anime pic.',
				brief='Anime pics bruh.',
				aliases=['ep', 'echpic'])
async def ecchi_pic(ctx, amt: typing.Optional[int]=1):
	if ctx.channel.name not in ['anime-pics', 'austins-bot-channel-nsfw']:
		log.error('Not in the correct channel.')
		return
	pics = list_anime_pics(amt, True)
	for p in pics:
		file = discord.File(p)
		try:
			await ctx.channel.send(file=file)
			file.close()
		except discord.errors.HTTPException:
			log.debug(p)
			p = list_anime_pics(1, True)[0]
			while p in pics:
				p = list_anime_pics(1, True)[0]
			f = discord.File(p)
			await ctx.channel.send(file=f)

@client.command(name='subreddit',
				pass_context=True,
				description='Allows a user to add a subreddit to the list of subs that the bot gets pics from',
				brief='Adds subs',
				aliases=['sub', 'sr', 'subs'])
async def add_subreddit(ctx, sub=None):
	subs = get_subs()
	subs.sort(key=lambda x: x.upper())
	if not sub:
		await ctx.channel.send(embed=gen_sub_embed(subs))
		return
	if sub in subs:
		await ctx.channel.send(f'{sub} is already in the list of subreddits.')
		return
	subs.append(sub)
	write_subs(subs)
	await ctx.channel.send(f'Added {sub} to the list of subreddits!')

def get_subs():
	with open('subreddits.txt') as f:
		return [l.strip() for l in f.readlines()]

def write_subs(subs):
	with open('subreddits.txt', 'w') as f:
		for sub in subs:
			f.write(sub+'\n')

def gen_sub_embed(subs):
	embed = discord.Embed(
		title='Subreddits',
		description='The list of subreddits the bot downloads from.',
		colour=discord.Colour.from_rgb(100, 20, 40)
	)
	embed.set_thumbnail(url="https://discordemoji.com/assets/emoji/002_happyjumping.gif")
	for sub in subs:
		embed.add_field(name=sub, value=f'https://www.reddit.com/r/{sub}', inline=False)
	return embed

def list_anime_pics(n, nsfw=False):
	path = ECCHI_PATH if nsfw else ANIME_PATH
	anime = [pjoin(path, f) for f in os.listdir(path) if isfile(pjoin(path, f))]
	pics = []
	while len(pics) < n:
		pic = choice(anime)
		while pic == last_pic or pic in too_big or pic in pics:
			pic = choice(anime)
		pics.append(pic)
	return pics

async def check_for_changes():
	await client.wait_until_ready()
	while not client.is_closed():
		if getmtime(SCRIPT_PATH) != SCRIPT_MTIME:
			log.debug('File has changed, Re-running.')
			os.execv(sys.executable, ['python'] + sys.argv)
		await asyncio.sleep(1)

def get_last_upload(file):
	n = dt.now().strftime('%Y-%m-%d')
	with open(file) as f:
		last = f.read()
	log.debug(last)
	if last == n:
		return True
	return False

async def change_pfp():
	await client.wait_until_ready()
	while not client.is_closed():
		random_pfp = choice([pjoin(ANIME_PATH, f) for f in os.listdir(ANIME_PATH) if isfile(pjoin(ANIME_PATH, f))])
		log.info(f'Changing pfp to {random_pfp}')
		with open(random_pfp, 'rb') as f:
			b = f.read()
		try:
			await client.user.edit(avatar=b)
		except discord.errors.HTTPException:
			log.error('Can\'t change the pfp right now. Did it too much.')
		await asyncio.sleep(43200)

async def weebstuff():
	await client.wait_until_ready()
	# sfw = await client.fetch_channel(Austin_weeb_id) 
	nsfw = client.get_channel(Austin_weeb_nsfw_id)
	while not client.is_closed():
		last_upload = get_last_upload('weebsUpload.txt')
		if dt.now().hour < 21 or last_upload:
			log.debug(f'Hour: {dt.now().hour}  Last Upload: {last_upload}  Then: {dt.now().hour >= 21 and not last_upload}')
			log.debug('Not uploading to Weeb Stuff.')
			await asyncio.sleep(3600)
			continue
		log.debug('Attempting to upload anime pics to Weeb Stuff.')
		today = dt.now().strftime('%d-%m-%Y')
		pics = [(pjoin(ECCHI_PATH, f), nsfw, True) for f in os.listdir(ECCHI_PATH) if isfile(pjoin(ECCHI_PATH, f)) and dt.fromtimestamp(getmtime(pjoin(ECCHI_PATH, f))).strftime('%d-%m-%Y') == today]
		# pics.extend([(pjoin(ANIME_PATH, f), sfw) for f in os.listdir(ANIME_PATH) if isfile(pjoin(ANIME_PATH, f)) and dt.fromtimestamp(getmtime(pjoin(ANIME_PATH, f))).strftime('%d-%m-%Y') == today])
		pics.sort(key=lambda x: x[0].split('\\')[-1])
		ret = await asyncio.gather(*(upload_a_pic(*pic) for pic in pics))
		# await sfw.send(f"Enjoy today's daily dump! :) There were {ret.count('sfw')} pics total!")
		await nsfw.send(f"Enjoy today's daily dump! :) There were {ret.count('nsfw')} pics total!")
		log.info('Uploaded all the pics from today')
		with open('weebsUpload.txt', 'w') as f:
			f.write(f'{dt.now().strftime("%Y-%m-%d")}')
		await asyncio.sleep(3600)

async def upload_a_pic(pic, channel, nsfw=False):
	file = discord.File(pic)
	log.info(pic)
	try:
		await channel.send(file=file)
		file.close()
		return 'nsfw' if nsfw else 'sfw'
	except discord.errors.HTTPException:
		log.error(f'{pic} is too large. Upload by hand.')


async def testing():
	global ANIME_COUNT
	global ECCHI_COUNT
	global posts
	log.info('Preparing to download...')
	await client.wait_until_ready()
	ch = await client.fetch_channel(test_general)
	while not client.is_closed():
		last_upload = get_last_upload('uploads.txt')
		# if dt.now().hour < 20 or last_upload:
		# 	log.debug(f'Hour: {dt.now().hour}  Last Upload: {last_upload}  Then: {dt.now().hour >= 20 and not last_upload}')
		# 	log.info('Not downloading.')
		# 	await asyncio.sleep(3600)
		# 	continue
		ANIME_COUNT = 0
		ECCHI_COUNT = 0
		ANIME = [f for f in os.listdir(ANIME_PATH) if isfile(pjoin(ANIME_PATH, f))]
		ECCHI = [f for f in os.listdir(ECCHI_PATH) if isfile(pjoin(ECCHI_PATH, f))]
		reddit = Reddit('bot1')

		def _cb(result):
			global ANIME_COUNT
			global ECCHI_COUNT
			if result == 'A':
				ANIME_COUNT += 1
			if result == 'E':
				ECCHI_COUNT += 1

		def __cb(ret):
			global posts
			if ret:
				posts.extend(ret)

		p1 = ThreadPool(10)
		for sub in get_subs():
			p1.apply_async(get_posts, args=(reddit, sub), callback=__cb)
		p1.close()
		p1.join()
		log.info(len(posts))
		p2 = ThreadPool(10)
		for i, s in enumerate(posts, start=1):
			p2.apply_async(downloader, args=(ANIME, ECCHI, s, i), callback=_cb)
		p2.close()
		p2.join()

		posts = []
		log.info(f'Anime pics downloaded: {ANIME_COUNT}\tEcchi pics downloaded: {ECCHI_COUNT}')
		# await upload_ecchi()
		today = dt.now().strftime('%d-%m-%Y')
		pics = [(pjoin(ECCHI_PATH, f), ch, True) for f in os.listdir(ECCHI_PATH) if isfile(pjoin(ECCHI_PATH, f)) and dt.fromtimestamp(getmtime(pjoin(ECCHI_PATH, f))).strftime('%d-%m-%Y') == today]
		pics.extend([(pjoin(ANIME_PATH, f), ch) for f in os.listdir(ANIME_PATH) if isfile(pjoin(ANIME_PATH, f)) and dt.fromtimestamp(getmtime(pjoin(ANIME_PATH, f))).strftime('%d-%m-%Y') == today])
		pics.sort(key=lambda x: x[0].split('\\')[-1])
		ret = await asyncio.gather(*(upload_a_pic(*pic) for pic in pics))
		await ch.send(f"Enjoy today's daily dump! :) There were {ret.count('sfw')} pics total!")
		await ch.send(f"Enjoy today's daily dump! :) There were {ret.count('nsfw')} pics total!")
		await asyncio.sleep(3600)

def get_posts(reddit, sub):
	log.info(sub)
	return reddit.subreddit(sub).hot(limit=50)

client.loop.create_task(check_for_changes())
client.loop.create_task(get_anime_pics())
client.loop.create_task(change_pfp())
client.loop.create_task(weebstuff())
# client.loop.create_task(testing())
client.run(TOKEN, bot=True)