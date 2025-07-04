## 4. Konfiguracja produkcyjna

W tym rozdziale opisujemy przygotowanie środowiska produkcyjnego oraz konfigurację niezbędnych komponentów.

### 4.1 Pliki konfiguracyjne

* **`docker-compose.yml`** (przykład produkcyjny):

  * Definicje usług: `web`, `nginx`, `db`, `redis`.
  * Sieci i wolumeny do trwałego przechowywania danych.
* **`nginx-site.conf`** (przykład):

  * Proxy do usługi Django.
  * Obsługa statycznych i media files.
* **`Dockerfile`**:

  * Budowanie warstwy Pythona (z wykorzystaniem multi-stage build).
  * Instalacja zależności.
  * Kopiowanie kodu i plików statycznych.
* **`docker-entrypoint.sh`**:

  * Inicjalizacja migracji.
  * Kolejkowanie zadań (np. Celery, jeśli używany).

### 4.2 Zmienne środowiskowe

Skopiuj `.env.production.example` do `.env.production` i uzupełnij:

```dotenv
DEBUG=False
SECRET_KEY=twoj_sekretny_klucz
DATABASE_URL=postgres://USER:PASSWORD@DB_HOST:5432/DB_NAME
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=twoja_domena.com
STATIC_ROOT=/vol/web/static
MEDIA_ROOT=/vol/web/media

# Opcjonalnie: Celery
CELERY_BROKER_URL=$REDIS_URL
CELERY_RESULT_BACKEND=$REDIS_URL
```

### 4.3 Budowanie i uruchamianie

1. Zbuduj obrazy:

   ```bash
   ```

docker-compose -f docker-compose.yml -f docker-compose.override.yml build

````
2. Uruchom w tle:
   ```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
````

3. Sprawdź logi:

   ```bash
   ```

docker-compose logs -f web

### 4.4 Ustawienia serwera reverse-proxy
````

- Skopiuj `nginx-site.conf` do `/etc/nginx/sites-available/` i stwórz link symboliczny do `sites-enabled`.
- Przykładowa konfiguracja:
  ```nginx
  server {
      listen 80;
      server_name twoja_domena.com;

      location /static/ {
          alias /vol/web/static/;
      }

      location /media/ {
          alias /vol/web/media/;
      }

      location / {
          proxy_pass http://web:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
````

### 4.5 Monitoring i skalowanie

* **Healthchecks** w Docker Compose.
* Automatyczne restarty kontenerów.
* Skalowanie usługi web:

  ```bash
  ```

docker-compose up -d --scale web=3

---
