import discord
import logging
import json
from datetime import datetime as dt, timedelta as td
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
import requests as r
import os
import sys
from collections import namedtuple
from PIL import Image
from io import BytesIO
from random import randint
from os.path import getmtime

SCRIPT_PATH = 'S:/OldPC/Python/Brendan/youtube.py'
SCRIPT_MTIME = getmtime(SCRIPT_PATH)

BWB_ID = 'UCJHA_jMfCvEnv-3kRjTCQXw'
BWB_CHANNEL_ID = 620440227114385409
YOUTUBE_CHANNEL_ID = 623291442726436884
BWB_VIDS = 0

Channel = namedtuple('Channel', 'name id url')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

client = Bot(command_prefix=commands.when_mentioned_or('!'))

@client.event
async def on_ready():
	act = discord.Activity(name='YouTube', type=discord.ActivityType.watching)
	await client.change_presence(activity=act)
	log.debug('Client is ready.')
	reload_subscriptions()

async def check_for_babish_video():
	await client.wait_until_ready()
	log.debug('Client is ready.')
	global BWB_VIDS
	if BWB_VIDS == 0:
		resp = r.get(f'https://www.googleapis.com/youtube/v3/channels?key={YOUTUBE_API_KEY}&id={BWB_ID}&part=statistics')
		BWB_VIDS = int(resp.json()['items'][0]['statistics']['videoCount'])
		log.info(f'Just Started up. Videos at startup: {BWB_VIDS}')
	while not client.is_closed():
		resp = r.get(f'https://www.googleapis.com/youtube/v3/channels?key={YOUTUBE_API_KEY}&id={BWB_ID}&part=statistics')
		vid_count = int(resp.json()['items'][0]['statistics']['videoCount'])
		if vid_count > BWB_VIDS:
			bwb_channel = await client.fetch_channel(BWB_CHANNEL_ID)
			emb = bwb_embed()
			await bwb_channel.send(embed=emb)
			BWB_VIDS = vid_count
			log.info(f'Sent the invitation to BWB\'s channel. New video count: {vid_count}')
		else:
			log.info('No new video.')
		await asyncio.sleep(3600)

def bwb_embed():
	embed = discord.Embed(
		title='New Binging With Babish Video!',
		url='https://www.youtube.com/user/bgfilms/videos',
		description='Go check it out!',
		colour=discord.Colour.dark_grey()
	)
	embed.set_image(url='https://cdn.discordapp.com/attachments/620440227114385409/620440437890482176/andrew.jpg')
	embed.set_thumbnail(url='https://i.imgur.com/zmua6tl.jpg')
	embed.set_footer(text='This is an automated message based on video count.')
	return embed

@client.command(name='subscribe',
				pass_context=True,
				description='Subscribes a user to the bot\'s video check.',
				brief='Subscribes you to a YouTuber.',
				aliases=['sub'])
async def subscribe_to_video_updates(ctx, *youtuber):
	user_id = ctx.message.author.id
	youtuber = '%20'.join(youtuber)
	log.debug(youtuber)
	resp = r.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={youtuber}&type=channel&key={YOUTUBE_API_KEY}')
	channels = [Channel(item['snippet']['title'], item['snippet']['channelId'], item['snippet']['thumbnails']['default']['url']) for item in resp.json()['items']]
	if len(channels) == 1:
		if not check_for_existing_subscription(user_id, channels[0]):
			client.loop.create_task(check_for_videos(user_id, channels[0]))
			add_subscription(user_id, channels[0])
			await ctx.channel.send(f'You\'ve successfully subscribed to {channels[0].name}')
		else:
			await ctx.channel.send(f'You\'re already subscribed to {channels[0].name}')
	else:
		choices = [i for i in range(len(channels))]
		await ctx.message.channel.send(embed=gen_choice_embed(channels))
		def same_user_and_channel(msg):
			return ctx.author == msg.author and ctx.channel == msg.channel
		try:
			choice_msg = await client.wait_for('message', check=same_user_and_channel, timeout=60)
			choice = reply_to_choice(choice_msg.content)
		except asyncio.TimeoutError:
			choice = None
		log.debug(choice)
		if choice in choices:
			if not check_for_existing_subscription(user_id, channels[choice]):
				client.loop.create_task(check_for_videos(user_id, channels[choice]))
				add_subscription(user_id, channels[choice])
				await ctx.channel.send(f'You\'ve successfully subscribed to {channels[choice].name}')
			else:
				await ctx.channel.send(f'You\'re already subscribed to {channels[choice].name}')
		elif not choice:
			await ctx.channel.send('You didn\'t make a choice.')
		else:
			await ctx.channel.send(f'{choice} is not a valid choice.')

