from . import log, BASE_PATH, Page, MyCog, chunk, sql, format_remaining_time, BACK, NEXT
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint
import typing
import os.path
from datetime import datetime as dt, timedelta as td

from .rpgFunctions import character as Character
from .rpgFunctions import profession
from .rpgFunctions import player as Player
from .rpgFunctions import equipment
from .rpgFunctions import area
from .rpgFunctions import combat
from .rpgFunctions import consumable
from .rpgFunctions import spell
from .rpgFunctions.database import initialise_db, migrate_db

# Version
version = '2.1.1'

# Constants
attack_emoji = '\u2694\ufe0f'
run_emoji = '\U0001f45f'
# equip_emoji = '\u2705'
equip_emoji = '<:equip:846532309632286720>'
sell_emoji = '\U0001fa99'
potion_emoji = '<:potion:846535026753011772>'
spell_equip_emoji = '<:spell_equip:846733184527892500>'
spell1_emoji = '<:spell1:846733202487902239>'
spell2_emoji = '<:spell2:846733211036155935>'
spell3_emoji = '<:spell3:846733218605826049>'
spell4_emoji = '<:spell4:846733227620040714>'
spell_emojis = [spell1_emoji, spell2_emoji, spell3_emoji, spell4_emoji]
main_hand = '\U0001f5e1\ufe0f'
off_hand = '\U0001f6e1\ufe0f'

# Functions
def is_same_user_channel(ctx):
	def check_same_user_channel(msg):
		return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
	return check_same_user_channel

