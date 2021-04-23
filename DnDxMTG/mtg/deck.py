from discord.ext import commands
import asyncio
from . import sql
from .card import Card, Creature
import logging
from discord import Member, Embed, Colour
from string import ascii_uppercase, ascii_lowercase

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

BACK = '\u2b05\ufe0f' # Left arrow
NEXT = '\u27a1\ufe0f' # Right arrow
YES = '\u2705' # white checkmark
NO = '\u274C' # Red x
PLAY = '\u2b06\ufe0f' # Up arrow

class DeckCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def get_deck(self, discord_id, name):
		df = sql('SELECT * FROM decks WHERE discord_id = ? AND name = ?', (discord_id, name))
		if df.empty:
			return None
		return Deck(**df.to_dict('records')[0])

	def get_decks(self, discord_id):
		df = sql('SELECT * FROM decks WHERE discord_id = ?', (discord_id,))
		if df.empty:
			return []
		return [Deck(**d) for d in df.to_dict('records')]

	def add_deck(self, deck):
		if not self.get_deck(deck.discord_id, deck.name):
			sql('INSERT INTO decks VALUES (?,?,?)', deck.row)

	def update_deck(self, deck):
		sql('UPDATE decks SET cards = ? WHERE discord_id = ? AND name = ?', (deck.row[-1], deck.discord_id, deck.name))


	@commands.command(name='create_deck',
					pass_context=True,
					description='Creates an empty deck for you to add cards to and use in the campaign',
					brief='Creates a deck',
					aliases=['cd'])
	async def create_deck(self, ctx, name):
		if self.get_deck(ctx.author.id, name):
			return await ctx.send('You already have a deck with that name.')
		deck = Deck(ctx.author.id, name, '')
		self.add_deck(deck)
		return await ctx.send(f'Created the deck {deck.name}') # use m.add_cards to add cards

	@commands.command(name='search_decks',
					pass_context=True,
					description='Searches for your created decks',
					brief='Searches for a deck',
					aliases=['sd'])
	async def search_decks(self, ctx, name):
		deck = self.get_deck(ctx.author.id, name)
		if deck and not deck.cards:
			return await ctx.send(f'{deck.name} exists but has no cards yet.')
		if deck and deck.cards:
			idx = 0
			emb = deck.cards[idx].embed
			emb.set_footer(text=f'{idx + 1}/{len(deck.cards)} — {deck.name}')
			msg = await ctx.send(embed=emb)
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

			def is_left_right(m):
				log.debug(m.emoji.name.encode('ascii', 'backslashreplace'))
				return all([
					(m.emoji.name == BACK or m.emoji.name == NEXT),
					m.member.id != self.bot.user.id,
					m.message_id == msg.id,
					m.member.id == ctx.author.id
				])

			while True:
				try:
					react = await self.bot.wait_for('raw_reaction_add', check=is_left_right, timeout=60)
				except asyncio.TimeoutError:
					log.debug('Timeout, breaking')
					break
				if react.emoji.name == NEXT:
					idx = (idx + 1) % len(deck.cards)
					await msg.remove_reaction(NEXT, react.member)
				else:
					idx = (idx - 1) % len(deck.cards)
					await msg.remove_reaction(BACK, react.member)
				emb = deck.cards[idx].embed
				emb.set_footer(text=f'{idx + 1}/{len(deck.cards)} — {deck.name}')
				await msg.edit(embed=emb)
		return await ctx.send(f'No deck exists with that name.')

	@commands.command(name='list_decks',
					pass_context=True,
					description='Lists all the decks you\'ve created',
					brief='All your decks',
					aliases=['ld'])
	async def list_decks(self, ctx):
		decks = self.get_decks(ctx.author.id)
		if decks:
			emb = Embed(
				title=f'{ctx.author.name}\'s Decks',
				description='\n'.join([f'**{d.name}** - {len(d.cards)}' for d in decks]),
				colour=Colour.from_rgb(157, 120, 78)
			)
			return await ctx.send(embed=emb)
		return await ctx.send('You have no decks.')

	@commands.command(name='add_cards',
					pass_context=True,
					description='Add cards to a deck',
					brief='Add cards to a deck',
					aliases=['ac'])
	async def add_cards(self, ctx, name):
		...


class Deck:

	trans = str.maketrans({u:"_"+l for u,l in zip(ascii_uppercase, ascii_lowercase)})

	def __init__(self, discord_id, name, cards, **kwargs):
		self.discord_id = discord_id
		self.name = name
		self.cards = self.get_cards(cards)

	def get_cards(self, cards):
		if cards:
			log.debug(cards)
			df = sql(f'SELECT * FROM cards WHERE multiverseid in ({cards})', ())
			return list(set([self.gen_card(c) for c in df.to_dict('records')]))
		return []

	def gen_card(self, card):
		card = {k.translate(__class__.trans): v for k, v in card.items()}
		if card.get('types', None):
			card['type'] = card.get('types')[0]
		if card.get('type') == 'Creature':
			return Creature(**card)
		return Card(**card)

	@property
	def row(self):
		return (self.discord_id, self.name, ','.join([c.multiverseid for c in self.cards]))
	
