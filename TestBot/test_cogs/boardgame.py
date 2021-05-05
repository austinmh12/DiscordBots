from . import log, BASE_PATH, Page, MyCog, chunk
from discord import File
from discord.ext import commands, tasks
import asyncio
from PIL import Image, ImageDraw, ImageFont
from random import randint
import typing
from . import boardgameFunctions as BGF
from .boardgameFunctions import yahtzee

# Version
version = '0.2.0'

# Constants

# Functions

# Classes
class BoardGameCog(MyCog):
	available_games = ['yahtzee']

	def __init__(self, bot):
		super().__init__(bot)
		self.yahtzee_game = None
		self.iniatited_games = {
			'yahtzee': {'owner': None, 'players': []}
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
	@commands.command(name='games',
					pass_context=True,
					description='View all the available board games',
					brief='View board games')
	async def games(self, ctx):
		desc = 'Welcome to the Board Game Plaza! Here you can view all the available\n'
		desc += 'board games. To initiate, or join, a board game, use **.<game name>**\n'
		desc += 'Once all the players who want to play have joined, the **owner** of\n'
		desc += 'the game instance can start the game with **.<game name> start**\n\n'
		for game in __class__.available_games:
			desc += f'***{game}***\n'
		return await self.paginated_embeds(ctx, Page('Board Games Plaza', desc))

	###########
	# Yahtzee #
	###########
	@commands.group(name='yahtzee',
					pass_context=True,
					invoke_without_command=True,
					description='Initiate a game of Yahtzee',
					brief='Yahtzee',
					aliases=['y'])
	async def yahtzee_main(self, ctx):
		if self.yahtzee_game:
			return await ctx.send('A game of Yahtzee is already ongoing.')
		yahtzee_info = self.iniatited_games['yahtzee']
		if not yahtzee_info['owner']:
			self.initiate_game('yahtzee', ctx.author.id)
			return await ctx.send(f'A game of Yahtzee has been initiated by <@{ctx.author.id}>')
		if ctx.author.id in yahtzee_info['players']:
			self.remove_player('yahtzee', ctx.author.id)
			await ctx.send('You have left the game.')
			if not yahtzee_info['owner']:
				return await ctx.send('The game of Yahtzee has been canceled.')
		self.add_player('yahtzee', ctx.author.id)
		return await ctx.send('You have joined the game of Yahtzee')

	@yahtzee_main.command(name='start',
					pass_context=True,
					description='Start a game that you initiated',
					brief='Starts the game')
	async def yahtzee_start(self, ctx):
		if self.yahtzee_game:
			return await ctx.send('A game of Yahtzee is already ongoing.')
		yahtzee_info = self.iniatited_games['yahtzee']
		if yahtzee_info['owner'] == ctx.author.id:
			self.yahtzee_game = yahtzee.YahtzeeGame(yahtzee_info['players'])
			return await ctx.send('The game of Yahtzee has started')
		return await ctx.send('You didn\'t initiate a game of Yahtzee.')

	@yahtzee_main.command(name='end',
					pass_context=True,
					description='End a game that you initiated',
					brief='Ends the game')
	async def yahtzee_end(self, ctx):
		yahtzee_info = self.iniatited_games['yahtzee']
		if yahtzee_info['owner'] == ctx.author.id:
			self.yahtzee_game = None
			self.iniatited_games['yahtzee'] = {'owner': None, 'players': []}
			return await ctx.send('The game of Yahtzee has been ended')
		return await ctx.send('You didn\'t initiate this game.')