# Classes
class RPGCog(MyCog):
	def __init__(self, bot):
		super().__init__(bot)
		if not os.path.exists(f'{BASE_PATH}/rpg.db'):
			log.info('Initialising database.')
			initialise_db()
		migrate_db(version)
		self.heal_all_characters.start()

	# Utilities
	async def get_reply(self, ctx, message, return_type=str):
		await ctx.send(message)
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			await ctx.send('You ran out of time.')
			return None
		if return_type == bool:
			return reply.content.lower() in ['y', 't', 'yes', 'true']
		elif return_type == int:
			try:
				return int(reply.content)
			except ValueError:
				return 0
		else:
			return reply.content

	# Listeners

	# Commands
	## Characters
	@commands.group(name='character',
					pass_context=True,
					invoke_without_command=True,
					description='Main command for character related functions',
					brief='Character related commands',
					aliases=['char'])
	async def character_main(self, ctx):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		chars = Character.get_characters(p.id, p.guild_id)
		desc = f'**Current Character:** '
		if p.current_character:
			desc += p.current_character.name
		desc += '\n\n__All characters__\n'
		desc += '\n'.join([f'{":skull_crossbones: " + format_remaining_time(c._death_timer) + " " if c._death_timer > dt.now() else ""}**{c.name}** ({c.profession.name}) --- _{c.level}_' for c in chars])
		page = Page(ctx.author.display_name, desc, colour=(150, 150, 150), icon=ctx.author.avatar_url)
		return await self.paginated_embeds(ctx, page)

	@character_main.command(name='create',
							pass_context=True,
							description='Create a character',
							brief='Create a character',
							aliases=['c'])
	async def character_create(self, ctx, name: typing.Optional[str] = '', prof: typing.Optional[str] = ''):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		marked_for_deletion = False
		if len(Character.get_characters(p.id, p.guild_id)) >= 5:
			return await ctx.send('You can only have 5 characters')
		if not name:
			name = await self.get_reply(ctx, 'What is your character\'s name?')
			if name is None:
				return await ctx.send('You must provide a name.')
		existing_char = Character.get_character(p.id, p.guild_id, name)
		if existing_char:
			msg = f'You have a character named **{existing_char.name}**, do you want to overwrite them? (y/n)'
			marked_for_deletion = await self.get_reply(ctx, msg, bool)
			if marked_for_deletion is None:
				return await ctx.send(f'You will keep **{existing_char.name}**')
		while prof.lower() not in profession.all_professions:
			prof = await self.get_reply(ctx, 'What is your desired profession?')
			if prof is None:
				return
		prof = profession.get_profession(prof)
		if prof.weight == 'Light':
			starting_chest = equipment.get_equipment(10)
			starting_legs = equipment.get_equipment(11)
		elif prof.weight == 'Medium':
			starting_chest = equipment.get_equipment(8)
			starting_legs = equipment.get_equipment(9)
		else:
			starting_chest = equipment.get_equipment(5)
			starting_legs = equipment.get_equipment(6)
		char = Character.Character(
			p.id, 
			p.guild_id, 
			name, 
			prof, 
			1, # level
			0, # exp
			0, # gold
			None, # helmet
			starting_chest, # chest
			starting_legs, # legs
			None, # boots
			None, # gloves
			None, # amulet
			None, # ring
			prof.starting_weapon,
			prof.starting_off_hand
		)
		if existing_char and marked_for_deletion:
			Character.delete_character(p.id, p.guild_id, existing_char.name)
		Character.add_character(char)
		p.current_character = char
		p.update()
		return await self.paginated_embeds(ctx, char.pages)

	@character_main.command(name='info',
						pass_context=True,
						description='Get information about one of your characters',
						brief='Get character info',
						aliases=['i'])
	async def character_info(self, ctx, name):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		char = Character.get_character(p.id, p.guild_id, name)
		if not char:
			return await ctx.send(f'You don\'t have a character with the name **{name}**')
		return await self.paginated_embeds(ctx, char.pages)

	@character_main.command(name='swap',
							pass_context=True,
							description='Swap your current character',
							brief='Swap your current character')
	async def character_swap(self, ctx, name):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		char = Character.get_character(p.id, p.guild_id, name)
		if not char:
			return await ctx.send(f'You don\'t have a character with the name **{name}**')
		p.current_character = char
		p.update()
		return await self.paginated_embeds(ctx, char.pages)

	@character_main.command(name='delete',
							pass_context=True,
							description='Delete one of your characters',
							brief='Delete a character',
							aliases=['del'])
	async def character_delete(self, ctx, name):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		char = Character.get_character(p.id, p.guild_id, name)
		if not char:
			return await ctx.send(f'You don\'t have a character with the name **{name}**')
		delete = await self.get_reply(ctx, f'Are you sure you want to delete **{char.name}**? (y/n)', bool)
		if delete:
			if char == p.current_character:
				p.current_character = ''
				p.update()
			Character.delete_character(p.id, p.guild_id, char.name)
			return await ctx.send(f'**{char.name}** has been deleted.')
		else:
			return await ctx.send(f'You will keep **{char.name}**')

	@character_main.command(name='current',
							pass_context=True,
							description='Get information about your current character',
							brief='Get current character info',
							aliases=['cur'])
	async def character_current(self, ctx):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if not p.current_character:
			return await ctx.send('You don\'t have a character set')
		return await self.paginated_embeds(ctx, p.current_character.pages)

	## Professions
	# TODO: Create profession group
	# TODO: Add info command
	@commands.command(name='viewprofessions',
					pass_context=True,
					description='View all available professions for characters',
					brief='View professions',
					aliases=['viewprofs', 'vp'])
	# TODO: Split into view_professions (default) and view_profession (info)
	async def view_professions(self, ctx, name: typing.Optional[str] = ''):
		profs = {p.name: p for p in profession.get_professions()}
		prof = profs.get(name, None)
		if not prof:
			return await self.paginated_embeds(ctx, [p.page for p in profs.values()])
		return await self.paginated_embeds(ctx, prof.page)

	## Areas
	# TODO: Create area group
	# TODO: Add info command
	# TODO: Add move command
	@commands.command(name='viewareas',
					pass_context=True,
					description='View all the areas you can travel to',
					brief='View areas',
					aliases=['va', 'areas'])
	# TODO: Split into view_areas (default) and view_area (info)
	async def view_areas(self, ctx, name: typing.Optional[str] = ''):
		areas = {a.name: a for a in area.get_areas()}
		a = areas.get(name, None)
		if not a:
			return await self.paginated_embeds(ctx, [a.page for a in areas.values()])
		return await self.paginated_embeds(ctx, a.page)

	@commands.command(name='moveareas',
					pass_context=True,
					description='Move your current character to a different area',
					brief='Move areas',
					aliases=['ma', 'move'])
	async def move_areas(self, ctx, name: typing.Optional[str] = ''):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if p.current_character is None:
			return await ctx.send('You need a character to move areas')
		ar = await self.get_or_ask_user_for_area(ctx, name)
		if not ar:
			return await ctx.send('That area does not exist')
		p.current_character.current_area = ar
		p.current_character.update()
		return await ctx.send(f'You moved to **{ar.name}**')

	## Combat
	# TODO: Create combat group
	# TODO: Add battle command
	# v4.0.0: Add boss command
	# v4.0.0: Add dungeon command
	@commands.command(name='findbattles',
					pass_context=True,
					description='Find a monster to battle in the current area',
					brief='Find a battle',
					aliases=['fbs'])
	async def find_battles(self, ctx):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if p.current_character is None:
			return await ctx.send('You need a character to battle')
		if p.current_character.current_area is None:
			return await ctx.send('You need to be in an area before you can battle')
		if p.current_character._death_timer > dt.now():
			return await ctx.send(f'**{p.current_character.name}** is dead for another **{format_remaining_time(p.current_character._death_timer)}**')
		cb = combat.Combat(p.current_character)
		msg = await ctx.send(embed=cb.embed)
		await msg.add_reaction(attack_emoji)
		if p.current_character._spells:
			await msg.add_reaction(spell1_emoji)
		await msg.add_reaction(run_emoji)
		while True:

			def is_combat_icon(m):
				return all([
					(m.emoji.name in [attack_emoji, run_emoji, 'spell1']),
					m.member.id != self.bot.user.id,
					m.message_id == msg.id,
					m.member == ctx.author
				])

			def is_spell_slot_icon(m):
				return all([
					(m.emoji.name in ['spell1', 'spell2', 'spell3', 'spell4']),
					m.member.id != self.bot.user.id,
					m.message_id == msg.id,
					m.member == ctx.author
				])

			while not cb.winner:
				try:
					react = await self.bot.wait_for('raw_reaction_add', check=is_combat_icon, timeout=600)
				except asyncio.TimeoutError:
					log.debug('Timeout, breaking')
					break
				if react.emoji.name == attack_emoji:
					await msg.remove_reaction(attack_emoji, react.member)
					cb.character_combat('Attack')
				elif react.emoji.name == 'spell1':
					await msg.clear_reactions()
					desc = f'**Current MP:** {p.current_character.current_mp}/{p.current_character.stats["INT"]}\n\n'
					for i, s in enumerate(p.current_character._spells):
						desc += f'{spell_emojis[i]} **{s.name}** (costs: {s.cost}) (DPS: {s.avg_dmg_with_character_stats(p.current_character)})\n'
						await msg.add_reaction(spell_emojis[i])
					await msg.edit(embed=Page('Which spell?', desc, colour=(150, 150, 150)).embed)
					try:
						react = await self.bot.wait_for('raw_reaction_add', check=is_spell_slot_icon, timeout=600)
					except asyncio.TimeoutError:
						log.debug('Timeout, breaking')
						await msg.clear_reactions()
						await msg.add_reaction(attack_emoji)
						await msg.add_reaction(spell1_emoji)
						await msg.add_reaction(run_emoji)
						continue
					if react.emoji.name == 'spell1':
						if p.current_character.current_mp < p.current_character._spells[0].cost:
							await msg.edit(content='You don\'t have the MP to cast this')
						else:
							cb.character_combat('Spell', 0)
					elif react.emoji.name == 'spell2':
						if p.current_character.current_mp < p.current_character._spells[1].cost:
							await msg.edit(content='You don\'t have the MP to cast this')
						else:
							cb.character_combat('Spell', 1)
					elif react.emoji.name == 'spell3':
						if p.current_character.current_mp < p.current_character._spells[2].cost:
							await msg.edit(content='You don\'t have the MP to cast this')
						else:
							cb.character_combat('Spell', 2)
					else:
						if p.current_character.current_mp < p.current_character._spells[3].cost:
							await msg.edit(content='You don\'t have the MP to cast this')
						else:
							cb.character_combat('Spell', 3)
					await msg.clear_reactions()
					await msg.add_reaction(attack_emoji)
					await msg.add_reaction(spell1_emoji)
					await msg.add_reaction(run_emoji)
				else:
					await msg.clear_reactions()
					await msg.edit(content='You run from the battle', embed=None)
					return p.current_character.update()
				await msg.edit(embed=cb.embed)

			if cb.winner == p.current_character:
				lvlup = p.current_character.add_exp(cb.exp)
				p.current_character.gold += cb.loot['gold']
				p.current_character._inventory['consumables'].extend(cb.loot['consumables'])
				p.current_character._inventory['equipment'].extend(cb.loot['equipment'])
				if lvlup:
					await ctx.send(f'You leveled up to {p.current_character.level}')
				await msg.edit(content=cb.desc)
			else:
				p.current_character._death_timer = dt.now() + td(hours=1)
				p.current_character.update()
				await msg.clear_reactions()
				return await msg.edit(content='', embed=cb.embed)
			p.current_character.update()
			cb = combat.Combat(p.current_character)
			await msg.edit(embed=cb.embed)

	## Equipment/Inventory
	# TODO: Create inventory group
	# TODO: Add equipment command
	# TODO: Add consumables command
	# TODO: Add spells command
	@commands.command(name='equipment',
					pass_context=True,
					description='View your equipment',
					brief='Equipment',
					aliases=['eq'])
	async def _equipment(self, ctx):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if p.current_character is None:
			return await ctx.send('You need a character to view an equipment')
		# Do something similar to the paginated_embeds, but with a forward, back, equip, and sell icons
		if not p.current_character._inventory['equipment']:
			return await ctx.send('You have no equipment')
		pages = [e for e in p.current_character._inventory['equipment']]
		idx = 0
		emb = pages[idx].stat_page(p.current_character).embed
		if len(pages) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
		msg = await ctx.send(embed=emb)
		await msg.add_reaction(equip_emoji)
		await msg.add_reaction(sell_emoji)
		if len(pages) > 1:
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

		def is_equipment_icon(m):
			return all([
				(m.emoji.name in [BACK, NEXT, 'equip', sell_emoji]),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		def is_main_off_hand_icon(m):
			return all([
				(m.emoji.name in [main_hand, off_hand]),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		while True:
			try:
				react = await self.bot.wait_for('raw_reaction_add', check=is_equipment_icon, timeout=60)
			except asyncio.TimeoutError:
				log.debug('Timeout, breaking')
				await msg.clear_reactions()
				break
			if react.emoji.name == NEXT:
				await msg.remove_reaction(NEXT, react.member)
				idx = (idx + 1) % len(pages)
			elif react.emoji.name == 'equip':
				await msg.remove_reaction(equip_emoji, react.member)
				unequipped = []
				eq = p.current_character._inventory['equipment'][idx]
				# If the item is armour
				if isinstance(eq, equipment.Armour):
					# If the item is in basic armour, equip it so long as the weight is for that profession
					if eq.type in equipment.basic_armour:
						unequipped.append(p.current_character.equip(eq))
					# If the item is in off hands then check to see if the weapon is two-handed
					if eq.type in equipment.off_hands:
						# If the weapon is two-handed check to see if this item ignores two-handed
						if p.current_character.weapon and p.current_character.weapon.type in equipment.two_handed_weapons:
							# If it ignores, equip it
							if eq.type in equipment.ignores_two_handed:
								unequipped.append(p.current_character.equip(eq))
							# If not send warning
							else:
								await msg.edit(content='You need to unequip you weapon to equip this')
								continue
						# If the weapon is one handed or dual-wieldable, equip
						else:
							unequipped.append(p.current_character.equip(eq))
				# If the item is a weapon
				elif isinstance(eq, equipment.Weapon):
					# If it's one handed, equip to main hand
					if eq.type not in [*equipment.dual_wield_weapons, *equipment.two_handed_weapons]:
						unequipped.append(p.current_character.equip(eq, 'main'))
					# If the item is dual-wieldable check if the current weapon is dual-wieldable
					elif eq.type in equipment.dual_wield_weapons:
						await msg.clear_reactions()
						await msg.edit(content='Main or Off-Hand?')
						await msg.add_reaction(main_hand)
						await msg.add_reaction(off_hand)
						try:
							react = await self.bot.wait_for('raw_reaction_add', check=is_main_off_hand_icon, timeout=60)
						except asyncio.TimeoutError:
							log.debug('Timeout, breaking')
							await msg.clear_reactions()
							await msg.add_reaction(equip_emoji)
							await msg.add_reaction(sell_emoji)
							await msg.add_reaction(BACK)
							await msg.add_reaction(NEXT)
							continue
						# check if current weapon is dual-wieldable
						if react.emoji.name == main_hand:
							# if it is, equip to off-hand
							unequipped.append(p.current_character.equip(eq, 'main'))
						else:
							# otherwise, unequip main hand and equip to off-hand
							if p.current_character.weapon and p.current_character.weapon.type in equipment.two_handed_weapons:
								unequipped.append(p.current_character.unequip('weapon'))
							unequipped.append(p.current_character.equip(eq, 'off'))
					# If the item is two-handed unequip the main hand
					else:
						# If the off-hand doesn't ignore two-handed weapons, unequip it
						if p.current_character.off_hand and p.current_character.off_hand.type not in equipment.ignores_two_handed:
							unequipped.append(p.current_character.unequip('offhand'))
						unequipped.append(p.current_character.equip(eq, 'main'))
				# If it's jewelry just equip it
				else:
					unequipped.append(p.current_character.equip(eq))
				# Add unequipped items back the inventory
				pages.pop(idx)
				if unequipped:
					pages = [e for e in p.current_character._inventory['equipment']]
				if len(pages) == 0:
					await msg.clear_reactions()
					return await msg.edit(content='You have no items', embed=None)
				idx = idx % len(pages)
				await msg.clear_reactions()
				await msg.add_reaction(equip_emoji)
				await msg.add_reaction(sell_emoji)
				await msg.add_reaction(BACK)
				await msg.add_reaction(NEXT)
			elif react.emoji.name == sell_emoji:
				await msg.remove_reaction(sell_emoji, react.member)
				sold = p.current_character._inventory['equipment'].pop(idx)
				equipment.delete_equipment(sold)
				pages.pop(idx)
				p.current_character.gold += sold.price
				p.current_character.update()
				if len(pages) == 0:
					await msg.clear_reactions()
					return await msg.edit(content='You have no items', embed=None)
				idx = idx % len(pages)
			else:
				await msg.remove_reaction(BACK, react.member)
				idx = (idx - 1) % len(pages)
			emb = pages[idx].stat_page(p.current_character).embed
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
			await msg.edit(content='', embed=emb)

	@commands.command(name='consumables',
					pass_context=True,
					description='View your consumables',
					brief='Consumables',
					aliases=['con'])
	async def _consumables(self, ctx):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if p.current_character is None:
			return await ctx.send('You need a character to view an consumables')
		if not p.current_character._inventory['consumables']:
			return await ctx.send('You have no consumables')
		pages = [c for c in p.current_character._inventory['consumables']]
		idx = 0
		emb = pages[idx].page.embed
		if len(pages) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
		msg = await ctx.send(embed=emb)
		await msg.add_reaction(potion_emoji)
		await msg.add_reaction(sell_emoji)
		if len(pages) > 1:
			content = ''
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

		def is_consumable_icon(m):
			return all([
				(m.emoji.name == BACK or m.emoji.name == NEXT or m.emoji.name == 'potion' or m.emoji.name == sell_emoji),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		while True:
			try:
				react = await self.bot.wait_for('raw_reaction_add', check=is_consumable_icon, timeout=60)
			except asyncio.TimeoutError:
				log.debug('Timeout, breaking')
				await msg.clear_reactions()
				break
			if react.emoji.name == NEXT:
				await msg.remove_reaction(NEXT, react.member)
				idx = (idx + 1) % len(pages)
			elif react.emoji.name == 'potion':
				await msg.remove_reaction(potion_emoji, react.member)
				consumed = p.current_character.drink(p.current_character._inventory['consumables'][idx])
				content = f'You regained {consumed.restored} {"HP" if consumed.type == "Health" else "MP"} ({p.current_character.current_con if consumed.type == "Health" else p.current_character.current_mp}/{p.current_character.stats["CON"] if consumed.type == "Health" else p.current_character.stats["INT"]})'
				pages.pop(idx)
				if len(pages) == 0:
					await msg.clear_reactions()
					return await msg.edit(content=f'{content}\nYou have no consumables', embed=None)
				idx = idx % len(pages)
			elif react.emoji.name == sell_emoji:
				await msg.remove_reaction(sell_emoji, react.member)
				sold = p.current_character._inventory['consumables'].pop(idx)
				consumable.delete_consumable(sold)
				pages.pop(idx)
				p.current_character.gold += sold.price
				p.current_character.update()
				if len(pages) == 0:
					await msg.clear_reactions()
					return await msg.edit(content='You have no consumables', embed=None)
				idx = idx % len(pages)
			else:
				await msg.remove_reaction(BACK, react.member)
				idx = (idx - 1) % len(pages)
			emb = pages[idx].page.embed
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
			await msg.edit(content=content, embed=emb)

	@commands.command(name='unequip',
					pass_context=True,
					description='Unequip an item',
					brief='Unequip items',
					aliases=['uneq'])
	async def unequip(self, ctx, slot):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if p.current_character is None:
			return await ctx.send('You need a character to view an inventory')
		if slot.lower() not in ['helmet', 'chest', 'legs', 'boots', 'gloves', 'amulet', 'ring', 'weapon', 'offhand']:
			return await ctx.send('That\'s not a slot')
		unequipped = p.current_character.unequip(slot.lower())
		if unequipped:
			return await ctx.send(f'You unequipped **{unequipped.name}**')
		else:
			return await ctx.send('You have nothing equipped in that slot.')

	## Spells
	@commands.command(name='spells',
					pass_context=True,
					description='Show the spells your character has learned',
					brief='Show learned spells',
					aliases=['sp'])
	async def spells(self, ctx):
		p = Player.get_player(ctx.author.id, ctx.author.guild.id)
		if p.current_character is None:
			return await ctx.send('You need a character to view learned spells')
		spells = [s for s in spell.get_spells_by_profession(p.current_character.profession) if s.level <= p.current_character.level]	
		if not spells:
			return await ctx.send('You haven\'t learned any spells yet')
		pages = [s.stat_page(p.current_character) for s in spells]
		idx = 0
		emb = pages[idx].embed
		if len(pages) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
		msg = await ctx.send(embed=emb)
		await msg.add_reaction(spell_equip_emoji)
		if len(pages) > 1:
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

		def is_spell_icon(m):
			return all([
				(m.emoji.name == BACK or m.emoji.name == NEXT or m.emoji.name == 'spell_equip'),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		def is_spell_slot_icon(m):
			return all([
				(m.emoji.name in ['spell1', 'spell2', 'spell3', 'spell4']),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		while True:
			try:
				react = await self.bot.wait_for('raw_reaction_add', check=is_spell_icon, timeout=60)
			except asyncio.TimeoutError:
				log.debug('Timeout, breaking')
				await msg.clear_reactions()
				break
			if react.emoji.name == NEXT:
				await msg.remove_reaction(NEXT, react.member)
				idx = (idx + 1) % len(pages)
			elif react.emoji.name == 'spell_equip':
				await msg.remove_reaction(spell_equip_emoji, react.member)
				if spells[idx] in p.current_character._spells:
					await msg.edit(content='You already have this spell equipped')
					continue
				if len(p.current_character._spells) < 4:
					p.current_character._spells.append(spells[idx])
					await msg.edit(content=f'You equipped **{spells[idx].name}**')
					p.current_character.update()
					continue
				await msg.clear_reactions()
				await msg.add_reaction(spell1_emoji)
				await msg.add_reaction(spell2_emoji)
				await msg.add_reaction(spell3_emoji)
				await msg.add_reaction(spell4_emoji)
				await msg.edit(content='Which slot?', embed=Page('Current Spells', '\n'.join([f'**{i}**: {s.name} ({s.avg_dmg})' for i, s in enumerate(p.current_character._spells, start=1)])).embed)
				try:
					react = await self.bot.wait_for('raw_reaction_add', check=is_spell_slot_icon, timeout=60)
				except asyncio.TimeoutError:
					log.debug('Timeout, breaking')
					await msg.clear_reactions()
					await msg.add_reaction(spell_equip_emoji)
					await msg.add_reaction(BACK)
					await msg.add_reaction(NEXT)
					continue
				if react.emoji.name == 'spell1':
					p.current_character._spells[0] = spells[idx]
				elif react.emoji.name == 'spell2':
					p.current_character._spells[1] = spells[idx]
				elif react.emoji.name == 'spell3':
					p.current_character._spells[2] = spells[idx]
				else:
					p.current_character._spells[3] = spells[idx]
				p.current_character.update()
				await msg.clear_reactions()
				await msg.add_reaction(spell_equip_emoji)
				await msg.add_reaction(BACK)
				await msg.add_reaction(NEXT)
				await msg.edit(content=f'You equipped **{spells[idx].name}**', embed=emb)
			else:
				await msg.remove_reaction(BACK, react.member)
				idx = (idx - 1) % len(pages)
			emb = pages[idx].embed
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
			await msg.edit(content='', embed=emb)

	# Tasks
	## Health
	@tasks.loop(seconds=600)
	async def heal_all_characters(self):
		log.info('Healing all characters')
		characters = Character.get_all_characters()
		for char in characters:
			char.heal()