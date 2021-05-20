from . import log, BASE_PATH, Page, MyCog, chunk
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint
import typing
import os.path

from rpgFunction import character
from rpgFunction import profession
from rpgFunction import player
from rpgFunction import equipment

# Version
version = '0.0.0'

# Constants

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
			,ring1 integer
			,ring2 integer
			,weapon integer
			,off_hand integer
			,current_con integer
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
			,loot_table text
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
	sql('rpg', 'create table areas (name text, recommended_level integer, monsters text)')
	sql('rpg', '''insert into professions values
			("Warrior","STR","DEX",10,8,5,7,3,2,1,3,1,7)
			,("Wizard","INT","",4,5,10,5,1,1,3,1,3,0)
			,("Archer","DEX","",5,9,6,5,1,3,1,2,2,0)
			,("Rogue","DEX","",3,11,7,6,1,3,1,1,4,0)'''
	)
	sql('rpg', '''insert into equipment values
			(1,"Starter Sword","Common","Sword",1,0,0,0,0,0,0,"",0,1,3,"STR",0.05)
			,(2,"Starter Shortbow","Common","Shortbow",1,0,0,0,0,0,0,"",0,1,3,"DEX",0.05)
			,(3,"Starter Wand","Common","Wand",1,0,0,0,0,0,0,"",0,1,3,"INT",0.05)
			,(4,"Starter Dagger","Common","Dagger",1,0,0,0,0,0,0,"",0,1,3,"DEX",0.1)
			,(5,"Dented Platmail","Common","Chest",1,0,0,0,0,0,0,"Heavy",3,0,0,"",0)
			,(6,"Dented Platelegs","Common","Legs",1,0,0,0,0,0,0,"Heavy",3,0,0,"",0)
			,(7,"Cracked Kite Shield","Common","Shield",1,0,0,0,0,0,0,"Heavy",3,0,0,"",0)
			,(8,"Ripped Leather Vest","Common","Chest",1,0,0,0,0,0,0,"Medium",2,0,0,"",0)
			,(9,"Ripped Leather Pants","Common","Legs",1,0,0,0,0,0,0,"Medium",2,0,0,"",0)
			,(10,"Tattered Cloth Shirt","Common","Chest",1,0,0,0,0,0,0,"Light",1,0,0,"",0)
			,(11,"Tattered Cloth Pants","Common","Legs",1,0,0,0,0,0,0,"Light",1,0,0,"",0)'''
	)

# Classes
class RPGCog(MyCog):
	def __init__(self, bot):
		super().__init__(bot)
		if not os.path.exists(f'{BASE_PATH}/rpg.db'):
			log.info('Initialising database.')
			initialise_db()

	# Utilities
	def get_or_add_player_from_ctx(self, ctx):
		id = ctx.author.id
		guild_id = ctx.author.guild.id
		player = player.get_player(id, guild_id)
		if not player:
			return player.add_player(id, guild_id)
		return player

	# Listeners

	# Commands
	@commands.command(name='createcharacter',
					pass_context=True,
					description='Create a character to start your journey',
					brief='Create a character',
					aliases=['cc', 'create'])
	async def create_character(self, ctx, name: typing.Optional[str] = '', prof: typing.Optional[str] = ''):
		p = self.get_or_add_player_from_ctx(ctx)

		def is_same_user_channel(msg):
			return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id

		if not name:
			await ctx.send('What is your character\'s name?')
			try:
				reply = await self.bot.wait_for('message', check=is_same_user_channel, timeout=30)
			except asyncio.TimeoutError:
				return await ctx.send('You ran out of time.')
			name = reply.content
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
			None, # ring1
			None, # ring2
			prof.starting_weapon,
			prof.starting_off_hand
		)
		character.add_character(char)
		p.current_character = char
		p.update()
		return await self.paginated_embeds(ctx, char.pages)

	# Tasks
