import discord
from discord.ext import commands, tasks
import gspread
from google.oauth2.service_account import Credentials
import re
import locale
from datetime import datetime, timedelta, date
import random
from datetime import time, datetime
import asyncio
from utils_calendrieravent import *
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests
from dotenv import load_dotenv

# ---- CONFIG ----
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ID_SERVEUR_DISCORD = int(os.getenv("ID_SERVEUR_DISCORD"))

CHANNEL_PARTICIPATION = int(os.getenv("CHANNEL_PARTICIPATION"))     # salon participation
CHANNEL_ANNOUNCE = int(os.getenv("CHANNEL_ANNOUNCE"))               # salon annonce
CHANNEL_LOTS = int(os.getenv("CHANNEL_LOTS"))                       # salon lots
CHANNEL_PRIVE = int(os.getenv("CHANNEL_PRIVE"))                     # salon privé pour les messages d'alerte
QUESTION_DISCUSSION_CHANNEL_ID = 1438578111246762104  # salon où répondre aux questions

SPREADSHEET_NAME = "[Animation] Calendrier de l'Avent 2025"
CREDENTIALS_FILE = "credentials.json"

heure_tirage = 22  # heure du tirage
minute_tirage = 1 # minute du tirage

heure_debut_participation = 0 #h00
heure_fin_participation = 22 #h00
jour_debut_calendrier = datetime(2025, 1, 1)
jour_fin_calendrier = datetime(2025, 12, 25)

# ---- GOOGLE SHEETS ----
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME)

# Feuilles
participants_sheet = sheet.worksheet("Participants")
Participants_interdits_sheet = sheet.worksheet("Participants_interdits")
lots_sheet = sheet.worksheet("Lots")
recompenses_sheet = sheet.worksheet("Récompenses")
technique_sheet = sheet.worksheet("Technique")

# --- Jours spéciaux ---
jours_speciaux = {
    6:  "Saint Nicolas 🎅",
    8:  "Fête des Lumières 🕯️",
    21: "Solstice d'Hiver ❄️",
    24: "Réveillon de Noël 🎄",
    25: "Joyeux Noël 🎁",
}

# ---- QUESTIONS DU CALENDRIER ----
QUESTIONS = {
    1:  "Quel est ton plus beau souvenir de Noël sur Transformice ou ailleurs ? 🎄",
    2:  "Si tu pouvais offrir un cadeau à toute la communauté, ce serait quoi ? 🎁",
    3:  "Plutôt chocolat chaud, thé, café… ou autre boisson de saison ? ☕",
    4:  "Quel est ton item ou ta fourrure préférée en jeu, et pourquoi ? 🐭",
    5:  "Quelle musique ou chanson te met immédiatement dans l’ambiance de Noël ? 🎶",
    6:  "Raconte une petite anecdote drôle qui t’est arrivée pendant les fêtes. 😺",
    7:  "Tu préfères recevoir un cadeau-surprise ou choisir toi-même ? 🎲",
    8:  "Si tu pouvais créer une nouvelle carte spéciale Noël, à quoi elle ressemblerait ? 🧊",
    9:  "Quel est ton dessert de fêtes préféré ? 🍰",
    10: "Si tu étais un PNJ de Noël dans Transformice, quel serait ton rôle ? 🎅",
    11: "Tu joues plutôt en solo, en duo ou avec un gros groupe d’amis ? 👥",
    12: "Quelle est ta tradition de fin d’année que tu ne rates jamais ? ⭐",
    13: "Si tu pouvais passer une journée entière avec un seul joueur, qui choisirais-tu ? 💫",
    14: "Quel est le plus beau cadeau que tu aies reçu (ou offert) ? 🎀",
    15: "Plutôt maps normales, fun, event ou bootcamp pendant les vacances ? 🧀",
    16: "Si tu devais décrire ton année 2025 en un seul mot, ce serait lequel ? ✨",
    17: "Quelle est ta tenue / ton look préféré pour les fêtes (en jeu et IRL) ? 👗",
    18: "Tu préfères organiser des événements ou simplement y participer ? 🎉",
    19: "Si tu pouvais avoir une gourmandise à volonté,  laquelle choisirais-tu ? 💫",
    20: "Quelle est la chose la plus cosy pour toi en hiver ? 🛋️",
    21: "Plutôt chocolat chaud, thé, café... ou autre boisson de saison ? ☕",#"As-tu déjà fait une rencontre marquante grâce au jeu ? Raconte ! 💌",
    22: "Si tu pouvais transformer le gameplay en version Noël, que ferrais-tu ? 🧊",
    23: "Quel est ton objectif de souris pour l’année prochaine ? 🐭",
    24: "Quelle surprise de Noël t’a le plus marqué·e dans ta vie ? 🎇",
    25: "Que voudrais-tu dire à toute la communauté pour ce 25 décembre ? 💝",
}

