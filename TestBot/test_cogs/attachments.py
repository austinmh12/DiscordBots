import logging
from discord.ext import commands
import asyncio
import os
import os.path
import subprocess
import re

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

class AttachmentHandler(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.p = None

	@commands.command(name='add_mod',
					pass_context=True,
					description='Add a mod to the server.',
					brief='Add a mod',
					aliases=['am'])
	async def add_mod(self, ctx):
		if self.p and self.p.poll() is None:
			return await ctx.send('Cannot add mods while the server is running.')
		if not ctx.message.attachments:
			return await ctx.send('There was no mod attached.')
		if not ctx.message.attachments[0].filename[-3:] == 'jar':
			return await ctx.send('That is not a jar file.')
		await ctx.send(f'Adding {ctx.message.attachments[0].filename} to mod list')
		await ctx.message.attachments[0].save(f'mods/{ctx.message.attachments[0].filename}')

	@commands.command(name='remove_mod',
					pass_context=True,
					description='Remove a mod from the server.',
					brief='Removes a mod',
					aliases=['rm'])
	async def remove_mod(self, ctx, modname):
		if self.p and self.p.poll() is None:
			return await ctx.send('Cannot remove mods while the server is running.')
		modname = modname + '.jar' if '.jar' not in modname else modname
		if not os.path.exists(f'mods/{modname}'):
			return await ctx.send(f'Mod {modname} does not exist.')
		os.remove(f'mods/{modname}')
		return await ctx.send(f'Deleted {modname} from the server.')

	@commands.command(name='list_mods',
					pass_context=True,
					description='List all of the mods on the server.',
					brief='List the mods',
					aliases=['lm'])
	async def list_mods(self, ctx):
		mods = [f for f in os.listdir('mods') if os.path.isfile(os.path.join('mods', f))]
		mods.sort()
		ret = '\n'.join(mods)
		return await ctx.send(ret)

	@commands.command(name='start',
					pass_context=True,
					description='Starts the minecraft server.',
					brief='Start the server')
	async def start_server(self, ctx):
		args = ['java', '-Xms4G', '-Xmx8G', '-jar', 'forge-1.16.3-34.1.35.jar', 'nogui']
		arg_pat = r'.*(?P<time_str>\d+\.\d+s).*'
		await ctx.send('Starting the server...')
		self.p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		while self.p.poll() is None:
			line = self.p.stdout.readline().decode('utf8')
			if line:
				msg = line.split(']: ')[-1]
				if re.match(arg_pat, msg):
					match = re.match(arg_pat, msg)
					_time = match.group('time_str')
					return await ctx.send(f'Server is up, it took {_time}')

	@commands.command(name='stop',
					pass_context=True,
					description='Stops the minecraft server.',
					brief='Stop the server')
	async def stop_server(self, ctx):
		await ctx.send('Stopping the server...')
		self.p.kill()
		self.p = None
		return await ctx.send('Server is stopped. It is safe to add and remove mods.')