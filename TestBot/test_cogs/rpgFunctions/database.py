from .. import sql, log

# TODO: Revert this to the base version and then add the migrations to migrate_db
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
			,weight text
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
			,death_timer integer
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
	sql('rpg', 'create table consumables (id integer, name text, type text, restored integer, stat text, bonus integer)')
	sql('rpg', '''insert into professions values
			("Warrior","STR","DEX",10,8,5,7,3,2,1,3,1,7,'Heavy')
			,("Wizard","INT","",4,5,10,5,1,1,3,1,3,0,'Light')
			,("Archer","DEX","",5,9,6,5,1,3,1,2,2,0,'Light')
			,("Rogue","DEX","",3,11,7,6,1,3,1,1,4,0,'Medium')
			,("Artificer","INT","CON",4,6,8,8,1,2,3,3,3,0,'Medium')
			,("Druid","CON","STR",8,7,5,9,3,1,1,3,1,0,'Medium')
			,("Paladin","STR","INT",9,4,8,7,3,1,3,2,1,7,'Heavy')
			'''
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
			,(11,"Tattered Cloth Pants","Trash","Legs",1,0,0,0,0,0,0,"Light",1,0,0,"",0)
			'''
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
			,('Guard','STR','',3,6,0.02,7,6,3,5,2,2,1,3,6,4)
			,('Duck','CON','',1,2,0,1,1,1,2,1,1,1,2,2,2)
			,('Chicken','CON','',1,2,0,1,1,1,3,1,1,1,2,2,2)
			,('Bat','DEX','',1,3,0.02,1,3,1,1,1,2,1,1,3,2)
			,('Snail','CON','',1,2,0,1,1,1,1,1,1,1,1,1,1)
			,('Slime','CON','',2,4,0,1,1,1,4,1,1,1,4,2,3)
			,('Scorpion','DEX','',1,4,0.02,1,3,1,1,1,2,1,1,3,1)
			,('Lizard','DEX','CON',1,3,0.02,1,3,1,2,1,2,1,2,3,3)
			,('Snake','DEX','CON',1,3,0.02,1,3,1,3,1,2,1,1,2,3)
			,('Scarab','DEX','CON',1,2,0.05,2,3,1,3,1,3,1,2,4,3)
			,('Mummy','STR','CON',3,6,0,5,2,1,5,3,2,1,3,8,5)
			,('Firebat','DEX','INT',1,3,0.02,1,5,5,3,1,2,2,2,5,4)
			,('Lava Eel','DEX','INT',1,3,0.02,2,4,6,4,1,3,3,3,5,5)
			,('Flame Spirit','INT','',5,6,0,1,5,9,4,1,2,4,2,10,8);'''
	)
	sql('rpg', '''insert into areas values
		('Sewer',1,'{"Fly":{"min_level":1,"max_level":2},"Spider":{"min_level":1,"max_level":3},"Rat":{"min_level":1,"max_level":3}}','{"gold":5,"item_chance":0.1,"max_item_count":2,"items":{"Sword":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Chest":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Boots":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Dagger":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Helmet":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Longsword":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Shortbow":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Gloves":{"rarities":["Trash","Common"],"min_level":1,"max_level":3},"Wand":{"rarities":["Trash","Common"],"min_level":1,"max_level":3}},"consumables":{"Health":{"min_level":1,"max_level":2}},"unique_items":[]}')
		,('Forest',4,'{"Mole":{"min_level":3,"max_level":8},"Spider":{"min_level":2,"max_level":6},"Rat":{"min_level":2,"max_level":6},"Skeleton":{"min_level":3,"max_level":5},"Zombie":{"min_level":2,"max_level":6},"Ghoul":{"min_level":1,"max_level":5},"Imp":{"min_level":1,"max_level":8}}','{"gold":15,"item_chance":0.15,"max_item_count":2,"items":{"Sword":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Chest":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Boots":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Dagger":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Helmet":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Longsword":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Shortbow":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Gloves":{"rarities":["Trash","Common"],"min_level":2,"max_level":6},"Wand":{"rarities":["Trash","Common"],"min_level":2,"max_level":6}},"consumables":{"Health":{"min_level":2,"max_level":4},"Mana":{"min_level":2,"max_level":4}},"unique_items":[]}')
		,('SideRoads',9,'{"Bandit":{"min_level":6,"max_level":11},"Thief":{"min_level":6,"max_level":11},"Imp":{"min_level":4,"max_level":14},"Goblin":{"min_level":5,"max_level":12},"Guard":{"min_level":7,"max_level":12}}','{"gold":40,"item_chance":0.15,"max_item_count":3,"items":{"Sword":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Chest":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Boots":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Dagger":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Helmet":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Longsword":{"rarities":["Common"],"min_level":5,"max_level":12},"Shortbow":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Gloves":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Wand":{"rarities":["Common","Uncommon"],"min_level":5,"max_level":12},"Claymore":{"rarities":["Common"],"min_level":5,"max_level":12},"Crossbow":{"rarities":["Common"],"min_level":5,"max_level":12},"Staff":{"rarities":["Common"],"min_level":5,"max_level":12},"Knife":{"rarities":["Common"],"min_level":5,"max_level":12}},"consumables":{"Health":{"min_level":3,"max_level":6},"Mana":{"min_level":3,"max_level":6}},"unique_items":[]}')
		,('Village',12,'{"Golbin":{"min_level":9,"max_level":15},"Guard":{"min_level":10,"max_level":16},"Duck":{"min_level":8,"max_level":12},"Chicken":{"min_level":13,"max_level":15},"Thief":{"min_level":9,"max_level":15}}','{"gold":100,"item_chance":0.25,"max_item_count":2,"items":{"Sword":{"rarities":["Common"],"min_level":8,"max_level":14},"Longsword":{"rarities":["Common"],"min_level":8,"max_level":14},"Claymore":{"rarities":["Common"],"min_level":8,"max_level":14},"Shortbow":{"rarities":["Common"],"min_level":8,"max_level":14},"Longbow":{"rarities":["Common"],"min_level":8,"max_level":14},"Crossbow":{"rarities":["Common"],"min_level":8,"max_level":14},"Staff":{"rarities":["Common"],"min_level":8,"max_level":14},"Wand":{"rarities":["Common"],"min_level":8,"max_level":14},"Dagger":{"rarities":["Common"],"min_level":8,"max_level":14},"Knife":{"rarities":["Common"],"min_level":8,"max_level":14},"Helmet":{"rarities":["Common"],"min_level":8,"max_level":14},"Chest":{"rarities":["Common"],"min_level":8,"max_level":14},"Legs":{"rarities":["Common"],"min_level":8,"max_level":14},"Boots":{"rarities":["Common"],"min_level":8,"max_level":14},"Gloves":{"rarities":["Common"],"min_level":8,"max_level":14},"Shield":{"rarities":["Common"],"min_level":8,"max_level":14}},"consumables":{"Health":{"min_level":8,"max_level":14},"Mana":{"min_level":8,"max_level":14}},"unique_items":[]}')
		,('Cave',16,'{"Bat":{"min_level":12,"max_level":20},"Snail":{"min_level":11,"max_level":18},"Spider":{"min_level":14,"max_level":18},"Slime":{"min_level":17,"max_level":20}}','{"gold":200,"item_chance":0.15,"max_item_count":2,"items":{"Sword":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Longsword":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Claymore":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Shortbow":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Longbow":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Crossbow":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Staff":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Wand":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Dagger":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Knife":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Helmet":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Chest":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Legs":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Boots":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Gloves":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18},"Shield":{"rarities":["Common","Uncommon"],"min_level":12,"max_level":18}},"consumables":{"Health":{"min_level":12,"max_level":18},"Mana":{"min_level":12,"max_level":18}},"unique_items":[]}')
		,('Desert',21,'{"Scorpion":{"min_level":15,"max_level":22},"Lizard":{"min_level":18,"max_level":24},"Snake":{"min_level":18,"max_level":22},"Scarab":{"min_level":16,"max_level":23},"Mummy":{"min_level":20,"max_level":25},"Skeleton":{"min_level":19,"max_level":25},"Crab":{"min_level":19,"max_level":25}}','{"gold":400,"item_chance":0.2,"max_item_count":3,"items":{"Sword":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Longsword":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Claymore":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Shortbow":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Longbow":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Crossbow":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Staff":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Wand":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Dagger":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Knife":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Helmet":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Chest":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Legs":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Boots":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Gloves":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24},"Shield":{"rarities":["Common","Uncommon"],"min_level":17,"max_level":24}},"consumables":{"Health":{"min_level":17,"max_level":24},"Mana":{"min_level":17,"max_level":24}},"unique_items":[]}')
		,('Volcano',27,'{"Slime":{"min_level":23,"max_level":29},"Firebat":{"min_level":22,"max_level":27},"Lava Eel":{"min_level":24,"max_level":30},"Flame Spirit":{"min_level":25,"max_level":31}}','{"gold":750,"item_chance":0.1,"max_item_count":1,"items":{"Sword":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Longsword":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Claymore":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Shortbow":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Longbow":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Crossbow":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Staff":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Wand":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Dagger":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Knife":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Helmet":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Chest":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Legs":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Boots":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Gloves":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30},"Shield":{"rarities":["Uncommon","Rare"],"min_level":22,"max_level":30}},"consumables":{"Health":{"min_level":22,"max_level":30},"Mana":{"min_level":22,"max_level":30}},"unique_items":[]}');'''
	)
	sql('rpg', '''create table version (
			version text
		)'''
	)
	sql('rpg', 'insert into version values (?)', ('1.0.0',))

