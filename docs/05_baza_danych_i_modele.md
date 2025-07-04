## 5. Opis bazy danych i modeli

W tym rozdziale przedstawiamy strukturę baz danych oraz kluczowe modele Django używane w projekcie INFOBoard. Opisane tabele i relacje pozwalają na pełne zrozumienie logiki przechowywania danych.

### 5.1 Model `CustomUser`

Niestandardowy model użytkownika rozszerza `AbstractUser` i używa UUID jako klucz główny.

| Pole            | Typ             | Opis                                           |
| --------------- | --------------- | ---------------------------------------------- |
| `id`            | `UUIDField`     | PK, automatycznie generowany                   |
| `username`      | `CharField`     | Unikalny alias użytkownika                     |
| `email`         | `EmailField`    | Unikalny, służy jako login                     |
| `is_creator`    | `BooleanField`  | Flaga oznaczająca użytkownika tworzącego pokój |
| `profile_image` | `ImageField`    | Obrazek profilowy użytkownika                  |
| `is_active`     | `BooleanField`  | Czy konto jest aktywne                         |
| `is_staff`      | `BooleanField`  | Uprawnienia do panelu administracyjnego        |
| `date_joined`   | `DateTimeField` | Data utworzenia konta                          |

#### Relacje i manager

* `CustomUser` korzysta z managera `UserManager`, który obsługuje tworzenie zwykłych użytkowników oraz superużytkowników.

### 5.2 Model `ExcalidrawRoom`

Reprezentuje pojedynczy pokój (tablicę) z zawartością i ustawieniami.

| Pole               | Typ             | Opis                                           |
| ------------------ | --------------- | ---------------------------------------------- |
| `room_name`        | `UUIDField`     | PK, unikalny identyfikator pokoju              |
| `room_created_by`  | `ForeignKey`    | FK do `CustomUser`, tworzący pokój             |
| `user_room_name`   | `CharField`     | Przyjazna nazwa pokoju                         |
| `created_at`       | `DateTimeField` | Data utworzenia pokoju                         |
| `last_update`      | `DateTimeField` | Data ostatniej modyfikacji                     |
| `_elements`        | `BinaryField`   | Skompresowane dane JSON z elementami           |
| `tracking_enabled` | `BooleanField`  | Czy śledzenie zmian użytkowników jest włączone |

#### Mechanizmy

* `_elements` przechowuje serializowaną zawartość rysunku, kompresowaną dla oszczędności miejsca.

### 5.3 Model `ExcalidrawLogRecord`

Loguje zdarzenia (eventy) z komunikacji WebSocket dla analizy i odtwarzania historii.

| Pole             | Typ             | Opis                                                |
| ---------------- | --------------- | --------------------------------------------------- |
| `id`             | `AutoField`     | PK                                                  |
| `room_name`      | `UUIDField`     | Identyfikator pokoju                                |
| `event_type`     | `CharField`     | Typ zdarzenia (`full_sync`, `update_elements` itp.) |
| `user_pseudonym` | `CharField`     | Pseudonim użytkownika wykonującego akcję            |
| `_content`       | `BinaryField`   | Skompresowana zawartość zdarzenia (JSON)            |
| `_compressed`    | `BooleanField`  | Czy `_content` jest skompresowane                   |
| `created_at`     | `DateTimeField` | Data zapisania zdarzenia                            |

#### Użycie

* Każde otrzymane zdarzenie jest serializowane i zapisywane w tym modelu przed rozgłoszeniem.

### 5.4 Model `Pseudonym`

Mapuje użytkownika na pseudonim używany w danym pokoju.

| Pole             | Typ          | Opis                            |
| ---------------- | ------------ | ------------------------------- |
| `user_pseudonym` | `CharField`  | PK, unikalny pseudonim w pokoju |
| `room`           | `ForeignKey` | FK do `ExcalidrawRoom`          |
| `user`           | `ForeignKey` | FK do `CustomUser`              |

#### Cel

* Zapewnienie anonimowości użytkowników w konkretnych pokojach.

### 5.5 Model `ExcalidrawFile`

Przechowuje pliki importowane lub eksportowane z Excalidraw.

| Pole              | Typ          | Opis                                         |
| ----------------- | ------------ | -------------------------------------------- |
| `id`              | `AutoField`  | PK                                           |
| `belongs_to`      | `ForeignKey` | FK do `ExcalidrawRoom`, właściciel pliku     |
| `element_file_id` | `CharField`  | Identyfikator pliku w Excalidraw             |
| `content`         | `FileField`  | Przechowywany plik `.excalidraw`             |
| `meta`            | `JSONField`  | Metadane pliku (`mimeType`, `created`, itp.) |

### 5.6 Model `BoardGroups`

Grupy pokoi organizujące kursy lub projekty.

| Pole         | Typ               | Opis                                      |
| ------------ | ----------------- | ----------------------------------------- |
| `group_id`   | `UUIDField`       | PK, unikalny identyfikator grupy          |
| `class_name` | `CharField`       | Nazwa grupy (np. "kurs A")                |
| `class_year` | `IntegerField`    | Rok realizacji kursu                      |
| `category`   | `CharField`       | Poziom (np. `podstawowy`, `zaawansowany`) |
| `code`       | `CharField`       | Unikalny kod dostępu                      |
| `owner`      | `ForeignKey`      | FK do `CustomUser`, właściciel            |
| `users`      | `ManyToManyField` | Użytkownicy przypisani do grupy           |
| `rooms`      | `ManyToManyField` | Powiązane pokoje (`ExcalidrawRoom`)       |

#### Relacje

* Grupa łączy się z użytkownikami i pokojami poprzez pola M2M.

---
