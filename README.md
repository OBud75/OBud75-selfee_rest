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

### Mise en contexte et explications  

#### Registration  
Sous-classer la classe `User` de Django est une bonne pratique en début de projet, même si cette sous-classe est identique au modèle natif.  
Dans les settings, on définit `AUTH_USER_MODEL = "registration.User"`.  
Cela permet d’anticiper toute modification future sans complexifier les migrations.  

Le package s’appelle **registration** pour rester cohérent avec la structure Django :  
les templates de login, logout, reset_password, etc. se trouvent dans  
`contrib/admin/templates/registration` et `contrib/auth/templates/registration`.  

#### Authentication  
Nous utilisons `rest_framework.authtoken`, la solution officielle DRF pour l’authentification par token :  
https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication  
Elle est largement adoptée, régulièrement maintenue et évite les pièges d’une implémentation “maison”.  

#### Pokemon  
Les données Pokémon et leurs types provenant d’une API tierce évoluent rarement.  
Nous avons créé des commandes dans `pokemon/management/commands` pour synchroniser :  

```bash
venv/bin/python manage.py <nom_du_fichier>
```

Ces commandes peuvent être automatisées (cron, CI/CD) et garantissent :

- Aucune requête externe à l’exécution de l’application.
- Fiabilité accrue en cas de pic de trafic ou de panne de l’API tierce.


Le QuerySet de Pokemon a été étendu pour abstraire la logique de filtrage et optimiser les requêtes SQL (voir pokemon/querysets.py).

Pour aller plus loin, on pourrait intégrer, entre autres :

- django_filters pour un filtrage avancé : https://www.django-rest-framework.org/api-guide/filtering/#djangofilterbackend
- drf-spectacular pour la documentation OpenAPI : https://www.django-rest-framework.org/topics/documenting-your-api/#drf-spectacular

#### Settings
Le fichier .env.json, intégré dans le code via l'objet env généré dans le fichier settings/jsonenv.py, permet de simuler un environnement réel sans exposer de secrets (SECRET_KEY auto-générée en mode debug). Dans un projet plus vaste, on aurait à priori séparé les settings en plusieurs fichiers :

- settings/base.py
- settings/authentication.py
- settings/rest_framework.py
- settings/database.py
- settings/development.py
- settings/production.py
- ...
