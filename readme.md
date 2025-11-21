# Bot Calendrier de l'Avent Transformice

Automatisation complète du Calendrier de l'Avent organisé sur un serveur Discord : collecte des participations quotidiennes, tirages au sort connectés à Google Sheets, annonces enrichies (bannières, vidéo de la roue), gestion des lots et rappels automatiques.

## Fonctionnalités principales

- Vérification des participations dans le salon dédié (contrôle des horaires, double participations et liste noire).
- Synchronisation avec Google Sheets (participants, lots, récompenses, feuilles techniques) pour garder tous les historiques dans un même fichier.
- Tirage automatique quotidien avec synthèse des gagnants, question du jour, quête surprise sur les dates spéciales et annonce des lots du lendemain.
- Publication d'une bannière datée générée avec Pillow et d'une vidéo de la roue des cadeaux.
- Commandes administrateur pour créer les messages d'annonce des lots et générer une bannière personnalisée.
- Dockerfile prêt à l'emploi pour déployer rapidement le bot sur un serveur isolé (timezone Europe/Paris, ffmpeg, locales FR).

## Prérequis

- Python 3.11+ 
- Un bot Discord configuré (token + accès aux salons mentionnés plus bas).
- Google Cloud Service Account avec accès au Google Sheet (fichier JSON de clés).
- ffmpeg installé localement (nécessaire pour MoviePy si vous n'utilisez pas Docker).
- Variables d'environnement listées ci-dessous et un accès aux assets du dossier `cal2025/`.

## Installation locale

```bash
git clone <url-du-repo>
cd <nom-du-repo>
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp <service-account>.json credentials.json
```

Les assets graphiques et la police utilisés pour la bannière/roulette sont déjà présents dans `cal2025/`. Si vous les remplacez, gardez les mêmes noms de fichiers ou ajustez `utils_calendrieravent.py`.

## Configuration (.env)

Créez un fichier `.env` (non versionné) à la racine :

```env
DISCORD_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ID_SERVEUR_DISCORD=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CHANNEL_PARTICIPATION=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CHANNEL_ANNOUNCE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CHANNEL_LOTS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CHANNEL_PRIVE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Les ID doivent correspondre aux salons suivants :
- `CHANNEL_PARTICIPATION` : où les joueurs postent leur participation quotidienne.
- `CHANNEL_ANNOUNCE` : annonces officielles des tirages, questions du jour, lots à venir.
- `CHANNEL_LOTS` : messages édités automatiquement pour tenir à jour la liste des lots.
- `CHANNEL_PRIVE` : alertes staff (ex. tentative de participation d'un joueur interdit).
- `QUESTION_DISCUSSION_CHANNEL_ID` : où les joueurs postent répondent à la question du jour.

## Configuration Google Sheets

Le fichier `[Animation] Calendrier de l'Avent 2025` doit contenir les onglets suivants :
- `Participants` : `[Pseudo, Jour, Message, Heure]`.
- `Participants_interdits` : `[Pseudo]`.
- `Lots` : `[Jour, Nom du lot, Formule type "Offert par", Donateur, Type, Commentaire optionnel]`.
- `Récompenses` : rempli automatiquement par le bot lors des tirages.
- `Technique` : utilisé pour mettre à jour les messages du salon lots (`[ID message, Jour]` principalement).

Partagez le Google Sheet avec l'adresse du service account utilisé dans `credentials.json` (droit Éditeur).

## Lancement

### Python
```bash
python calendrieravent.py
```
Le bot se connecte puis lance les trois tâches planifiées :
- `draw_lots_task` : tirage quotidien (22h01 par défaut) + envoi des annonces complètes.
- `update_lots_task` : rafraîchit les messages du salon des lots toutes les 30 minutes.
- `send_message` : ouverture automatique du salon de participation à minuit et fermeture à 22h.

### Docker
```bash
docker build --no-cache -t cal2025 .

# Si besoin
docker stop calbot2025
docker rm calbot2025

docker run -d --name calbot2025 --env-file .env cal2025
```
Montez `credentials.json` et les assets en lecture seule pour sécuriser le conteneur.

## Commandes Discord

- `!creer_messages_lots` (admin) : poste 25 messages (un par jour) dans `CHANNEL_LOTS` qui seront ensuite mis à jour automatiquement selon Google Sheets.
- `!creer_banniere <texte>` (admin) : génère la bannière à partir du texte fourni. Utilisez la syntaxe `Titre spécial $ Ligne date` pour afficher les deux lignes (par ex. `Saint Nicolas $ Vendredi 6 décembre 2025`).

## Structure du dépôt

- `calendrieravent.py` : logique principale du bot Discord.
- `utils_calendrieravent.py` : génération de la bannière, outil vidéo de la roue.
- `cal2025/` : images, police et vidéo utilisées dans les annonces.
- `requirements.txt` : dépendances Python.
- `Dockerfile` : image prête pour déployer le bot.

## Conseils d'exploitation

- Surveillez les logs (stdout) pour détecter les problèmes de connexion Discord ou Google Sheets.
```bash
docker logs calbot2025
```
- Adaptez `QUESTIONS`, `jours_speciaux`, `heure_tirage`, `heure_fin_participation` et la période (`jour_debut_calendrier`, `jour_fin_calendrier`) pour les prochaines éditions.