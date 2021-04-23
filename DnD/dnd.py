import discord, logging, json
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
import os, sys
from os.path import getmtime
from character import CharacterCommands
from field import FieldCommands
from dice import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

SCRIPT_PATH = 'S:/OldPC/Python/Bots/DnD/dnd.py'
SCRIPT_MTIME = getmtime(SCRIPT_PATH)


dnd = Bot(command_prefix=commands.when_mentioned_or('!'))

@dnd.event
async def on_ready():
	log.info('Bot is ready.')

async def check_for_changes():
	await dnd.wait_until_ready()
	while not dnd.is_closed():
		if getmtime(SCRIPT_PATH) != SCRIPT_MTIME:
			log.debug('File has changed, Re-running.')
			os.execv(sys.executable, ['python'] + sys.argv)
		await asyncio.sleep(1)

dnd.loop.create_task(check_for_changes())
dnd.add_cog(CharacterCommands(dnd))
dnd.add_cog(FieldCommands(dnd))
dnd.run(TOKEN, bot=True)