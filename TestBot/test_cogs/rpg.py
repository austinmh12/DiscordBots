from . import log, BASE_PATH, Page, MyCog, chunk
from discord import File
from discord.ext import commands, tasks
import asyncio
from random import randint
import typing
import os.path

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
			,exp_to_next_level integer
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