def get_today_question():
    """Retourne la question du jour (1–25), ou None si hors période."""
    today_day = datetime.now().day
    return QUESTIONS.get(today_day)

# ---- DISCORD ----
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- COMMANDES ----
@bot.command()
@commands.has_permissions(administrator=True)
async def creer_messages_lots(ctx):
    channel = bot.get_channel(CHANNEL_LOTS)
    if not channel:
        await ctx.send("Salon introuvable.")
        return
    for day in range(1, 26): # du 1er au 25 décembre
        msg = await channel.send(f"{day} décembre 2025")

@bot.command()
@commands.has_permissions(administrator=True)
async def creer_banniere(ctx, *, texte: str = None):
    """Affiche dans la console le texte tapé après la commande"""
    if texte is None:
        await ctx.send("❌ Merci d’ajouter un texte après la commande.")
        return
    # Supprimer le message de la commande 
    await ctx.message.delete()
    # Générer l'image et l’envoyer
    image_buffer = generer_image_avec_date(texte)
    file = discord.File(image_buffer, filename="banniere_date.png")
    await ctx.send(file=file)

# ---- UTILITAIRES ----
def is_participation_valid(message_time):
    # Vérifie que la participation est dans le calendrier
    date_valide = jour_debut_calendrier.date() <= message_time.date() <= jour_fin_calendrier.date()
    # Vérifie que l'heure est bonne
    heure_valide = heure_debut_participation <= message_time.hour < heure_fin_participation
    return date_valide and heure_valide

def get_today_str():
    day = datetime.now().day  # renvoie un entier, 1 pour le 1er
    if day == 1:
        return "1er"
    return str(day)

# Vérifie si joueur déjà participé aujourd'hui
def already_participated(user_display, today):
    all_values = participants_sheet.get_all_values()
    for row in all_values:
        if len(row) >= 2 and row[0] == user_display and row[1] == today:
            return True
    return False

# Ajouter un participant
def add_participant(user_display, today, message, msg_time):
    participants_sheet.append_row([user_display, int(today), message, msg_time])

# Tirage au sort des lots
def draw_lots():
    today = get_today_str()
    # Récupérer les participants du jour
    all_values = participants_sheet.get_all_values()
    participants_today = [row[0] for row in all_values if len(row) >= 2 and row[1] == today]

    # Récupérer les lots du jour (chaque ligne = 1 lot)
    all_lots = lots_sheet.get_all_values()
    lots_today = [row for row in all_lots if len(row) >= 2 and row[0] == today]

    results = []
    if participants_today:
        for lot_row in lots_today:
            jour = lot_row[0]
            lot = lot_row[1]
            part = lot_row[2] if len(lot_row) > 2 else ""
            donateur = lot_row[3] if len(lot_row) > 3 else ""
            type = lot_row[4] if len(lot_row) > 4 else ""
            commentaire = lot_row[5] if len(lot_row) > 5 else ""

            participants_today_sans_le_donateur = [p for p in participants_today if p not in donateur]
            winner = random.choice(participants_today_sans_le_donateur)

            results.append((lot, part, donateur, winner, type, commentaire))

            # Enregistrer dans la feuille "Récompenses"
            recompenses_sheet.append_row([today, lot, part, winner, donateur, type])

    return results, len(participants_today)

def draw_roue():
    today = get_today_str()
    # Récupérer les participants du jour
    all_values = participants_sheet.get_all_values()
    participants_today = [row[0] for row in all_values if len(row) >= 2 and row[1] == today]

    if participants_today:
        winner = random.choice(participants_today)

        # Enregistrer dans la feuille "Récompenses"
        recompenses_sheet.append_row([today, "", "de la part de la", winner, "Roue des cadeaux", "🛞"])
        return winner, "un lot surprise de la Roue des cadeaux"
    return None, None

