from moviepy.editor import (
    ImageClip,
    CompositeVideoClip,
    VideoClip,
    VideoFileClip,
    vfx,
    concatenate_videoclips,
)
import random
import os

# Taille de la vidéo
TAILLE = 600

# Dossier de sortie
OUTPUT_DIR = "roulettes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Fonction principale pour générer UNE vidéo ---
def genere_roulette(output_path: str):
    # Charger les images
    fond1 = ImageClip("fond1.png").resize((TAILLE, TAILLE))
    background_base = ImageClip("pied.png").resize((TAILLE, TAILLE))
    roue = ImageClip("roue.png").resize((TAILLE, TAILLE))
    fleche = ImageClip("fleche.png").resize((TAILLE, TAILLE)).set_opacity(0.7)

    # Mettre background_base sur fond1
    background = CompositeVideoClip([
        fond1,
        background_base.set_position(("center", "center")),
    ])

    # Paramètres de rotation (aléatoires pour chaque vidéo)
    vitesse_max = 100
    duree_rotation = round(random.uniform(6, 20), 3)
    duree_pause = 4

    def angle_a_t(t):
        return vitesse_max * (0.999999 ** t) * t

    angle_final = angle_a_t(duree_rotation)

    # Image finale figée
    roue_finale = roue.rotate(angle_final)
    frame_finale = CompositeVideoClip([
        background,
        roue_finale.set_position(("center", "center")),
        fleche.set_position(("center", "center")),
    ]).get_frame(0)

    # --- CLIP 1 : rotation ---
    def make_frame_rotation(t):
        angle = angle_a_t(t)
        roue_rotated = roue.rotate(angle)
        return CompositeVideoClip([
            background,
            roue_rotated.set_position(("center", "center")),
            fleche,
        ]).get_frame(0)

    clip_rotation = VideoClip(make_frame_rotation, duration=duree_rotation)

    # --- CLIP 2 : pause + confettis ---
    clip_pause_base = ImageClip(frame_finale).set_duration(duree_pause)

    confetti = (
        VideoFileClip("confetti.gif", has_mask=True)
        .resize((TAILLE, TAILLE))
        .fx(vfx.loop, duration=duree_pause)
    )

    clip_pause = CompositeVideoClip(
        [clip_pause_base, confetti.set_position(("center", "center"))]
    ).set_duration(duree_pause)

    # --- Assemblage final ---
    final_clip = concatenate_videoclips([clip_rotation, clip_pause])

    # Export
    final_clip.write_videofile(output_path, fps=30, codec="libx264", audio=False)

    # Nettoyage
    for c in (fond1, background_base, roue, fleche, confetti,
              clip_rotation, clip_pause, final_clip):
        try:
            c.close()
        except Exception:
            pass


# --- Génération des 25 vidéos ---
for jour in range(1, 26):
    filename = f"roulette_{jour}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)
    print(f"Génération de {output_path} ...")
    genere_roulette(output_path)

print("✅ Génération des 25 vidéos terminée.")