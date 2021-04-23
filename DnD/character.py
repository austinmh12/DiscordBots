from discord.ext import commands
import asyncio
from oauth2client.service_account import ServiceAccountCredentials as SAC
import gspread
import logging
import typing

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
cred = SAC.from_json_keyfile_name('dndbot_scopes.json', scope)
g_sheets = gspread.authorize(cred)
dnd_sheet = g_sheets.open('DnDTest')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

class CharacterCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.players = self.get_character_sheets()

	def get_character_sheets(self):
		scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
		cred = SAC.from_json_keyfile_name('dndbot_scopes.json', scope)
		g_sheets = gspread.authorize(cred)
		return g_sheets.open('DnDTest')

	def get_character_sheet(self, player):
		return self.players.worksheet(player)

	@commands.command()
	async def char(self, ctx, *, player: typing.Optional[str]=''):
		log.debug(player)
		pl = self.get_character_sheet(player) if player else self.get_character_sheet(ctx.message.author.name)
		await ctx.channel.send(pl.cell(2, 2).value)