# ---- EVENTS ----
@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    draw_lots_task.start()  # démarrer la tâche quotidienne
    update_lots_task.start()
    send_message.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == CHANNEL_PARTICIPATION:
        now = datetime.now()
        if now.day >= 1 and now.day <= 25: # durant le calendrier de l'Avent du 1er au 25 décembre
            user_display = message.author.display_name
            today = get_today_str()
            time_str = (message.created_at + timedelta(hours=1)).strftime("%H:%M:%S")
            msg_time = message.created_at + timedelta(hours=1) #heure française hiver
            
            # dans Participants_interdits_sheet prendre dans une liste toute la colonne 1
            all_interdits = Participants_interdits_sheet.get_all_values()
            all_interdits = [row[0] for row in all_interdits if len(row) >= 1]

            print(f"Message de {user_display} {time_str} {msg_time} {message.content}")

            if is_participation_valid(msg_time):
                organisateurs = ["Tagathe#0000", "Cillanne#0010", "Wonder#0010", "Xxthomatexx#0000"]
                if already_participated(user_display, today) and user_display not in organisateurs:
                    await message.add_reaction("❌")
                    await message.reply("Ta participation a déjà été prise en compte aujourd'hui.")
                elif user_display in all_interdits:
                    await message.delete()
                    await bot.get_channel(CHANNEL_PRIVE).send(f"[Joueur interdit] ⚠️ Attention {user_display} essaie de participer, sa participation a été refusée et son message supprimé. Il s'agit d'un joueur tricheur.")
                    await message.author.send("⚠️ Désolé, tu ne peux pas participer au Calendrier de l'Avent.")
                    #await message.reply(f"⚠️ Désolé {user_display}, tu ne peux pas participer au tirage d'aujourd'hui.")
                elif not already_participated(user_display, today):
                    add_participant(user_display, today, message.content, time_str)
                    now = datetime.now()
                    if now.day == 6:
                        await message.add_reaction("🎅")
                    elif now.day == 8:
                        await message.add_reaction("🕯️")
                    elif now.day == 21:
                        await message.add_reaction("❄️")
                    elif now.day == 24:
                        await message.add_reaction("🎄")
                    elif now.day == 25:
                        await message.add_reaction("🎁")
                    else:
                        await message.add_reaction("🎉")                    
                    #await message.reply(f"🎉 Participation validée !")

    await bot.process_commands(message)

