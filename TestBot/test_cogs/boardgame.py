from . import log, BASE_PATH, Page, MyCog, chunk
from discord import File
from discord.ext import commands, tasks
import asyncio
from PIL import Image, ImageDraw, ImageFont
from random import randint
import typing

# Version
version = '0.1.0'

# Constants

# Functions

# Classes
class BoardGameCog(MyCog):
	available_games = ['yahtzee']

	def __init__(self, bot):
		super().__init__(bot)
		self.yahtzee_game = None
		self.iniatited_games = {
			'yahtzee': {
				'owner': None,
				'players': []
			}
		}

	# Functions
	def initiate_game(self, game, user_id):
		self.iniatited_games[game]['owner'] = user_id
		self.iniatited_games[game]['players'].append(user_id)

	def add_player(self, game, user_id):
		self.iniatited_games[game]['players'].append(user_id)

	def remove_player(self, game, user_id):
		self.iniatited_games[game]['players'].pop(self.iniatited_games[game]['players'].index(user_id))
		if user_id == self.iniatited_games[game]['owner']:
			if self.iniatited_games[game]['players']:
				self.iniatited_games[game]['owner'] = self.iniatited_games[game]['players'][0]
			else:
				self.iniatited_games[game]['owner'] = None

	# Commands
	@commands.group(name='game',
					pass_context=True,
					invoke_without_command=True,
					description='View all the available board games',
					brief='View board games')
	async def game_main(self, ctx):
		desc = 'Welcome to the Board Game Plaza! Here you can view all the available\n'
		desc += 'board games. To initiate, or join, a board game, use **.game <name>**\n'
		desc += 'Once all the players who want to play have joined, the **owner** of\n'
		desc += 'the game instance can start the game with **.game start**\n\n'
		for game in __class__.available_games:
			desc += f'***{game}***\n'
		return await self.paginated_embeds(ctx, Page('Board Games Plaza', desc))

	@game_main.command(name='yahtzee',
					pass_context=True,
					invoke_without_command=True,
					description='Initiate a game of Yahtzee',
					brief='Yahtzee')
	async def game_yahtzee(self, ctx):
		if self.yahtzee_game:
			return await ctx.send('A game of Yahtzee is already ongoing.')
		user_id = ctx.author.id
		if not self.iniatited_games['yahtzee']['owner']:
			self.initiate_game('yahtzee', user_id)
			return await ctx.send(f'A game of Yahtzee has been initiated by <@{user_id}>')
		if user_id in self.iniatited_games['yahtzee']['players']:
			self.remove_player('yahtzee', user_id)
			await ctx.send('You have left the game.')
			if not self.iniatited_games['yahtzee']['owner']:
				return await ctx.send('The game of Yahtzee has been canceled.')
		self.add_player('yahtzee', user_id)
		return await ctx.send('You have joined the game of Yahtzee')

	@game_main.command(name='start',
					pass_context=True,
					invoke_without_command=True,
					description='Start a game that you initiated',
					brief='Starts the game')
	async def game_start(self, ctx):
		...