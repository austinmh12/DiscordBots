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
	sql('poketcg', 'insert into version values (?)', ('1.0.0',))

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
	if version <= current:
		return
	log.debug('Migrating database')
	migration_versions = [k for k in migration_steps if k > current]
	migration_versions.sort()
	for migration_version in migration_versions:
		for step in migration_steps[migration_version]:
			sql('poketcg', step)
	update_version(version)

migration_steps = {
	'1.1.0': [
		"alter table players add column collections text default '{}'",
		"alter table players add column collections_bought integer default 0",
		"alter table players add column trainers text default '{}'",
		"alter table players add column trainers_bought integer default 0",
		"alter table players add column boosters text default '{}'",
		"alter table players add column boosters_bought integer default 0"
	],
	'1.2.0': [
		"alter table players add column daily_packs integer default 50",
		"alter table players add column quiz_questions integer default 5",
		"alter table players add column current_multiplier integer default 1",
		"alter table players add column quiz_correct integer default 0"
	],
	'1.2.2': [
		"""create table tmp_player (
			discord_id integer
			,cash integer
			,daily_reset integer
			,packs text
			,packs_opened integer
			,packs_bought integer
			,total_cash integer
			,total_cards integer
			,cards_sold integer
			,daily_packs integer
			,quiz_questions integer
			,current_multiplier integer
			,quiz_correct integer
		) """,
		"""insert into tmp_player select
			discord_id
			,cash
			,daily_reset
			,packs
			,packs_opened
			,packs_bought
			,total_cash
			,total_cards
			,cards_sold
			,daily_packs
			,quiz_questions
			,current_multiplier
			,quiz_correct
		from
			players
		""",
		'drop table players',
		"""create table players (
			discord_id integer
			,cash integer
			,daily_reset integer
			,packs text
			,packs_opened integer
			,packs_bought integer
			,total_cash integer
			,total_cards integer
			,cards_sold integer
			,daily_packs integer
			,quiz_questions integer
			,current_multiplier integer
			,quiz_correct integer
		) """,
		'insert into players select * from tmp_player',
		'drop table tmp_player'
	],
	'1.2.3': [
		'alter table players add column quiz_reset integer default 1629401801.1'
	],
	'1.3.0': [
		"alter table players add column savelist text default '[]'"
	],
	'1.4.0': [
		"alter table players add column permanent_mult integer default 0"
	]
}