# ---- TÂCHE QUOTIDIENNE ----
@tasks.loop(minutes=1)  # vérifie chaque minute
async def draw_lots_task():
    now = datetime.now()
    if now.hour == heure_tirage and now.minute == minute_tirage and now.day >= 1 and now.day <= 25:
        print("Lancement du tirage au sort...", now)
        results, nb_participants = draw_lots()
        channel = bot.get_channel(CHANNEL_ANNOUNCE)

        if channel:
            # Générer l'image et l’envoyer
            image_buffer = generer_image_avec_date()
            file = discord.File(image_buffer, filename="banniere_date.png")
            await channel.send(file=file)

            await channel.send(
                f"# :christmas_tree::sparkles: Le Calendrier de l'Avent du {get_today_str()} décembre :confetti_ball:\n"
                f"Ce soir, **{nb_participants} participants** ont tenté leur chance pour être tiré au sort ! "
                f"**Plusieurs lots sont en jeu**, et la tension monte à **chaque pseudonyme annoncé**... "
                f"\nQui décrochera le premier ? Qui repartira avec le plus convoité ?\n"
                f"Le **hasard** est prêt à faire des **heureux**... préparez-vous ! 🎉\n<:space:1360661681583165470>"
            )
            msg = f"## :sparkles: Les tirages au sort du {get_today_str()} décembre 🎁\n\n"

            # Résultats du tirage
            for lot, part, donateur, winner, type, commentaire in results:
                lot = lot.lower()
                com = f", {commentaire}" if len(commentaire) > 5 and commentaire != "" else ""
                member_winner = discord.utils.get(channel.guild.members, display_name=winner)
                member_donateur = discord.utils.get(channel.guild.members, display_name=donateur)

                if member_winner:
                    if member_donateur:
                        msg += f"- {member_winner.mention} gagne **{lot}** {type}{com} ({part} {member_donateur.mention})\n"
                    else:
                        msg += f"- {member_winner.mention} gagne **{lot}** {type}{com} ({part} {donateur})\n"
                else:
                    if member_donateur:
                        msg += f"- {winner} gagne **{lot}** {type}{com} ({part} {member_donateur.mention})\n"
                    else:
                        msg += f"- {winner} gagne **{lot}** {type}{com} ({part} {donateur})\n"

            await channel.send(
                msg + "\nFélicitations aux gagnants et merci à nos généreux donateurs ! :tada:\n<:space:1360661681583165470>"
            )

            # Tirage de la roue des cadeaux
            roue_winner, roue_lot = draw_roue()
            member_roue_winner = discord.utils.get(channel.guild.members, display_name=roue_winner)
            if roue_winner: 
                # Message narratif
                await channel.send(
                    f"## :sparkles: La roue des cadeaux du {get_today_str()} décembre :wheel:\n"
                    f"Ho ho ho ! Le moment tant attendu est arrivé. Il est maintenant l'heure de **lancer la roue des cadeaux** ! 🎁🎄\n"
                    f"Et la roue s'arrête... sur...\n"
                )

                # Envoi de la vidéo
                video_path = r"cal2025/roulette.mp4" #creer_video_roulette()
                with open(video_path, "rb") as f:
                    await channel.send(file=discord.File(f, "roulette.mp4"))

                # Message narratif
                if member_roue_winner:                
                    await channel.send(
                        f"Félicitations, c'est **||{member_roue_winner.mention}||** qui remporte ce lot ! :tada:\n"
                        f"Bravo au gagnant et un grand merci à tous les participants.\n"
                        f"-# La roue des cadeaux a été imaginée et dessinée par Cillanne, puis mise en mouvement par Tagathe et Xxthomatexx. Bravo à eux !"
                        f"\n<:space:1360661681583165470>"
                    )
                else:
                    await channel.send(
                        f"Félicitations, c'est **||{roue_winner}||** qui remporte ce lot ! :tada:\n"
                        f"Bravo au gagnant et un grand merci à tous les participants.\n"
                        f"-# La roue des cadeaux a été imaginée et dessinée par Cillanne, puis mise en mouvement par Tagathe et Xxthomatexx. Bravo à eux !"
                        f"\n<:space:1360661681583165470>"                    
                    )

            # ---- Envoi de la quête surprise ----
            if now.day in jours_speciaux:
                question_surprise = f"## :sparkles: La quête surprise du {get_today_str()} décembre 🙀\n"
                question_surprise += f"Pour célébrer ce jour spécial {jours_speciaux[now.day]}, nous lançons une **quête surprise** ! 🎉\n"
                question_surprise += f"**Objectif** : Soyez le premier à poster une capture d'écran de votre souris portant un chapeau de Noël dans le salon <#{CHANNEL_PARTICIPATION}>.\n"
                question_surprise += f"**Récompense** : Le gagnant recevra un lot exclusif en plus des tirages habituels ! 🎁\n"
                question_surprise += f"Bonne chance à toutes et à tous ! :tada:\n"
                question_surprise += f"<:space:1360661681583165470>"
                await channel.send(question_surprise)

            # ---- Envoi de la question du jour ----
            question = get_today_question()
            if question:
                await channel.send(
                    f"## :sparkles: La question du jour du {get_today_str()} décembre :interrobang:\n"
                    f"> **{question}**\n\n"
                    f"Vous **pouvez y répondre** dans <#{QUESTION_DISCUSSION_CHANNEL_ID}>. Nous avons hâte de **lire vos réponses** ! :confetti_ball:"
                    f"\n<:space:1360661681583165470>"
                )

            # ---- Annonce des lots du lendemain ----
            tomorrow = now + timedelta(days=1)                
            if tomorrow.date() <= jour_fin_calendrier.date():
                all_lots = lots_sheet.get_all_values()
                tomorrow_lots = [row for row in all_lots if row[0] == str(tomorrow.day)]

                if tomorrow_lots:
                    tomorrow_msg = f"""## :sparkles: Les lots à gagner pour le {tomorrow.strftime('%d')} décembre 🎁\nPréparez-vous ! Les **lots de demain** réservent de __très belles surprises__ :\n"""
                    
                    for row in tomorrow_lots:
                        lot = row[1]
                        part = row[2] if len(row) > 2 else ""
                        donateur = row[3] if len(row) > 3 else ""
                        type = row[4] if len(row) > 4 else ""
                        commentaire = f"({row[5]}) " if len(row) > 5 and row[5] != "" else ""

                        #member_donateur = discord.utils.get(channel.guild.members, display_name=donateur)
                        #if member_donateur:
                        #    tomorrow_msg += f"- {type} **{lot}** {commentaire}{part} {member_donateur.mention}\n"
                        #else:
                        tomorrow_msg += f"- {type}  **{lot}** {commentaire}{part} {donateur}\n"

                    await channel.send(
                        tomorrow_msg
                        + "\nSi vous souhaitez aussi **offrir un lot**, n’hésitez pas à contacter un organisateur.\n"
                        + f"\nLes <#1434958487686746223> du **{tomorrow.strftime('%d')} décembre** s’ouvriront dès **0h00** et fermeront à **22h00**. Que **la chance** soit avec vous ! :sparkles:\n"
                    )


