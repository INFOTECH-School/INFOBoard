## 1. Wprowadzenie

### 1.1 Cel projektu

Projekt **INFOBoard** to interaktywna aplikacja typu "białej tablicy" (whiteboard), która umożliwia tworzenie i edycję diagramów oraz rysunków we współpracy wielu użytkowników w czasie rzeczywistym. Celem projektu jest dostarczenie lekkiego, łatwo rozszerzalnego narzędzia, które może być wykorzystywane zarówno w edukacji, jak i w środowisku biznesowym do burzy mózgów, prezentacji pomysłów oraz dokumentacji wizualnej.

### 1.2 Główne funkcje

* **Rysowanie i diagramy**: bogaty zestaw narzędzi do tworzenia linii, kształtów, tekstu i adnotacji.
* **Współpraca w czasie rzeczywistym**: synchronizacja zmian pomiędzy użytkownikami przy użyciu WebSocketów i Django Channels.
* **Zarządzanie projektami**: organizacja tablic w grupy i projekty, nadawanie uprawnień użytkownikom.
* **Integracja z Excalidraw**: możliwość importu/eksportu plików `.excalidraw` oraz korzystania z natywnych komponentów Excalidraw.
* **Dashboard administracyjny**: panel zarządzania użytkownikami, grupami oraz ustawieniami systemu.

### 1.3 Przegląd technologii

* **Backend**: Python 3.8+, Django 3.2+, Django Channels do obsługi komunikacji WebSocket.
* **Frontend**: TypeScript, React oraz komponenty Excalidraw dla zaawansowanej edycji rysunków.
* **Conteneryzacja**: Docker i Docker Compose do uproszczenia instalacji, rozwoju i wdrożeń.
* **Baza danych**: PostgreSQL jako domyślne rozwiązanie produkcyjne, SQLite w trybie deweloperskim.
* **CI/CD**: GitHub Actions do automatyzacji testów, lintowania i budowania obrazów Dockera.

---
