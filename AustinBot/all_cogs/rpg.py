from . import log, BASE_PATH, Page, MyCog, chunk, sql, format_remaining_time, BACK, NEXT
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint
import typing
import os.path
from datetime import datetime as dt, timedelta as td

from .rpgFunctions import character
from .rpgFunctions import profession
from .rpgFunctions import player
from .rpgFunctions import equipment
from .rpgFunctions import area
from .rpgFunctions import combat

# Version
version = '1.0.0'

# Constants
attack_emoji = '\u2694\ufe0f'
run_emoji = '\U0001f45f'
equip_emoji = '\u2705'
sell_emoji = '\U0001fa99'

# Functions
def initialise_db():
	sql('rpg', 'create table players (id integer, guild_id integer, current_character text)')
	sql('rpg', '''create table professions (
			name text
			,primary_stat text
			,secondary_stat text
			,base_str integer
			,base_dex integer
			,base_int integer
			,base_con integer
			,str_mod integer
			,dex_mod integer
			,int_mod integer
			,con_mod integer
			,starting_weapon integer
			,starting_off_hand integer
		)'''
	)
	sql('rpg', '''create table characters (
			player_id integer
			,player_guild_id integer
			,name text
			,profession text
			,level integer
			,exp integer
			,gold integer
			,helmet integer
			,chest integer
			,legs integer
			,boots integer
			,gloves integer
			,amulet integer
			,ring integer
			,weapon integer
			,off_hand integer
			,current_con integer
			,current_area text
			,death_timer text
			,inventory text
		)'''
	)
	sql('rpg', '''create table monsters (
			name text
			,primary_stat text
			,secondary_stat text
			,min_damage integer
			,max_damage integer
			,crit_chance integer
			,base_str integer
			,base_dex integer
			,base_int integer
			,base_con integer
			,str_mod integer
			,dex_mod integer
			,int_mod integer
			,con_mod integer
			,base_exp integer
			,exp_mod integer
		)'''
	)
	sql('rpg', '''create table equipment (
			id integer
			,name text
			,rarity text
			,type text
			,level integer
			,str_bonus integer
			,dex_bonus integer
			,int_bonus integer
			,con_bonus integer
			,def_bonus integer
			,atk_bonus integer
			,weight text
			,defense integer
			,min_damage integer
			,max_damage integer
			,stat text
			,crit_chance integer
		)'''
	)
	sql('rpg', 'create table areas (name text, recommended_level integer, monsters text, loot_table text)')
	sql('rpg', '''insert into professions values
			("Warrior","STR","DEX",10,8,5,7,3,2,1,3,1,7)
			,("Wizard","INT","",4,5,10,5,1,1,3,1,3,0)
			,("Archer","DEX","",5,9,6,5,1,3,1,2,2,0)
			,("Rogue","DEX","",3,11,7,6,1,3,1,1,4,0)'''
	)
	sql('rpg', '''insert into equipment values
			(1,"Starter Sword","Trash","Sword",1,0,0,0,0,0,0,"",0,1,3,"STR",0.05)
			,(2,"Starter Shortbow","Trash","Shortbow",1,0,0,0,0,0,0,"",0,1,3,"DEX",0.05)
			,(3,"Starter Wand","Trash","Wand",1,0,0,0,0,0,0,"",0,1,3,"INT",0.05)
			,(4,"Starter Dagger","Trash","Dagger",1,0,0,0,0,0,0,"",0,1,3,"DEX",0.1)
			,(5,"Dented Platmail","Trash","Chest",1,0,0,0,0,0,0,"Heavy",3,0,0,"",0)
			,(6,"Dented Platelegs","Trash","Legs",1,0,0,0,0,0,0,"Heavy",3,0,0,"",0)
			,(7,"Cracked Kite Shield","Trash","Shield",1,0,0,0,0,0,0,"Heavy",3,0,0,"",0)
			,(8,"Ripped Leather Vest","Trash","Chest",1,0,0,0,0,0,0,"Medium",2,0,0,"",0)
			,(9,"Ripped Leather Pants","Trash","Legs",1,0,0,0,0,0,0,"Medium",2,0,0,"",0)
			,(10,"Tattered Cloth Shirt","Trash","Chest",1,0,0,0,0,0,0,"Light",1,0,0,"",0)
			,(11,"Tattered Cloth Pants","Trash","Legs",1,0,0,0,0,0,0,"Light",1,0,0,"",0)'''
	)
	sql('rpg', '''insert into monsters values
			('Goblin','STR','',1,3,0.02,1,1,1,1,1,1,1,1,2,2)
			,('Rat','DEX','',1,2,0.05,1,2,1,1,1,1,1,1,1,2)
			,('Spider','DEX','',1,3,0.01,1,1,1,1,1,2,1,1,2,1)
			,('Crab','CON','',1,2,0,1,1,1,3,1,1,1,2,1,1)
			,('Mole','CON','',2,3,0,1,1,1,3,1,1,1,2,2,2)
			,('Wisp','INT','',2,3,0,1,1,2,1,1,1,2,2,2,2)
			,('Ghost','INT','',1,3,0,1,1,1,1,1,1,3,2,2,3)
			,('Fly','DEX','',1,2,0,1,1,1,1,1,1,1,1,1,1)
			,('Skeleton','STR','',2,4,0,3,2,1,1,2,2,1,1,3,2)
			,('Zombie','STR','',1,4,0,3,3,1,3,2,2,1,2,3,3)
			,('Ghoul','STR','',2,3,0,2,1,1,4,3,2,1,3,3,2)
			,('Bandit','DEX','',2,4,0.1,2,5,2,3,1,1,1,3,4,2)
			,('Thief','DEX','',3,4,0.1,4,4,2,4,2,2,1,2,7,3)
			,('Imp','DEX','INT',1,5,0.05,1,8,4,1,1,2,2,1,4,2)
			,('Guard','STR','',3,6,0.02,7,6,3,5,2,2,1,3,6,4)'''
	)
	sql('rpg', '''insert into areas values
		('Sewer',2,'{"Fly":{"min_level":1,"max_level":2},"Spider":{"min_level":1,"max_level":3},"Rat":{"min_level":1,"max_level":3}}','{"gold":5,"item_chance":0.1,"max_item_count":2,"items":{"Sword":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Chest":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Boots":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Dagger":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Helmet":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Longsword":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Shortbow":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Gloves":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Wand":{"rarities":["Trash","Common"],"min_level":1,"max_level":3}},"unique_items":[]}')
		,('Forest',4,'{"Mole":{"min_level":3,"max_level":8},"Spider":{"min_level":2,"max_level":6},"Rat":{"min_level":2,"max_level":6},"Skeleton":{"min_level":3,"max_level":5},"Zombie":{"min_level":2,"max_level":6},"Ghoul":{"min_level":1,"max_level":5},"Imp":{"min_level":1,"max_level":8}}','{"gold":15,"item_chance":0.15,"max_item_count":2,"items":{"Sword":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Chest":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Boots":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Dagger":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Helmet":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Longsword":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Shortbow":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Gloves":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Wand":{"rarities":["Trash","Common"],"min_level":2,"max_level":6}},"unique_items":[]}')
		,('SideRoads',9,'{"Bandit":{"min_level":6,"max_level":11},"Thief":{"min_level":6,"max_level":11},"Imp":{"min_level":4,"max_level":14},"Goblin":{"min_level":5,"max_level":12},"Guard":{"min_level":7,"max_level":12}}','{"gold":40,"item_chance":0.15,"max_item_count":3,"items":{"Sword":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Chest":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Boots":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Dagger":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Helmet":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Longsword":{"rarities":["Common"],"min_level":5,"max_level":12},"Shortbow":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Gloves":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Wand":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Claymore":{"rarities":["Common"],"min_level":5,"max_level":12},"Crossbow":{"rarities":["Common"],"min_level":5,"max_level":12},"Staff":{"rarities":["Common"],"min_level":5,"max_level":12},"Knife":{"rarities":["Common"],"min_level":5,"max_level":12}},"unique_items":[]}')'''
	)