def reply_to_choice(s):
	if s == 'None':
		return
	try:
		return int(s) - 1
	except ValueError:
		return s

async def check_for_videos(user_id, channel):
	await client.wait_until_ready()
	if not user_id:
		return
	vids = 0
	if vids == 0:
		resp = r.get(f'https://www.googleapis.com/youtube/v3/channels?key={YOUTUBE_API_KEY}&id={channel.id}&part=statistics')
		vids = int(resp.json()['items'][0]['statistics']['videoCount'])
		wait_amount = randint(1,3600)
		log.info(f'Just subscribed to {channel.name}. Videos at start: {vids}. Will check at {(dt.now()+td(seconds=wait_amount)).strftime("%H:%M:%S,%f")}')
		await asyncio.sleep(wait_amount)
	while not client.is_closed():
		if isinstance(user_id, list):
			user_id = [user for user in user_id if check_for_existing_subscription(user, channel)]
		else:
			user_id = user_id if check_for_existing_subscription(user_id, channel) else None
		if not user_id:
			log.warning(f'{user_id} is no longer subscribed to {channel.name}. Ending Task.')
			return
		resp = r.get(f'https://www.googleapis.com/youtube/v3/channels?key={YOUTUBE_API_KEY}&id={channel.id}&part=statistics')
		vid_count = int(resp.json()['items'][0]['statistics']['videoCount'])
		if vid_count > vids:
			yt_updates_channel = await client.fetch_channel(YOUTUBE_CHANNEL_ID)
			emb = gen_embed(channel)
			tag_message = ', '.join([f'<@{user}>' for user in user_id])
			tag_message += f'! A new {channel.name} video!'
			await yt_updates_channel.send(tag_message, embed=emb)
			vids = vid_count
			log.info(f'Sent the notification for {channel.name} to YouTuber Updates channel. New video count: {vid_count}')
		elif vid_count < vids:
			vids = vid_count
			log.warning(f'A {channel.name} video must\'ve been deleted. New video count: {vid_count}')
		else:
			log.info(f'No new {channel.name} video.')
		await asyncio.sleep(3600)

def gen_embed(channel):
	red, grn, blu = get_channel_colour(channel.url)
	ret = discord.Embed(
		title=f'New {channel.name} Video!',
		url=f'https://www.youtube.com/channel/{channel.id}/videos',
		description='Go check it out!',
		color=discord.Colour.from_rgb(red, grn, blu)
	)
	ret.set_thumbnail(url=channel.url)
	ret.set_footer(text='This is an automated message based on video count.')
	return ret

def gen_choice_embed(channels, choice=True):
	red, grn, blu = get_channel_colour(channels[0].url)
	if choice:
		desc = 'Here are the results of your search. Reply with one of the numbers or "None" to make a selection.'
	else:
		desc = 'Here are all your subscriptions'
	ret = discord.Embed(
			title='Search Results',
			description=desc,
			colour=discord.Colour.from_rgb(red, grn, blu)
	)
	for i, channel in enumerate(channels):
		if i == 0:
			log.debug(channel.url)
			ret.set_thumbnail(url=channel.url)
		ret.add_field(name=f'{i+1}.) {channel.name}', value=f'https://www.youtube.com/channel/{channel.id}')
	return ret

def check_for_existing_subscription(user, channel):
	subs = get_subscriptions(channel)
	if not subs:
		return False
	return str(user) in subs['subscribers']

def add_subscription(user, channel):
	subs = get_subscriptions()
	channel_info = subs.get(channel.name, None)
	if channel_info:
		channel_info['subscribers'].append(str(user))
	else:
		subs[channel.name] = {"id": channel.id, "url": channel.url, "subscribers": [str(user)]}
	with open('subscriptions.json', 'w') as sub_library:
		json.dump(subs, sub_library)

