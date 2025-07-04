## 13. Zasady kontrybucji i licencja

W tym rozdziale opisujemy, jak można wnosić wkład do projektu INFOBoard oraz prezentujemy informacje dotyczące licencji.

### 13.1 Contributing (Wkład w projekt)

Aby usprawnić proces zgłaszania zmian i utrzymywania jakości kodu, stosujemy następujące wytyczne:

1. **Fork i branch**

   * Stwórz fork repozytorium INFOTECH-School/INFOBoard.
   * Utwórz branch opisujący zmianę, np. `feature/add-authentication` lub `fix/issue-123`.

2. **Style kodu**

   * Backend: PEP8, `flake8` z poziomu CI.
   * Frontend: `eslint` oraz `prettier`.
   * Nazwy commitów: krótkie, w trybie imperatywnym, np. `Add user login endpoint`.

3. **Testy**

   * Każda nowa funkcjonalność powinna być pokryta testami:

     * Testy jednostkowe dla backendu (pytest).
     * Testy komponentów React (Jest + React Testing Library).

4. **Pull Request (PR)**

   * Opisz cel PR w tytule i szczegóły w opisie.
   * Dodaj referencję do issue, np. `Fixes #123`.
   * CI musi być zielone: brak błędów lintera, testy przechodzą.

5. **Code review**

   * Recenzenci: minimum dwóch zatwierdzających.
   * Sprawdź zgodność z architekturą i zasadami projektowania.

6. **Merge**

   * Po zatwierdzeniu PR, automatyczne scalanie do `main` odbywa się przy pomocy GitHub Actions.

### 13.2 Licencja

Projekt INFOBoard jest udostępniony na podstawie licencji **GPL-3.0**. Oto najważniejsze postanowienia:

* **Darmowe użycie i modyfikacja**: każdy może używać, kopiować, modyfikować i rozpowszechniać kod.
* **Copyleft**: każde pochodne dzieło musi być udostępnione na tej samej licencji.
* **Brak gwarancji**: oprogramowanie dostarczane jest "as is" bez żadnych gwarancji.

Pełny tekst licencji znajduje się w pliku `LICENSE` w katalogu głównym repozytorium.

---

*To kończy dokumentację techniczną INFOBoard. Dziękujemy za uwagę!*