def get_version():
	df = sql('rpg', 'select * from version')
	if df.empty:
		return ''
	return df.to_dict('records')[0]['version']

def update_version(version):
	sql('rpg', 'delete from version')
	sql('rpg', 'insert into version values (?)', (version,))

def migrate_db(version):
	current = get_version()
	log.debug(current)
	log.debug(version)
	if version <= current:
		return
	log.debug('Migrating database')
	migration_versions = [k for k in migration_steps if k > current]
	migration_versions.sort()
	for migration_version in migration_versions:
		for step in migration_steps[migration_version]:
			sql('rpg', step)
	update_version(version)

migration_steps = {
	'2.0.0': [
		"alter table characters add column inventory text default '{}'",
		"alter table characters add column current_mp integer default -1",
		"alter table characters add column spells text default '[]'",
		'create table spells (name text, profession text, level integer, min_damage integer, max_damage integer, stat text, cost integer)',
		'''insert into spells values
			('Roar','Warrior',3,5,7,'STR',2)
			,('Frenzy','Warrior',5,10,11,'STR',5)
			,('Stomp','Warrior',8,15,20,'STR',10)
			,('Cleave','Warrior',10,25,26,'STR',12)
			,('Pinpoint','Archer',2,8,9,'DEX',1)
			,('Deadeye','Archer',4,5,18,'DEX',3)
			,('Straight Shot','Archer',6,12,20,'DEX',7)
			,('Double Shot','Archer',9,30,36,'DEX',15)
			,('Firebolt','Wizard',1,2,3,'INT',2)
			,('Thunderbolt','Wizard',1,2,3,'INT',2)
			,('Icebolt','Wizard',2,3,5,'INT',3)
			,('Earthbolt','Wizard',3,5,8,'INT',5)
			,('Fire Strike','Wizard',5,8,12,'INT',8)
			,('Lightning Strike','Wizard',7,11,17,'INT',10)
			,('Ice Strike','Wizard',9,14,21,'INT',13)
			,('Earth Strike','Wizard',10,15,23,'INT',15)
			,('Sneak','Rogue',2,7,8,'DEX',3)
			,('Backstab','Rogue',5,7,12,'DEX',5)
			,('Tendon Slash','Rogue',10,25,35,'DEX',10);''',
		"""update areas set loot_table = '{"gold":1,"100%":{"drops":0,"items":[]},"main":{"drops":1,"chance":0.2,"items":[{"type":"Simple Weapon","rarities":["Trash"],"min_level":1,"max_level":1},{"type":"Basic Armour","rarities":["Trash"],"min_level":1,"max_level":1},{"type":"Health","rarities":[],"min_level":1,"max_level":2}]},"secondary":{"drops":0,"chance":0,"items":[]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Fly":{"min_level":1,"max_level":1},"Spider":{"min_level":1,"max_level":1},"Rat":{"min_level":1,"max_level":1},"Slime":{"min_level":1,"max_level":1}}' where name = 'Sewer'""",
		"""update areas set loot_table = '{"gold":15,"100%":{"drops":0,"items":[]},"main":{"drops":2,"chance":0.15,"items":[{"type":"Simple Weapon","rarities":["Trash","Common"],"min_level":3,"max_level":6},{"type":"Basic Armour","rarities":["Trash","Common"],"min_level":3,"max_level":6},{"type":"Restoration","rarities":[],"min_level":3,"max_level":6}]},"secondary":{"drops":1,"chance":0.075,"items":[{"type":"Advanced Weapon","rarities":["Common"],"min_level":5,"max_level":8},{"type":"Advanced Weapon","rarities":["Trash"],"min_level":3,"max_level":6},{"type":"Jewelry","rarities":["Common"],"min_level":5,"max_level":8},{"type":"Restoration","rarities":[],"min_level":5,"max_level":8},{"type":"Off Hand","rarities":["Common"],"min_level":5,"max_level":8}]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Mole":{"min_level":3,"max_level":8},"Spider":{"min_level":2,"max_level":6},"Rat":{"min_level":2,"max_level":6},"Skeleton":{"min_level":3,"max_level":5},"Zombie":{"min_level":2,"max_level":6},"Ghoul":{"min_level":1,"max_level":5},"Imp":{"min_level":1,"max_level":8}}', where name = 'Forest'""",
		"""update areas set loot_table = '{"gold":40,"100%":{"drops":0,"items":[]},"main":{"drops":2,"chance":0.15,"items":[{"type":"Simple Weapon","rarities":["Common"],"min_level":6,"max_level":10},{"type":"Advanced Weapon","rarities":["Common"],"min_level":6,"max_level":10},{"type":"All Armour","rarities":["Common"],"min_level":6,"max_level":10},{"type":"Restoration","rarities":[],"min_level":6,"max_level":10},{"type":"Jewelry","rarities":["Common"],"min_level":6,"max_level":10}]},"secondary":{"drops":1,"chance":0.075,"items":[{"type":"Simple Weapon","rarities":["Uncommon"],"min_level":8,"max_level":12},{"type":"All Armour","rarities":["Uncommon"],"min_level":8,"max_level":12},{"type":"Advanced Weapon","rarities":["Uncommon"],"min_level":8,"max_level":12},{"type":"Restoration","rarities":[],"min_level":8,"max_level":12},{"type":"Jewelry","rarities":["Uncommon"],"min_level":8,"max_level":12}]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Bandit":{"min_level":6,"max_level":11},"Thief":{"min_level":6,"max_level":11},"Imp":{"min_level":4,"max_level":14},"Goblin":{"min_level":5,"max_level":12},"Guard":{"min_level":7,"max_level":12}}' where name = 'SideRoads'""",
		"""update areas set loot_table = '{"gold":100,"100%":{"drops":0,"items":[]},"main":{"drops":1,"chance":0.2,"items":[{"type":"Simple Weapon","rarities":["Common","Uncommon"],"min_level":9,"max_level":15},{"type":"All Armour","rarities":["Common","Uncommon"],"min_level":9,"max_level":15},{"type":"Advanced Weapon","rarities":["Common","Uncommon"],"min_level":9,"max_level":15},{"type":"Restoration","rarities":[],"min_level":9,"max_level":15},{"type":"Jewelry","rarities":["Common","Uncommon"],"min_level":9,"max_level":15}]},"secondary":{"drops":1,"chance":0.05,"items":[{"type":"Complex Weapon","rarities":["Uncommon"],"min_level":12,"max_level":17},{"type":"Off Hand","rarities":["Uncommon"],"min_level":12,"max_level":17},{"type":"Jewelry","rarities":["Uncommon"],"min_level":12,"max_level":17}]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Goblin":{"min_level":9,"max_level":15},"Guard":{"min_level":10,"max_level":16},"Duck":{"min_level":8,"max_level":12},"Chicken":{"min_level":13,"max_level":15},"Thief":{"min_level":9,"max_level":15}}' where name = 'Village'""",
		"""update areas set loot_table = '{"gold":200,"100%":{"drops":1,"items":[{"type":"Restoration","rarities":[],"min_level":14,"max_level":20}]},"main":{"drops":2,"chance":0.15,"items":[{"type":"Simple Weapon","rarities":["Common","Uncommon"],"min_level":14,"max_level":20},{"type":"All Armour","rarities":["Common","Uncommon"],"min_level":14,"max_level":20},{"type":"Advanced Weapon","rarities":["Common","Uncommon"],"min_level":14,"max_level":20},{"type":"Restoration","rarities":[],"min_level":16,"max_level":21},{"type":"Jewelry","rarities":["Common","Uncommon"],"min_level":14,"max_level":20}]},"secondary":{"drops":1,"chance":0.05,"items":[{"type":"Complex Weapon","rarities":["Uncommon"],"min_level":17,"max_level":23},{"type":"Off Hand","rarities":["Uncommon","Rare"],"min_level":17,"max_level":23},{"type":"Jewelry","rarities":["Rare"],"min_level":17,"max_level":23}]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Bat":{"min_level":12,"max_level":20},"Snail":{"min_level":11,"max_level":18},"Spider":{"min_level":14,"max_level":18}}' where name = 'Cave'""",
		"""update areas set loot_table = '{"gold":500,"100%":{"drops":1,"items":[{"type":"Restoration","rarities":[],"min_level":18,"max_level":25}]},"main":{"drops":3,"chance":0.15,"items":[{"type":"All Weapons","rarities":["Uncommon"],"min_level":18,"max_level":25},{"type":"All Armour","rarities":["Uncommon"],"min_level":18,"max_level":25},{"type":"Jewelry","rarities":["Uncommon"],"min_level":18,"max_level":25}]},"secondary":{"drops":1,"chance":0.05,"items":[{"type":"All Weapons","rarities":["Rare"],"min_level":20,"max_level":27},{"type":"Off Hand","rarities":["Uncommon","Rare"],"min_level":20,"max_level":27},{"type":"Jewelry","rarities":["Rare"],"min_level":20,"max_level":27}]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Scorpion":{"min_level":15,"max_level":22},"Lizard":{"min_level":18,"max_level":24},"Snake":{"min_level":18,"max_level":22},"Scarab":{"min_level":16,"max_level":23},"Mummy":{"min_level":20,"max_level":25},"Skeleton":{"min_level":19,"max_level":25},"Crab":{"min_level":19,"max_level":25}}' where name = 'Desert'""",
		"""update areas set loot_table = '{"gold":850,"100%":{"drops":1,"items":[{"type":"Restoration","rarities":[],"min_level":25,"max_level":31}]},"main":{"drops":2,"chance":0.10,"items":[{"type":"All Weapons","rarities":["Uncommon","Rare"],"min_level":25,"max_level":31},{"type":"All Armour","rarities":["Uncommon","Rare"],"min_level":25,"max_level":31},{"type":"Jewelry","rarities":["Uncommon","Rare"],"min_level":25,"max_level":31}]},"secondary":{"drops":1,"chance":0.05,"items":[{"type":"Simple Weapon","rarities":["Legendary"],"min_level":29,"max_level":34},{"type":"All Armour","rarities":["Rare"],"min_level":29,"max_level":34},{"type":"Jewelry","rarities":["Rare","Legendary"],"min_level":29,"max_level":34}]},"rare":{"drops":0,"chance":0,"items":[]}}', monsters = '{"Firebat":{"min_level":22,"max_level":27},"Lava Eel":{"min_level":24,"max_level":30},"Flame Spirit":{"min_level":25,"max_level":31}}' where name = 'Volcano'""",
		"""insert into areas values ('Farm', 2, '{"Chicken":{"min_level":1,"max_level":4},"Duck":{"min_level":2,"max_level":4},"Rat":{"min_level":1,"max_level":4}}', '{"gold":5,"100%":{"drops":0,"items":[]},"main":{"drops":1,"chance":0.2,"items":[{"type":"Simple Weapon","rarities":["Trash"],"min_level":2,"max_level":4},{"type":"Basic Armour","rarities":["Trash"],"min_level":2,"max_level":4},{"type":"Restoration","rarities":[],"min_level":2,"max_level":3}]},"secondary":{"drops":1,"chance":0.05,"items":[{"type":"Simple Weapon","rarities":["Trash","Common"],"min_level":3,"max_level":4},{"type":"Basic Armour","rarities":["Trash","Common"],"min_level":3,"max_level":4},{"type":"Restoration","rarities":[],"min_level":3,"max_level":4},{"type":"Off Hand","rarities":["Common"],"min_level":3,"max_level":4}]},"rare":{"drops":0,"chance":0,"items":[]}}')""",
	] # Add the new area loot format
}