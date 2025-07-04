## 10. Aplikacja `draw`

Moduł `draw` odpowiada za integrację z biblioteką Excalidraw: parsowanie, renderowanie oraz import/eksport plików `.excalidraw`.

### 10.1 Struktura katalogu

```text
draw/
├── adapters/             # Konwertery JSON <-> modele Django
│   ├── parser.py         # Parsowanie JSON Excalidraw do wewnętrznej formy
│   └── serializer.py     # Serializacja modeli do formatu Excalidraw
├── views.py              # Widoki importu/eksportu plików Excalidraw
├── urls.py               # Ścieżki REST API dla draw
├── models.py             # Model `ExcalidrawFile` (importowane pliki)
├── services.py           # Logika importu/eksportu, walidacja plików
└── tests.py              # Testy jednostkowe importu/eksportu
```

### 10.2 Import plików Excalidraw

* Endpoint: `PUT /api/rooms/{room_name}/files/{file_id}/`
* Widok `DrawImportView`:

  1. Odczytuje przesłany plik `.excalidraw`
  2. Parsuje JSON za pomocą `parser.py`
  3. Tworzy instancję `ExcalidrawFile` oraz zapisuje `_elements` do powiązanego `ExcalidrawRoom`
  4. Ustawia flagę `imported=True` i zwraca zserializowane dane rysunku

### 10.3 Eksport plików Excalidraw

* Endpoint: `GET /api/rooms/{room_name}/files/{file_id}/`
* Widok `DrawExportView`:

  1. Pobiera `ExcalidrawFile` lub aktualny stan pokoju
  2. Serializuje model do JSON Excalidraw przy pomocy `serializer.py`
  3. Zwraca plik do pobrania z nagłówkiem `Content-Type: application/json`

### 10.4 Adaptery JSON

#### 10.4.1 `parser.py`

* Funkcja `parse_excalidraw(data: dict) -> List[Element]`:

  * Waliduje strukturę JSON
  * Konwertuje obiekty `elements` na modele wewnętrzne

#### 10.4.2 `serializer.py`

* Funkcja `serialize_elements(elements: QuerySet) -> dict`:

  * Mapuje pola modeli na format `elements[]` dla Excalidraw
  * Dołącza metadane (`appState`, `version`)

### 10.5 Testy i walidacja

* Testy importu: sprawdzają poprawność parsowania przykładowych plików `.excalidraw`
* Testy eksportu: porównują wygenerowane JSON z oczekiwanym wzorcem

---
