# Site UDRe
Variables d'environnement à définir sur l'hébergeur :
- SECRET_KEY : une longue chaîne aléatoire
- ADMIN_PASSWORD : le mot de passe de /admin
- DB_PATH : chemin de la base (ex. /var/data/udre.db sur Render avec disque persistant)
Commande de démarrage : gunicorn app:app
Test local : pip install -r requirements.txt puis python app.py
