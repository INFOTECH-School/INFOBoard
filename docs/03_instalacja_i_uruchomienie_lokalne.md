## 3. Instalacja i uruchomienie lokalne

Ten rozdział opisuje, jak przygotować środowisko programistyczne i uruchomić INFOBoard lokalnie.

### 3.1 Wymagania

* **Python** >= 3.8
* **Node.js** >= 14.x i **npm**
* **Docker** i **Docker Compose** (opcjonalnie, dla konteneryzacji)
* **Git** do klonowania repozytorium

### 3.2 Klonowanie repozytorium

```bash
git clone https://github.com/INFOTECH-School/INFOBoard.git
cd INFOBoard
```

### 3.3 Konfiguracja środowiska wirtualnego (Python)

1. Utwórz i aktywuj wirtualne środowisko:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\\Scripts\\activate # Windows
   ```
2. Zainstaluj zależności backendu:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 3.4 Instalacja zależności frontendowych

Przejdź do katalogu `client/` i zainstaluj pakiety:

```bash
cd client
npm install
```

### 3.5 Konfiguracja bazy danych

Domyślnie w trybie deweloperskim używany jest SQLite. Aby skonfigurować PostgreSQL:

1. Upewnij się, że masz uruchomiony kontener lub serwer PostgreSQL.
2. Utwórz bazę danych i użytkownika.
3. Skopiuj plik `.env.example` do `.env` i uzupełnij wartości:

   ```dotenv
   DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB_NAME
   SECRET_KEY=twoj_sekretny_klucz
   DEBUG=True
   ```

### 3.6 Migracje i dane początkowe

W katalogu głównym projektu uruchom:

```bash
python manage.py migrate
python manage.py loaddata initial_data.json  # opcjonalnie przykładowe dane
python manage.py createsuperuser
```

### 3.7 Uruchomienie aplikacji

#### 3.7.1 Ręczne uruchomienie

1. Backend (Django + Channels):

   ```bash
   python manage.py runserver
   ```
2. Frontend (React):

   ```bash
   cd client
   npm start
   ```

Aplikacja będzie dostępna pod adresem `http://localhost:8000`.

#### 3.7.2 Uruchomienie z Docker Compose

W katalogu głównym:

```bash
docker-compose up --build
```

Skorzystaj z przykładów konfiguracji w `docker-compose.example.yml` i `nginx-site.example.conf`, aby dostosować środowisko.

---
