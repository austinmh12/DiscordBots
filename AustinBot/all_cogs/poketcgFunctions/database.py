from .. import sql

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

def migrate_db():
	...

migration_steps = {}