# Debian 12. Debian 11 (bullseye) is past end of support: its security
# packages moved to archive.debian.org, so apt-get install 404s and the build
# fails - the same failure psychometric-reporter hit. wkhtmltopdf is 0.12.6 in both.
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    fonts-liberation \
    fonts-dejavu-core \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY main.py .

# The port comes from .env. Shell form on purpose: the exec form would hand
# uvicorn the literal text ${PORT} instead of the number.
ENV PORT=5011
EXPOSE ${PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-5011} --workers 3