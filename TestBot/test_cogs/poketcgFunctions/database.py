from .. import sql, log

def initialise_db():
	sql('poketcg', '''create table players (
			discord_id integer
			,cash integer
			,daily_reset integer
			,packs text
			,packs_opened integer
			,packs_bought integer
			,total_cash integer
			,total_cards integer
			,cards_sold integer
		)'''
	)
	sql('poketcg', '''create table packs (
			discord_id integer
			,set_id text
			,amount integer
		)'''
	)
	sql('poketcg', '''create table cards (
			discord_id integer
			,card_id text
			,amount integer
		)'''
	)
	sql('poketcg', '''create table version (
			version text
		)'''
	)

def get_version():
	df = sql('poketcg', 'select * from version')
	if df.empty:
		return ''
	return df.to_dict('records')[0]['version']

def update_version(version):
	sql('poketcg', 'delete from version')
	sql('poketcg', 'insert into version values (?)', (version,))

def migrate_db(version):
	current = get_version()
	log.debug(current)
	log.debug(version)
	if version != get_version():
		log.info('Migrating database')
		for step in migration_steps:
			sql('poketcg', step)
		update_version(version)

migration_steps = []

# migration_steps = [
# 	"alter table players add column collections text default '{}'",
# 	"alter table players add column collections_bought integer default 0",
# 	"alter table players add column trainers text default '{}'",
# 	"alter table players add column trainers_bought integer default 0",
# 	"alter table players add column boosters text default '{}'",
# 	"alter table players add column boosters_bought integer default 0"
# ]