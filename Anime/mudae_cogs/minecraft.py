import logging
from discord import Game, Embed, Colour
from discord.utils import get
from discord.ext import commands
import asyncio
import os
import os.path
import subprocess
import re
import threading
import typing
from time import sleep
from queue import Queue, Empty

q = Queue()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

class Minecraft(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.server = None

	## Server related
	@commands.command(name='add_mod',
					pass_context=True,
					description='Add a mod to the server.',
					brief='Add a mod',
					aliases=['am'])
	async def add_mod(self, ctx):
		if self.server and self.server.is_alive():
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
		if self.server and self.server.is_alive():
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
		if self.server:
			return await ctx.send('The server is already up.')
		act = Game('Minecwaft')
		await self.bot.change_presence(activity=act)
		await ctx.send('Starting the server...')
		log.info('Starting the server thread')
		self.server = Server(q)
		self.server.start()
		log.info('The server thread is running')
		reply = await self.listen_for_replies('For help')
		while not reply:
			reply = await self.listen_for_replies('For help')
		reply = reply.split('(')[-1].replace(')', '').replace('!', '').split(' ')[0]
		return await ctx.send(f'The server is up after {reply}.')

	@commands.command(name='stop',
					pass_context=True,
					description='Stops the minecraft server.',
					brief='Stop the server')
	async def stop_server(self, ctx):
		if not self.server:
			return await ctx.send('The server is not up.')
		await ctx.send('Stopping the server...')
		log.info('Stopping the server')
		self.server.stop()
		log.info('Server thread stop called')
		self.server.join()
		log.info('Server thread joined')
		self.server = None
		await self.bot.change_presence()
		while self.server:
			pass
		return await ctx.send('Server is stopped. It is safe to add and remove mods.')

	@commands.command(name='restart',
					pass_context=True,
					description='Restarts the minecraft server.',
					brief='Restart the server')
	async def restart_server(self, ctx):
		if self.server:
			await self.stop_server(ctx)
		await self.start_server(ctx)

	@commands.command(name='status',
					pass_context=True,
					description='Returns the status of the minecraft server.',
					brief='Status of the server.')
	async def server_status(self, ctx):
		if self.server:
			return await ctx.send('The server is running.')
		return await ctx.send('The server is down.')

	## Teleporting
	@commands.command(name='tp',
					pass_context=True,
					description='Teleport command in minecraft',
					brief='Teleports.')
	async def tp(self, ctx, player, *args):
		if not self.server:
			return await ctx.send('Server needs to be running.')
		if len(args) == 1:
			self.server.send_command(f'/tp {player} {args[0]}')
		else:
			self.server.send_command(f'/tp {player} {" ".join(args)}')
		reply = await self.listen_for_replies('Teleported')
		while not reply:
			reply = await self.listen_for_replies('Teleported')
		return await ctx.send(reply)

	## Online players
	@commands.command(name='list',
					pass_context=True,
					description='Lists the players currently in the server',
					brief='Lists online players',
					aliases=['online'])
	async def _list(self, ctx):
		if not self.server:
			return await ctx.send('Server needs to be running.')
		self.server.send_command('/list')
		reply = await self.listen_for_replies('players online')
		while not reply:
			reply = await self.listen_for_replies('players online')
		amt, players = reply.split(':')
		if not players:
			return await ctx.send('There are no players online.')
		desc = '\n'.join([p.strip() for p in players.split(',')])
		ret = Embed(
			title='Online Players',
			description=desc,
			colour=Colour.from_rgb(141, 195, 104)
		)
		ret.set_footer(text=f'{amt.split(" ")[2]}/20')
		return await ctx.send(embed=ret)

	## Weather
	@commands.command(name='weather',
					pass_context=True,
					description='Sets the weather to the specified type',
					brief='Sets the weather')
	async def weather(self, ctx, type, duration: typing.Optional[int] = 120):
		if not self.server:
			return await ctx.send('Server needs to be running.')
		if type.lower() not in ['clear', 'rain', 'thunder']:
			return await ctx.send(f'{type} is not a valid weather (clear, rain, thunder)')
		self.server.send_command(f'/weather {type.lower()} {duration}')
		reply = await self.listen_for_replies('weather to')
		while not reply:
			reply = await self.listen_for_replies('weather to')
		return await ctx.send(f'The weather has been set to {type} for {duration}s')

	@commands.command(name='clear',
					pass_context=True,
					description='Sets the weather to clear',
					brief='Sets the weather to clear')
	async def clear(self, ctx, duration: typing.Optional[int] = 120):
		return await self.weather(ctx, 'clear', duration)

	@commands.command(name='rain',
					pass_context=True,
					description='Sets the weather to rain',
					brief='Sets the weather to rain')
	async def rain(self, ctx, duration: typing.Optional[int] = 120):
		return await self.weather(ctx, 'rain', duration)

	@commands.command(name='thunder',
					pass_context=True,
					description='Sets the weather thunder',
					brief='Sets the weather thunder')
	async def thunder(self, ctx, duration: typing.Optional[int] = 120):
		return await self.weather(ctx, 'thunder', duration)

	# Time
	@commands.command(name='time',
					pass_context=True,
					description='Sets or adds the specified time.',
					brief='Sets or adds time')
	async def _time(self, ctx, action, amt):
		if not self.server:
			return await ctx.send('Server needs to be running.')
		if action.lower() not in ['set', 'add']:
			return await ctx.send(f'{action} is not a valid action (set, add)')
		try:
			amt = int(amt)
			self.server.send_command(f'/time {action} {amt}')
		except Exception as e:
			log.error(str(e))
			self.server.send_command(f'/time {action} {amt}')
		reply = await self.listen_for_replies('Set the time')
		while not reply:
			reply = await self.listen_for_replies('Set the time')
		return await ctx.send(reply)

	@commands.command(name='day',
					pass_context=True,
					description='Sets the time to day.',
					brief='Sets the time to day')
	async def day(self, ctx):
		return await self._time(ctx, 'set', 'day')

	@commands.command(name='night',
					pass_context=True,
					description='Sets the time to night.',
					brief='Sets the time to night')
	async def night(self, ctx):
		return await self._time(ctx, 'set', 'night')

	@commands.command(name='midnight',
					pass_context=True,
					description='Sets the time to midnight.',
					brief='Sets the time to midnight')
	async def midnight(self, ctx):
		return await self._time(ctx, 'set', 'midnight')

	@commands.command(name='noon',
					pass_context=True,
					description='Sets the time to noon.',
					brief='Sets the time to noon')
	async def noon(self, ctx):
		return await self._time(ctx, 'set', 'noon')

	# Chat functions
	@commands.command(name='say',
					pass_context=True,
					description='Enables chat between discord and minecraft',
					brief='Xplat chat')
	async def say(self, ctx, *msg):
		if not self.server:
			return await ctx.send('Server needs to be running.')
		msg = ' '.join(msg)
		self.server.send_command(f'/say {ctx.author.nick}: {msg}')

	async def listen_for_replies(self, note):
		if self.server and self.server.is_alive():
			try:
				while q.empty() is False:
					reply = q.get()
					if note in reply:
						return reply
			except Empty:
				return
		else:
			return

class Server(threading.Thread):
	def __init__(self, q):
		super().__init__()
		self.running = True
		self._stop_event = threading.Event()

	def run(self):
		log.info('Server thread - starting')
		self.p = subprocess.Popen(['java', '-Xms4G', '-Xmx8G', '-jar', 'forge-1.16.3-34.1.35.jar', 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
		log.info('Server process started')
		while self.p.poll() is None:
			while self.running:
				line = self.p.stdout.readline().decode('utf8')
				if 'STDERR' in line or 'ERROR' in line:
					continue
				msg = line.split(']: ')[-1].strip()
				if msg:
					log.debug(msg)
					q.put(msg)
				sleep(.01)
			break
		return
			
	def stop(self):
		log.info('Stopping')
		self.send_command('/stop')
		sleep(2.5)
		log.info('Server stopped')
		self._stop_event.set()
		log.info('Stop set')
		self.running = False
		log.info('Running false')

	def send_command(self, command):
		# TODO: Return server response
		cmd = bytes(f'{command}\r\n', 'ascii')
		self.p.stdin.write(cmd)
		self.p.stdin.flush()