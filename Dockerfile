FROM python:3.11-slim

# Dossier de travail dans le conteneur
WORKDIR /app

# Configure timezone
ENV TZ=Europe/Paris
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Dépendances système nécessaires (notamment pour moviepy / ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    locales \
 && sed -i 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen fr_FR.UTF-8 \
 && update-locale LANG=fr_FR.UTF-8 LC_TIME=fr_FR.UTF-8 \
 && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code dans le conteneur
COPY . .

# Lance ton bot
CMD ["python", "calendrieravent.py"]
