from . import log
from datetime import datetime as dt, timedelta as td
from discord.ext import commands
from discord import File
import asyncio
import requests as r

# Version
version = '0.0.1'

# Constants
brendans_channel = 587447130474414086
brendans_id = 311306843718942740

# Utility Functions

# Classes
class BrendanCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.channel.id != brendans_channel or msg.author == self.bot.user or msg.author.id == brendans_id:
			return

		if brendans_id in [m.id for m in msg.mentions]:
			log.info('Brendan is already mentioned.')
			return

		atch = msg.attachments[0] if msg.attachments else None
		if atch:
			resp = r.get(atch.url)
			ext = atch.filename.split('.')[-1]
			with open(f'tmp.{ext}', 'wb') as f:
				f.write(resp.content)
			file = discord.File(f'tmp.{ext}')
		at_d_msg = f'<@{brendans_id}> ' + msg.content
		await msg.delete()
		if atch:
			await msg.channel.send(at_d_msg, file=file)
			await asyncio.sleep(2)
			file.close()
			os.remove(f'tmp.{ext}')
		else:
			await msg.channel.send(at_d_msg)