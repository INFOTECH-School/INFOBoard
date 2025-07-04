## 2. Architektura systemu

W tej części omówimy ogólną strukturę INFOBoard, zależności między komponentami oraz role poszczególnych modułów.

### 2.1 Diagram komponentów

```text
+--------------------+          +---------------------+
|     Frontend       | <------> |  Backend (Django)   |
| (React + Excalidraw)|          | + Channels (WS)     |
+--------------------+          +---------------------+
            |                               |
            v                               v
       Przeglądarka                   System plików / DB
            |                               |
            v                               v
+--------------------+          +---------------------+
|   WebSocket Server | <------> | PostgreSQL / SQLite |
+--------------------+          +---------------------+
```

### 2.2 Opis modułów

#### 2.2.1 `client/`

* Kod frontendowy oparty na React i TypeScript.
* Komponenty Excalidraw do rysowania elementów.
* Obsługa routingu, autoryzacji i synchronizacji przez WebSocket.

#### 2.2.2 `collab/`

* Implementacja logiki współpracy w czasie rzeczywistym.
* Mechanizmy mergowania i rozgłaszania zmian między klientami.
* Zarządzanie stanem tablicy w pamięci oraz kolejką zdarzeń.

#### 2.2.3 `draw/`

* Integracja z Excalidraw: parser, renderer i serializator plików `.excalidraw`.
* Obsługa eksportu/importu i konwersji formatów.

#### 2.2.4 `dash/`

* Panel administracyjny i dashboard dla użytkowników z uprawnieniami.
* Widoki do zarządzania grupami, projektami i uprawnieniami.

#### 2.2.5 `devscripts/`

* Skrypty wspomagające pracę deweloperską:

  * Migracje testowe,
  * Czyszczenie bazy danych,
  * Generowanie danych testowych,
  * Narzędzia do profilowania.

### 2.3 Przepływ danych

1. **Inicjalizacja**: Klient pobiera aktualny stan tablicy z REST API.
2. **Edycja**: Zmiany generowane na kliencie są wysyłane przez WebSocket do serwera.
3. **Propagacja**: Serwer rozsyła zmiany do pozostałych podłączonych klientów.
4. **Zapis**: Serwer zapisuje zdarzenia w bazie danych lub plikach (w zależności od konfiguracji).

---
