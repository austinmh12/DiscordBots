from datetime import datetime as dt, timedelta as td
from discord.ext import commands
from discord.ext.commands import Bot
from os import execv
from os.path import getmtime
import asyncio
import discord
import logging
import sys
from incremental.player import Player
from incremental.resource import Resource

with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

SCRIPT_PATH = 'S:/OldPC/Python/Bots/discord_bots/Incremental/inc_bot.py'
SCRIPT_MTIME = getmtime(SCRIPT_PATH)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

client = Bot(command_prefix=commands.when_mentioned_or('I.', 'i.'))

@client.event
async def on_ready():
	log.info('Client is ready.') 
	for ch in client.get_all_channels():
		log.debug(f'{ch.name} - {ch.id}')

async def check_for_changes():
	await client.wait_until_ready()
	while not client.is_closed():
		if getmtime(SCRIPT_PATH) != SCRIPT_MTIME:
			log.debug('File has changed, Re-running.')
			execv(sys.executable, ['python'] + sys.argv)
		await asyncio.sleep(1)

client.loop.create_task(check_for_changes())
client.add_cog(Player(client))
client.add_cog(Resource(client))
client.run(ENV['INCTOKEN'], bot=True)