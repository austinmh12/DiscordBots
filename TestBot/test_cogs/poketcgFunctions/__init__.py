import requests as r

# Constants
with open('../.env') as f:
	ENV = {l.strip().split('=')[0]: l.strip().split('=')[1] for l in f.readlines()}

# Functions
def api_call(endpoint, params={}):
	return r.get(
		f'https://api.pokemontcg.io/v2/{endpoint}',
		headers={'X-Api-Key': ENV.get('POKETCGAPIKEY')},
		params=params
	).json()



