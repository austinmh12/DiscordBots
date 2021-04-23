import discord, logging, json
from datetime import datetime as dt, timedelta as td
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
import requests as r
import os, sys
from os.path import getmtime
from random import choice

SCRIPT_PATH = 'S:/OldPC/Python/Brendan/brendan.py'
SCRIPT_MTIME = getmtime(SCRIPT_PATH)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

client = Bot(command_prefix=commands.when_mentioned_or('!', 'L.'))
brendan_discord_id = '311306843718942740'

GUILD_ID = 549390998506307595
LAIDO_ID = 550770497667989505
LONELY_ID = 549390998506307599
MIEST_ID = 608091756646629380

colours = ['css','yaml','fix','diff']
last_message = None

@client.event
async def on_ready():
	act = discord.Activity(name='@Laido', type=discord.ActivityType.listening)
	await client.change_presence(activity=act)
	log.debug('Client is ready.')
	# log.info('Ready to @Laido.')
	# for i in client.get_all_members():
	# 	log.info(f'{i} {i.id}')

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.channel.name == 'bot-test':
		# log.info(f'{message.role_mentions}')
		cnt = message.content
		colour = choice(colours)
		log.debug(cnt)
		await message.delete()
		await message.channel.send(f'{message.author.nick}```{colour}\n{choice(["-","+","---"]) if colour == "diff" else ""}{cnt}\n```')

	if str(message.author.id) == brendan_discord_id:
		log.warning('This is Brendan.')
		await client.process_commands(message)
		return

	if message.channel.name != 'getting-brendans-attention':
		# cnt = message.content
		# colour = choice(colours)
		# log.debug(cnt)
		# await message.delete()
		# await message.channel.send(f'{message.author.nick}```{colour}\n{choice(["-","+","---"]) if colour == "diff" else ""}{cnt}\n```')
		return

	ments = [str(ment.id) for ment in message.mentions]
	role_ments = [rment.id for rment in message.role_mentions]
	if brendan_discord_id in ments and LAIDO_ID in role_ments:
		log.warning('Brendan is already @\'d.')
		await client.process_commands(message)
		return

	else:
		log.info('@ing Brendan.')
		log.debug(message.attachments)
		atch = message.attachments[0] if message.attachments else None
		if atch:
			resp = r.get(atch.url)
			ext = atch.filename.split('.')[-1]
			with open(f'tmp.{ext}', 'wb') as f:
				f.write(resp.content)
			file = discord.File(f'tmp.{ext}')
		msg = message.content
		at_d_msg = f'<@&{LAIDO_ID}> ' + msg
		last_author = (str(message.author.id))
		await message.delete()
		if atch:
			await message.channel.send(at_d_msg, file=file)
			await asyncio.sleep(2)
			os.remove(f'tmp.{ext}')
		else:
			await message.channel.send(at_d_msg)

@client.event
async def on_voice_state_update(user, before, after):
	if after.channel:
		if after.channel.name == 'Austin\'s Home':
			if user.name != 'rectrec369':
				await user.move_to(None)

async def check_for_changes():
	await client.wait_until_ready()
	while not client.is_closed():
		if getmtime(SCRIPT_PATH) != SCRIPT_MTIME:
			log.debug('File has changed, Re-running.')
			os.execv(sys.executable, ['python'] + sys.argv)
		await asyncio.sleep(1)

def refresh_tasks():
	os.execv(sys.executable, ['python'] + sys.argv)



client.loop.create_task(check_for_changes())
client.run(TOKEN, bot=True)