def reload_subscriptions():
	subs = get_subscriptions()
	for youtuber, info in subs.items():
		channel = Channel(youtuber, info['id'], info['url'])
		client.loop.create_task(check_for_videos(info['subscribers'], channel))

def delete_subscriptions(user, channel):
	subs = get_subscriptions()
	channel_info = subs.get(channel.name, None)
	if not channel_info:
		return
	else:
		channel_info['subscribers'].pop(channel_info['subscribers'].index(str(user)))
	with open('subscriptions.json', 'w') as sub_library:
		json.dump(subs, sub_library)

def get_subscriptions(channel=None):
	with open('subscriptions.json', encoding='utf-8') as sub_library:
		subs = json.load(sub_library)
	if channel:
		channel_info = subs.get(channel.name, None)
		if channel_info:
			return channel_info
		else:
			return None
	return subs

def get_user_subscriptions(user):
	subs = get_subscriptions()
	return [Channel(name, info['id'], info['url']) for name, info in subs.items() if str(user) in info['subscribers']]

def get_channel_colour(url):
	resp = r.get(url)
	im = Image.open(BytesIO(resp.content))
	im.thumbnail((1, 1))
	return im.getpixel((0, 0))

@client.command(name='unsubscribe',
				pass_context=True,
				description='Unubscribes a user from the bot\'s video check.',
				brief='Unsubscribes you from a YouTuber.',
				aliases=['unsub','negatesub','negsub','neg'])
async def unsubscribe_from_video_updates(ctx):
	user_id = ctx.author.id
	channels = get_user_subscriptions(user_id)
	choices = [i for i in range(len(channels))]
	await ctx.message.channel.send(embed=gen_choice_embed(channels))
	def same_user_and_channel(msg):
		return ctx.author == msg.author and ctx.channel == msg.channel
	try:
		choice_msg = await client.wait_for('message', check=same_user_and_channel, timeout=60)
		choice = reply_to_choice(choice_msg.content)
	except asyncio.TimeoutError:
		choice = None
	if choice in choices:
		delete_subscriptions(user_id, channels[choice])
		await ctx.channel.send(f'You\'ve successfully unsubscribed from {channels[choice].name}')
	elif not choice:
		await ctx.channel.send('You didn\'t make a choice.')
	else:
		await ctx.channel.send(f'{choice} is not a valid choice.')

@client.command(name='subs',
				pass_context=True,
				description='Shows you all your subscriptions.',
				brief='Your subs.',
				aliases=['subz','mysubs','mysubz'])
async def get_all_subscriptions(ctx):
	user_id = ctx.author.id
	channels = get_user_subscriptions(user_id)
	await ctx.message.channel.send(embed=gen_choice_embed(channels))

async def check_for_changes():
	await client.wait_until_ready()
	while not client.is_closed():
		if getmtime(SCRIPT_PATH) != SCRIPT_MTIME:
			log.debug('File has changed, Re-running.')
			os.execv(sys.executable, ['python'] + sys.argv)
		await asyncio.sleep(1)

@client.command(name='meme',
				pass_context=True,
				description='Makes the big blue letters',
				brief='Big blue letters',
				aliases=['memez','b','bigblue','blue', 'bbl'])
async def big_blue_letters(ctx):
	log.debug(ctx.message.content)
	def same_user_and_channel(msg):
			return ctx.author == msg.author and ctx.channel == msg.channel
	await ctx.message.channel.send('Type what you want to be in big blue letters.')
	history = await ctx.message.channel.history(limit=1).flatten()
	last = history[0]
	try:
		msg = await client.wait_for('message', check=same_user_and_channel, timeout=300)
	except asyncio.TimeoutError:
		msg = None
	if msg is None:
		await ctx.message.channel.send('You didn\'t finish in time :(')
		return
	await last.delete()
	blue = big_letters(msg.content)
	log.debug(blue)
	await msg.delete()
	await ctx.message.channel.send(blue[:2000])

def big_letters(s):
	s = s.lower()
	ret = []
	words = s.split(' ')
	for word in words:
		new_word = ' '.join([f':regional_indicator_{letter}:' for letter in list(word)])
		ret.append(new_word)
	return '   '.join(ret)


client.loop.create_task(check_for_changes())
client.loop.create_task(check_for_babish_video())
client.run(TOKEN, bot=True)