# Classes
class RPGCog(MyCog):
	def __init__(self, bot):
		super().__init__(bot)
		if not os.path.exists(f'{BASE_PATH}/rpg.db'):
			log.info('Initialising database.')
			initialise_db()
		self.heal_all_characters.start()

	# Utilities
	def get_or_add_player_from_ctx(self, ctx):
		id = ctx.author.id
		guild_id = ctx.author.guild.id
		p = player.get_player(id, guild_id)
		if not p:
			return player.add_player(id, guild_id)
		return p

	async def get_or_ask_user_for_character(self, ctx, player, name):

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
		
		if not name:
			await ctx.send('Which character?')
			await self.me(ctx)
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('You ran out of time.')
			name = reply.content
		return character.get_character(player, name)

	async def get_or_ask_user_for_area(self, ctx, name):

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
		
		if not name:
			await ctx.send('Which area?')
			areas = area.get_areas()
			p = Page('Areas', '\n'.join([f'**{a.name}** - Rec. Lvl: {a.recommended_level}' for a in areas]), colour=(150, 150, 150))
			await ctx.send(embed=p.embed)
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('You ran out of time.')
			name = reply.content
		return area.get_area(name)

	# Listeners

	# Commands
	## Characters
	@commands.command(name='createcharacter',
					pass_context=True,
					description='Create a character to start your journey',
					brief='Create a character',
					aliases=['cc', 'create'])
	async def create_character(self, ctx, name: typing.Optional[str] = '', prof: typing.Optional[str] = ''):
		p = self.get_or_add_player_from_ctx(ctx)
		marked_for_deletion = False
		if len(character.get_characters(p)) >= 3:
			return await ctx.send('You can only have 3 characters')

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

		if not name:
			await ctx.send('What is your character\'s name?')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('You ran out of time.')
			name = reply.content
		existing_char = character.get_character(p, name)
		if existing_char:
			await ctx.send(f'You have a character named {existing_char.name}, do you want to overwrite them? (y/n)')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('You ran out of time.')
			if reply.content.lower() == 'y':
				marked_for_deletion = True
			else:
				return await ctx.send(f'You will keep {existing_char.name}')
		while prof.lower() not in profession.all_professions:
			await ctx.send('What is your desired profession?')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('You ran out of time.')
			prof = reply.content
		prof = profession.get_profession(prof)
		if prof.name in profession.light_professions:
			starting_chest = equipment.get_equipment(10)
			starting_legs = equipment.get_equipment(11)
		elif prof.name in profession.medium_professions:
			starting_chest = equipment.get_equipment(8)
			starting_legs = equipment.get_equipment(9)
		else:
			starting_chest = equipment.get_equipment(5)
			starting_legs = equipment.get_equipment(6)
		char = character.Character(
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
			character.delete_character(p, existing_char.name)
		character.add_character(char)
		p.current_character = char
		p.update()
		return await self.paginated_embeds(ctx, char.pages)

	@commands.command(name='me',
					pass_context=True,
					description='Shows your characters',
					brief='Shows your characters')
	async def me(self, ctx):
		p = self.get_or_add_player_from_ctx(ctx)
		chars = character.get_characters(p)
		desc = f'**Current Character:** {p.current_character.name if p.current_character else ""}\n\n'
		desc += '__All characters__\n'
		desc += '\n'.join([f'**{c.name}** ({c.profession.name}) --- _{c.level}_' for c in chars])
		page = Page(ctx.author.display_name, desc, colour=(150, 150, 150), icon=ctx.author.avatar_url)
		return await self.paginated_embeds(ctx, page)

	@commands.command(name='swapcharacter',
					pass_context=True,
					description='Swap your current character',
					brief='Swap your current character',
					aliases=['swap'])
	async def swap_character(self, ctx, name: typing.Optional[str] = ''):
		p = self.get_or_add_player_from_ctx(ctx)
		char = await self.get_or_ask_user_for_character(ctx, p, name)
		if not char:
			return await ctx.send(f'You don\'t have a character with the name {name}')
		p.current_character = char
		p.update()
		return await self.paginated_embeds(ctx, char.pages)

	@commands.command(name='deletecharacter',
					pass_context=True,
					description='Delete one of your characters',
					brief='Delete a character',
					aliases=['delchar', 'dc'])
	async def delete_character(self, ctx, name: typing.Optional[str] = ''):
		p = self.get_or_add_player_from_ctx(ctx)

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

		char = await self.get_or_ask_user_for_character(ctx, p, name)
		if not char:
			return await ctx.send(f'You don\'t have a character with the name {name}')
		await ctx.send(f'Are you sure you want to delete {char.name}? (y/n)')
		try:
			reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('You ran out of time.')
		if reply.content.lower() == 'y':
			if char == p.current_character:
				p.current_character = ''
				p.update()
			character.delete_character(p, char.name)
			return await ctx.send(f'{char.name} has been deleted.')
		else:
			return await ctx.send(f'You will keep {existing_char.name}')

	@commands.command(name='getcharacter',
					pass_context=True,
					description='Get information about one of your characters',
					brief='Get character info',
					aliases=['getchar', 'gc'])
	async def get_character(self, ctx, name: typing.Optional[str] = ''):
		p = self.get_or_add_player_from_ctx(ctx)
		char = await self.get_or_ask_user_for_character(ctx, p, name)
		if not char:
			return await ctx.send(f'You don\'t have a character with the name {name}')
		return await self.paginated_embeds(ctx, char.pages)

	@commands.command(name='currentcharacter',
					pass_context=True,
					description='Get information about your current character',
					brief='Get current character info',
					aliases=['curchar', 'cur'])
	async def current_character(self, ctx):
		p = self.get_or_add_player_from_ctx(ctx)
		if not p.current_character:
			return await ctx.send('You don\'t have a character set')
		return await self.paginated_embeds(ctx, p.current_character.pages)

	## Professions
	@commands.command(name='viewprofessions',
					pass_context=True,
					description='View all available professions for characters',
					brief='View professions',
					aliases=['viewprofs', 'vp'])
	async def view_professions(self, ctx, name: typing.Optional[str] = ''):
		profs = {p.name: p for p in profession.get_professions()}
		prof = profs.get(name, None)
		if not prof:
			return await self.paginated_embeds(ctx, [p.page for p in profs.values()])
		return await self.paginated_embeds(ctx, prof.page)

	## Areas
	@commands.command(name='viewareas',
					pass_context=True,
					description='View all the areas you can travel to',
					brief='View areas',
					aliases=['va', 'areas'])
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
		p = self.get_or_add_player_from_ctx(ctx)
		if p.current_character is None:
			return await ctx.send('You need a character to move areas')
		ar = await self.get_or_ask_user_for_area(ctx, name)
		if not ar:
			return await ctx.send('That area does not exist')
		p.current_character.current_area = ar
		p.current_character.update()
		return await ctx.send(f'You moved to **{ar.name}**')

	## Combat
	@commands.command(name='findbattle',
					pass_context=True,
					description='Find a monster to battle in the current area',
					brief='Find a battle',
					aliases=['fb'])
	async def find_battle(self, ctx):
		p = self.get_or_add_player_from_ctx(ctx)
		if p.current_character is None:
			return await ctx.send('You need a character to battle')
		if p.current_character.current_area is None:
			return await ctx.send('You need to be in an area before you can battle')
		if p.current_character._death_timer > dt.now():
			return await ctx.send(f'**{p.current_character.name}** is dead for another **{format_remaining_time(p.current_character._death_timer)}**')
		cb = combat.Combat(p.current_character)
		msg = await ctx.send(embed=cb.embed)
		await msg.add_reaction(attack_emoji)
		await msg.add_reaction(run_emoji)

		def is_combat_icon(m):
			return all([
				(m.emoji.name == attack_emoji or m.emoji.name == run_emoji),
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
			else:
				await msg.remove_reaction(run_emoji, react.member)
				await msg.remove_reaction(attack_emoji, self.bot.user)
				await msg.remove_reaction(run_emoji, self.bot.user)
				await msg.edit(content='You run from the battle', embed=None)
				return p.current_character.update()
			await msg.edit(embed=cb.embed)

		await msg.remove_reaction(attack_emoji, self.bot.user)
		await msg.remove_reaction(run_emoji, self.bot.user)
		if cb.winner == p.current_character:
			lvlup = p.current_character.add_exp(cb.exp)
			p.current_character.gold += cb.loot['gold']
			p.current_character._inventory.extend(cb.loot['items'])
			if lvlup:
				await ctx.send(f'You leveled up to {p.current_character.level}')
		else:
			p.current_character._death_timer = dt.now() + td(hours=1)
		return p.current_character.update()

	## Equipment/Inventory
	@commands.command(name='inventory',
					pass_context=True,
					description='View your inventory',
					brief='Inventory',
					aliases=['inv'])
	async def inventory(self, ctx):
		p = self.get_or_add_player_from_ctx(ctx)
		if p.current_character is None:
			return await ctx.send('You need a character to view an inventory')
		# Do something similar to the paginated_embeds, but with a forward, back, equip, and sell icons
		if not p.current_character._inventory:
			return await ctx.send('You have no items')
		pages = [e.stat_page(p.current_character) for e in p.current_character._inventory]
		idx = 0
		emb = pages[idx].embed
		if len(pages) > 1:
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
		msg = await ctx.send(embed=emb)
		await msg.add_reaction(equip_emoji)
		await msg.add_reaction(sell_emoji)
		if len(pages) > 1:
			await msg.add_reaction(BACK)
			await msg.add_reaction(NEXT)

		def is_inventory_icon(m):
			return all([
				(m.emoji.name == BACK or m.emoji.name == NEXT or m.emoji.name == equip_emoji or m.emoji.name == sell_emoji),
				m.member.id != self.bot.user.id,
				m.message_id == msg.id,
				m.member == ctx.author
			])

		while True:
			try:
				react = await self.bot.wait_for('raw_reaction_add', check=is_inventory_icon, timeout=60)
			except asyncio.TimeoutError:
				log.debug('Timeout, breaking')
				break
			if react.emoji.name == NEXT:
				idx = (idx + 1) % len(pages)
				await msg.remove_reaction(NEXT, react.member)
			elif react.emoji.name == equip_emoji:
				unequipped = p.current_character.equip(p.current_character._inventory[idx])
				p.current_character._inventory.pop(idx)
				pages.pop(idx)
				if unequipped:
					p.current_character._inventory.append(unequipped)
					pages = [e.stat_page(p.current_character) for e in p.current_character._inventory]
				else:
					if len(pages) == 0:
						return await msg.edit(content='You have no items', embed=None)
				idx = idx % len(pages)
				await msg.remove_reaction(equip_emoji, react.member)
			elif react.emoji.name == sell_emoji:
				sold = p.current_character._inventory.pop(idx)
				equipment.delete_equipment(sold)
				pages.pop(idx)
				p.current_character.gold += sold.price
				p.current_character.update()
				if len(pages) == 0:
					return await msg.edit(content='You have no items', embed=None)
				idx = idx % len(pages)
				await msg.remove_reaction(sell_emoji, react.member)
			else:
				idx = (idx - 1) % len(pages)
				await msg.remove_reaction(BACK, react.member)
			emb = pages[idx].embed
			emb.set_footer(text=f'{idx + 1}/{len(pages)}')
			await msg.edit(embed=emb)

	@commands.command(name='unequip',
					pass_context=True,
					description='Unequip an item',
					brief='Unequip items',
					aliases=['uneq'])
	async def unequip(self, ctx, slot):
		p = self.get_or_add_player_from_ctx(ctx)
		if p.current_character is None:
			return await ctx.send('You need a character to view an inventory')
		if slot.lower() not in ['helmet', 'chest', 'legs', 'boots', 'gloves', 'amulet', 'ring', 'weapon', 'offhand']:
			return await ctx.send('That\'s not a slot')
		unequipped = p.current_character.unequip(slot.lower())
		if unequipped:
			p.current_character._inventory.append(unequipped)
			return await ctx.send(f'You unequipped **{unequipped.name}**')
		else:
			return await ctx.send('You have nothing equipped in that slot.')

	# Tasks
	## Health
	@tasks.loop(seconds=600)
	async def heal_all_characters(self):
		log.info('Healing all characters')
		characters = character.get_all_characters()
		for char in characters:
			char.heal()