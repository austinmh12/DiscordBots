from datetime import datetime as dt, timedelta as td
from discord import Member, Embed, Colour
from discord.ext import commands
from discord.ext.commands import Bot
import os
from os.path import getmtime
import asyncio
import discord
import logging
import sys
import typing

with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

SCRIPT_PATH = f"{ENV['WINPATH']}/AustinBot" if sys.platform == 'win32' else f'{ENV["LINUXPATH"]}/AustinBot'

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

intents = discord.Intents.default()
intents.members = True
client = Bot(command_prefix=commands.when_mentioned_or('.'), intents=intents, help_command=None)

@client.event
async def on_ready():
	log.info('Client is ready.')

@client.event
async def on_reaction_add(r, u):
	if r.emoji == '\u2705':
		await r.message.add_reaction('<:backchk:799333634263613440>')

@client.command(name='sheesh',
				pass_context=True,
				description='Sheesh',
				brief='sheesh')
async def sheesh(ctx, e: typing.Optional[int] = 4, user: typing.Optional[Member] = None):
	await ctx.message.delete()
	e = 4 if e < 4 else e
	e = 1900 if e > 1900 else e # discord api limit is 2000
	if user:
		return await ctx.send(f'***SHEE{"e"*e}***eeesh <@{user.id}>\n> - _{ctx.author.display_name}_')
	return await ctx.send(f'***SHEE{"e"*e}***eeesh\n> - _{ctx.author.display_name}_')

@client.command(name='sheesha',
				pass_context=True,
				description='Sheesh anonymously',
				brief='sheesh')
async def sheesha(ctx, e: typing.Optional[int] = 4, user: typing.Optional[Member] = None):
	await ctx.message.delete()
	e = 4 if e < 4 else e
	e = 1900 if e > 1900 else e # discord api limit is 2000
	if user:
		return await ctx.send(f'***SHEE{"e"*e}***eeesh <@{user.id}>')
	return await ctx.send(f'***SHEE{"e"*e}***eeesh')

@client.command()
async def help(ctx, cog_name: typing.Optional[str] = 'PokeRoulette'):
	cog = client.cogs.get(cog_name, None)
	if not cog:
		return
	commands = [(cmd.name, cmd.usage, cmd.description) for cmd in cog.get_commands() if not cmd.hidden]
	commands.sort(key=lambda x: x[0])
	descs = []
	desc = ''
	for name, usage, description in commands:
		tmp = f'**{name}**{" _"+usage+"_" if usage else ""}: {description}\n'
		if len(desc) + len(tmp) > 2000:
			descs.append(desc)
			desc = ''
		desc += tmp
	descs.append(desc)
	embs = []
	for i, desc in enumerate(descs):
		if i == 0:
			embs.append(Embed(title=f'{cog_name} Help', description=desc, colour=Colour.from_rgb(255, 50, 20)))
		else:
			embs.append(Embed(description=desc, colour=Colour.from_rgb(255, 50, 20)))
	for emb in embs:
		await ctx.author.send(embed=emb)
	return await ctx.send('DM\'d you the help!')

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
client.run(ENV['AUSTINTOKEN'], bot=True)
