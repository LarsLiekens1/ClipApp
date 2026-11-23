FROM python:3.11-slim

# Installeer systeemdependencies: FFmpeg voor videobewerking
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces vereist een niet-root gebruiker met UID 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1     HOST=0.0.0.0

WORKDIR $HOME/app

# Installeer Python packages
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Kopieer de rest van het project
COPY --chown=user:user . .

# Zorg dat de work-directory bestaat
RUN mkdir -p work

# Hugging Face Spaces routeert verkeer naar poort 7860
EXPOSE 7860

CMD ["python", "app.py"]