@tasks.loop(minutes=1)
async def update_lots_task():
    now = datetime.now()
    # Lancement toutes les 30 minutes
    if now.minute not in [15, 45]:
        return

    channel = bot.get_channel(CHANNEL_LOTS)
    if not channel:
        return

    # Récupérer toutes les lignes de la feuille "technique"
    all_rows = technique_sheet.get_all_values()
    
    for row in all_rows[1:]:  # on saute l'en-tête
        await asyncio.sleep(2)

        # Nettoyer l'ID du message
        msg_id_clean = row[0].replace(" ", "").replace("\u202f", "")
        try:
            target_message_id = int(msg_id_clean)
            jour = int(row[1])
        except ValueError:
            continue  # ignorer les lignes invalides

        # Récupérer les récompenses du jour correspondant
        all_rewards = lots_sheet.get_all_values()
        rewards_today = [r for r in all_rewards if r[0] == str(jour)]

        # Activer la locale française pour le jour
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        date_obj = datetime(2025, 12, jour)
        day_name = date_obj.strftime("%A").capitalize()
        day_str = "1er" if jour == 1 else str(jour)
        
        # Construire l'en-tête
        if jours_speciaux.get(jour, '') != '':
            header = f"### {day_name} {day_str} décembre 2025 :\n> **{jours_speciaux[jour]}**\n\n"
        else:
            header = f"### {day_name} {day_str} décembre 2025 :\n"

        # Construire la liste des lots
        if rewards_today:
            lines = []
            for r in rewards_today:
                if r[5] != "":
                    lines.append(f"- {r[4]} **{r[1]}** ({r[5]}) {r[2]} {r[3]}")
                else:
                    lines.append(f"- {r[4]} **{r[1]}** {r[2]} {r[3]}")
            content = header + "\n".join(lines)
        else:
            content = header + "- *Pour l’instant, il n'y a pas de lot prévu. Mais vous pouvez en offrir un si vous le souhaitez !*"

        # Éditer le message
        try:
            msg = await channel.fetch_message(target_message_id)
            await msg.edit(content=content)
        except Exception as e:
            print(f"Impossible de modifier le message {target_message_id}: {e}")

@tasks.loop(minutes=1)
async def send_message():
    now = datetime.now()
    if now.day >= 1 and now.day <= 25: # durant le calendrier de l'Avent du 1er au 25 décembre
        if now.hour == 0 and now.minute == 0:
            channel = bot.get_channel(CHANNEL_PARTICIPATION)
            if channel:
                # Générer l'image et l’envoyer
                image_buffer = generer_image_avec_date()
                file = discord.File(image_buffer, filename="banniere_date.png")
                await channel.send(file=file)
                # f"# :christmas_tree::sparkles: Le Calendrier de l'Avent du {get_today_str()} décembre :confetti_ball:\n"
                await channel.send(f"### **Les participations sont ouvertes !**\n"
                + f"> Vous pouvez maintenant **tenter votre chance** pour remporter les <#1434986755282440264> de ce jour en **écrivant un message** dans ce salon. Bonne chance à toutes et à tous. :tada:\n")

        elif now.hour == heure_fin_participation and now.minute == 0:
            channel = bot.get_channel(CHANNEL_PARTICIPATION)
            if channel:
                await channel.send(f"Fin des participations pour ce {get_today_str()} décembre. Les tirages au sort ont lieu en ce moment. Restez connectés pour découvrir les heureux gagnants ! 🎁")

@bot.event
async def on_guild_join(guild):
    if guild.id != ID_SERVEUR_DISCORD:
        await guild.leave()

bot.run(TOKEN)