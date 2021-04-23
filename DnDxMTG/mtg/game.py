from discord.ext import commands
import asyncio
from . import sql, parse_args, mtgapi
import logging
import re
import typing
from discord import Member, Embed, Colour

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

class GameCog(commands.Cog):
	KEYWORDS = {
		'first strike': 'Gives advantage on attacking rolls',
		'haste': 'Removes summoning sickness from a creature',
		'flying': 'Give advantage on attacks against non-flying creatures, and non-flying attackers have disadvantage',
		'vigilance': 'Creature is unable to provoke attacks of opportunity',
		'defender': 'Attackers have disadvantage on attack rolls',
		'deathtouch': 'Lowers critical attack threshold by creatures power, e.g. a 3/2 would crit on 18, 19, or 20',
		"can't block": 'Attackers have advantage on attack rolls',
		'destroy': 'Rolling higher than 20-CMC will cause the spell to hit. E.g. Doom Blade (CMC 2) needs a 19 or 20 to hit',
		'fight': 'Taunts a target creature to move to and attack another target creature',
		'counter': 'Dispels magic or breaks concentration on a sustained spell',
		'exile': 'Destroy the creature and remove from battlefield (can\'t be regenerated)',
		'mill': 'Cycle the top x cards of the library to the bottom of target player\'s library',
		'sacrifice': 'Destroy target creature, can be regenerated',
		'scry': 'MTG rules',
		'tap': 'Remove all actions from target creature',
		'untap': 'Restore all actions to target creature',
		'double strike': 'Multi-attack',
		'hexproof': 'MTG rules',
		'indestructible': 'MTG rules',
		'lifelink': 'MTG rules but to that creature only',
		'protection': 'Attackers of the protection criteria have disadvantage',
		'prowess': 'MTG rules',
		'reach': 'Normal attacks against flying creatures, and flying attackers don\'t have advantage',
		'trample': 'Cleave',
		'adapt': 'MTG rules',
		'afterlife': 'MTG rules',
		'annihilator': 'The x closest enemy creatures roll a con save. Failing loses half the creatures current HP rounded up',
		'ascend': 'MTG rules',
		'regenerate': 'If the creature were to take lethal damage, it instead has 1 hp',
		'flash': 'Can be summoned using a bonus action',

	}

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='keyword',
					pass_context=True,
					description='Searches for the DnD description of a MTG keyword',
					brief='DnD version of MTG keyword',
					aliases=['kw'])
	async def keyword(self, ctx, *kw):
		kw = ' '.join(kw).lower()
		_kw = ' '.join([k.capitalize() for k in kw.split()])
		return await ctx.send(f'**{_kw}**: {__class__.KEYWORDS.get(kw), "N/A"}')