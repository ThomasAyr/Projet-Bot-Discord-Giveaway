try:
    from PIL import Image
    if not hasattr(Image, "ANTIALIAS"):
        # équivalences vers Resampling
        Image.ANTIALIAS = Image.Resampling.LANCZOS    # type: ignore
        Image.BICUBIC   = Image.Resampling.BICUBIC    # type: ignore
        Image.BILINEAR  = Image.Resampling.BILINEAR   # type: ignore
except Exception:
    pass

from moviepy.editor import ImageClip, CompositeVideoClip, VideoClip
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import locale
from datetime import date, datetime
import io

# ---------------- CONFIG ----------------
IMAGE_PATH = r"cal2025/banniere.png"
FONT_PATH  = r"cal2025/soopafre.ttf" 
FONT_SIZE_DATE  = 70
FONT_SIZE_TITLE = 90
TEXT_COLOR = (255, 255, 255, 255)               # blanc
TEXT_COLOR_TITLE = (255, 215, 0, 255)          # doré
ADD_SHADOW = True
SHADOW_COLOR = (0, 0, 0, 180)                   # ombre noire
# ------------------------------------------

def date_fr_str(d: date) -> str:
    for loc in ("fr_FR.UTF-8", "French_France"):
        try:
            locale.setlocale(locale.LC_TIME, loc)
            break
        except locale.Error:
            continue
    try:
        day_name = d.strftime("%A").capitalize()
        month_name = d.strftime("%B").lower()
    except Exception:
        jours = ["lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"]
        mois  = ["janvier","février","mars","avril","mai","juin",
                 "juillet","août","septembre","octobre","novembre","décembre"]
        day_name   = jours[d.weekday()].capitalize()
        month_name = "décembre" #mois[d.month-1]
    day_str = "1er" if d.day == 1 else str(d.day)
    return f"{day_name} {day_str} {month_name} {d.year}"

def generer_image_avec_date(texte: str | None = None):
    now = datetime.now()
    d = now.date()

    # --- Jours spéciaux ---
    jours_speciaux = {
        6:  "Saint Nicolas",
        8:  "Fête des Lumières",
        21: "Solstice d'Hiver",
        24: "Réveillon de Noël",
        25: "Joyeux Noël",
    }
    titre_special = jours_speciaux.get(now.day, None)

    # Ligne date / gestion texte personnalisé
    if texte is None:
        texte_date = date_fr_str(d)
    else:
        if '$' in texte:
            titre_special = texte.split('$')[0].strip()
            texte_date   = texte.split('$')[1].strip()
        else:
            # pas de titre spécial si texte personnalisé sans "$"
            titre_special = None
            texte_date = texte

    # --- chargement image ---
    img = Image.open(IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # --- Fonctions utilitaires ---
    def get_size(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def draw_text(x, y, text, font, color):
        if ADD_SHADOW:
            for dx, dy in [(-2,-2),(2,-2),(2,2),(-2,2)]:
                draw.text((x+dx, y+dy), text, font=font, fill=SHADOW_COLOR)
        draw.text((x, y), text, font=font, fill=color)

    # --- Police titre (si besoin) ---
    if titre_special:
        try:
            font_title = ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE)
        except Exception:
            font_title = ImageFont.load_default()
        w_t, h_t = get_size(titre_special, font_title)
    else:
        font_title = None
        w_t = h_t = 0  # pas utilisé

    # --- Police date ---
    if titre_special:
        try:
            font_date = ImageFont.truetype(FONT_PATH, FONT_SIZE_DATE)
        except Exception:
            font_date = ImageFont.load_default()
    else:
        try:
            font_date = ImageFont.truetype(FONT_PATH, int(FONT_SIZE_DATE * 1.15))
        except Exception:
            font_date = ImageFont.load_default()
    w_d, h_d = get_size(texte_date, font_date)

    # --- Calcul des positions ---
    spacing = 20  # espace entre titre et date

    if titre_special:
        # on centre le bloc [titre + date]
        total_height = h_t + spacing + h_d
        y_top = (H - total_height) / 2

        # titre
        x_t = (W - w_t) / 2
        y_t = y_top

        # date
        x_d = (W - w_d) / 2
        y_d = y_t + h_t + spacing
    else:
        # pas de titre → on centre juste la date, vraiment au milieu
        x_d = (W - w_d) / 2
        y_d = (H - h_d) / 2

    # --- Dessin ---
    if titre_special and font_title:
        draw_text(x_t, y_t, titre_special, font_title, TEXT_COLOR_TITLE)

    draw_text(x_d, y_d, texte_date, font_date, TEXT_COLOR)

    # --- export ---
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf