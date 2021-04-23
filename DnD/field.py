from PIL import Image as Img, ImageDraw as IDraw
from discord.ext import commands
import discord
import logging
import typing

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

class FieldCommands(commands.Cog):
	def __init__(self, bot, grid=10):
		self.bot = bot
		self.grid = grid

	@commands.command()
	async def field(self, ctx, w: typing.Optional[int]=100, h: typing.Optional[int]=100):
		log.debug(f'Drawing field of size: ({w}, {h}) and grid of size: {self.grid}')
		img = Img.new('RGB', (w, h), color='green')
		draw = IDraw.Draw(img)
		for i in range(1, w // self.grid):
			draw.line((i*self.grid, 0, i*self.grid, h), fill='#fff')
		for i in range(1, h // self.grid):
			draw.line((0, i*self.grid, w, i*self.grid), fill='#fff')
		img.save('tmp.png')
		f = discord.File('tmp.png')
		await ctx.channel.send(file=f)
		f.close()
