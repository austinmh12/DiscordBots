from datetime import datetime as dt, timedelta as td
from sqlite3 import connect
import pandas as pd
import logging
from discord.ext import commands

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

#############
# Constants #
#############
BASE_PATH = './all_cogs'
BACK = '\u2b05\ufe0f' # Left arrow
NEXT = '\u27a1\ufe0f' # Right arrow

#############
# Functions #
#############
def format_remaining_time(date):
	time = date - dt.now()
	hrs, rem = divmod(time.total_seconds(), 3600)
	min_ = rem // 60 + 1
	if min_ == 60 and hrs:
		min_ = 59
	if hrs:
		return f'{int(hrs)}h {int(min_)}min'
	return f'{int(min_)}min'

def chunk(l, size):
	for i in range(0, len(l), size):
		yield l[i:i+size]

def sql(file, query, args=()):
	conn = connect(f'{BASE_PATH}/{file}.db', isolation_level=None)
	cur = conn.cursor()
	cur.execute(query, args)
	try:
		_df = pd.DataFrame.from_records(cur.fetchall(), columns=[desc[0] for desc in cur.description])
		conn.close()
		return _df
	except Exception:
		return pd.DataFrame()

###########
# Classes #
###########
class Page:
	def __init__(self, author, desc, colour=(255, 50, 20), title=None, icon=None, image=None, thumbnail=None, footer=None):
		self.author = author
		self.desc = self.parse_desc(desc)
		self.colour = colour
		self.title = title
		self.icon = icon
		self.image = image
		self.thumbnail = thumbnail
		self.footer = footer

	@property
	def embed(self):
		emb = Embed(
			description=self.desc,
			colour=Colour.from_rgb(*self.colour)
		)
		if self.title:
			emb.title = self.title
		if self.icon:
			emb.set_author(name=self.author, icon_url=self.icon)
		else:
			emb.set_author(name=self.author)
		if self.image:
			emb.set_image(url=self.image)
		if self.thumbnail:
			emb.set_thumbnail(url=self.thumbnail)
		if self.footer:
			emb.set_footer(text=self.footer)
		return emb

	def parse_desc(self, desc):
		if isinstance(desc, str):
			return desc
		elif isinstance(desc, list) or isinstance(desc, tuple):
			return '\n'.join(desc)
		else:
			raise TypeError(f'Expected str or iterable, got {type(desc)}')

class MyCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def paginated_embeds(self, ctx, pages, content=''):
		idx = 0
		if not isinstance(pages, list):
			pages = [pages]
		emb = pages[idx].embed
		if len(pages) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
		msg = await ctx.send(content, embed=emb)
		if len(pages) > 1:
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

			def is_left_right(m):
				return all([
					(m.emoji.name == BACK or m.emoji.name == NEXT),
					m.member.id != self.bot.user.id,
					m.message_id == msg.id
				])

			while True:
				try:
					react = await self.bot.wait_for('raw_reaction_add', check=is_left_right, timeout=60)
				except asyncio.TimeoutError:
					log.debug('Timeout, breaking')
					break
				if react.emoji.name == NEXT:
					idx = (idx + 1) % len(pages)
					await msg.remove_reaction(NEXT, react.member)
				else:
					idx = (idx - 1) % len(pages)
					await msg.remove_reaction(BACK, react.member)
				emb = pages[idx].embed
				emb.set_footer(text=f'{idx + 1}/{len(pages)}')
				await msg.edit(content=content, embed=emb)