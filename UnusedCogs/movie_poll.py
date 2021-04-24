import logging
from discord.ext import commands
from random import choice

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s'))
log.addHandler(stream_handler)

REGIONAL_INDICATOR_Y = '\U0001f1fe'
REGIONAL_INDICATOR_N = '\U0001f1f3'

class Movies(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.movies = self.get_movies()
		self.last_movie = None

	def get_movies(self):
		with open('./movieList.txt') as f:
			return list(set([m.strip() for m in f.readlines()]))

	def save_movies(self):
		with open('./movieList.txt', 'w') as f:
			for movie in list(set([m.lower() for m in self.movies])):
				f.write(movie + '\n')

	def update_movies(self, movie, remove=False):
		if remove:
			self.movies.pop(self.movies.index(movie))
		else:
			self.movies.append(movie)
		self.save_movies()
		self.movies = self.get_movies()

	async def __vote(self, ctx, pick=''):
		random_movie = choice(self.movies) if not pick else pick
		self.last_movie = await ctx.channel.send(f'{random_movie}')
		await self.last_movie.add_reaction(REGIONAL_INDICATOR_Y)
		await self.last_movie.add_reaction(REGIONAL_INDICATOR_N)
		await ctx.channel.send('Voting ends in 3 seconds!')
		log.debug(self.last_movie)
		await asyncio.sleep(3)
		self.last_movie = await ctx.channel.fetch_message(self.last_movie.id)
		yes = self.last_movie.reactions[0].count
		no = self.last_movie.reactions[1].count
		if yes > no:
			await ctx.channel.send(f"We'll be watching {random_movie}! Yay!")
			self.update_movies(random_movie, True)
		elif yes < no:
			await ctx.channel.send(f"I guess we'll look for a different movie :(")
			await self.__vote(ctx)
			return
		else:
			await ctx.channel.send(f"Hmm... Let's try again.")
			await self.__vote(ctx, pick=random_movie)
			return

	@commands.command()
	async def r(self, ctx, *, movie):
		log.debug(movie)
		if movie.lower() in self.movies:
			await ctx.channel.send(f'{movie} is already in the list of movies!')
			return
		self.update_movies(movie)
		await ctx.channel.send(f'{movie} has been added to the list :)')
		log.debug(self.movies)

	@commands.command()
	async def vote(self, ctx):
		await self.__vote(ctx)
		return


	@commands.Cog.listener()
	async def on_raw_reaction_add(self, r):
		log.debug(r.emoji.name.encode('ascii', 'backslashreplace'))