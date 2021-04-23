import logging
from discord.ext.commands import Bot
from discord.ext import commands
from discord import Intents
import asyncio
import os
import sys
from os.path import getmtime, isfile
from mtg.card import CardCog
from mtg.game import GameCog
from mtg.gm import GMCog
from mtg.deck import DeckCog

with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

SCRIPT_PATH = 'S:/OldPC/Python/Bots/discord_bots/DnDxMTG'

intents = Intents.default()
intents.members = True
intents.reactions = True
client = Bot(command_prefix=commands.when_mentioned_or('M.','D.', 'm.', 'd.'))

@client.event
async def on_ready():
	log.info('Client is ready.')
	for ch in client.get_all_channels():
		log.debug(f'{ch.name} - {ch.id}')


async def check_for_changes():
	await client.wait_until_ready()
	files = [(f'{dp}/{f}', getmtime(f'{dp}/{f}')) for dp, _, fs in os.walk(SCRIPT_PATH) for f in fs if '__pycache__' not in dp and '.py' in f]
	while not client.is_closed():
		for file, mtime in files:
			if getmtime(file) != mtime:
				log.debug(f'{file.split("/")[-1]} has changed, re-running.')
				os.execv(sys.executable, ['python'] + sys.argv)
		await asyncio.sleep(1)

client.loop.create_task(check_for_changes())
client.add_cog(CardCog(client))
client.add_cog(GameCog(client))
client.add_cog(GMCog(client))
client.add_cog(DeckCog(client))
client.run(ENV['DNDXMTG'], bot=True)