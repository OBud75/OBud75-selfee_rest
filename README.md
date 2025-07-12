## Local Env
python3 -m venv venv

. venv/bin/activate

pip install -r requirements.txt

echo '{"debug": true}' > .env.json


## Synch Database
./manage.py sync_types

./manage.py sync_pokemons

./manage.py sync_pokemon_types


## Launch tests
./manage.py test --keepdb
