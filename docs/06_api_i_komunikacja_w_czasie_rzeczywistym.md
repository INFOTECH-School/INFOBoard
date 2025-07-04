## 8. Moduły aplikacji i zarządzanie

W tym rozdziale przedstawiamy wszystkie aplikacje Django w projekcie INFOBoard oraz szczegółowy opis modułu `dash/` do interfejsu administracyjnego.

### 8.1 Przegląd aplikacji

Projekt zawiera następujące aplikacje Django:

| Aplikacja    | Opis                                                                           |
| ------------ | ------------------------------------------------------------------------------ |
| `collab`     | Logika współpracy w czasie rzeczywistym (WebSocket)                            |
| `draw`       | Integracja z Excalidraw (parser, renderer, serializacja)                       |
| `dash`       | Panel administracyjny (zarządzanie użytkownikami, grupami, pokojami)           |
| `devscripts` | Narzędzia developerskie (skrypty migracji, czyszczenia DB, generowania danych) |
| `client`     | Frontendowa aplikacja React/TypeScript (poza Django)                           |

### 8.2 Moduł `dash/`

Moduł `dash` odpowiada za interfejs webowy do zarządzania projektem.

#### 8.2.1 Struktura katalogu

```
<project_root>/dash/
├── templates/              # Szablony HTML Django
│   ├── dash/
│   │   ├── dashboard.html  # Główna strona dashboardu
│   │   ├── groups.html     # Lista i podgląd grup
│   │   └── rooms.html      # Lista i podgląd pokoi
├── views.py                # Widoki Django
├── urls.py                 # Trasowanie modułu
├── forms.py                # Formularze: grupy i pokoje
├── permissions.py          # Niestandardowe uprawnienia
└── tests.py                # Testy jednostkowe widoków
```

#### 8.2.2 Routing i zabezpieczenia

* Ścieżki w `dash/urls.py`:

  * `/dash/` – dashboard główny
  * `/dash/groups/` – zarządzanie grupami
  * `/dash/groups/<uuid:group_id>/` – szczegóły grupy
  * `/dash/rooms/` – zarządzanie pokojami
  * `/dash/rooms/<uuid:room_name>/` – szczegóły pokoju
* Wszystkie widoki opatrzone dekoratorem `@login_required`.
* Dodatkowo mixiny `UserPassesTestMixin` i `PermissionRequiredMixin`.

#### 8.2.3 Zarządzanie grupami

* Lista grup: paginacja i wyszukiwanie.
* Formularz dodawania/edycji grupy:

  * Pola: `class_name`, `class_year`, `category`, `code`, `owner`, `users`.
  * Możliwość resetowania kodu dostępu (generacja losowa).
* Widok szczegółów grupy: zarządzanie członkami i pokojami.

#### 8.2.4 Zarządzanie pokojami

* Lista pokoi: filtrowanie po grupie, właścicielu, statusie (`active`, `archived`).
* Formularz dodawania/edycji pokoju:

  * Pola: `user_room_name`, `room_created_by`, `tracking_enabled`, `is_public`, `groups`.
* Akcje masowe: archiwizacja, przywracanie, usuwanie pokoi.

#### 8.2.5 Uprawnienia

* `permissions.py` definiuje:

  * `IsGroupOwner` – tylko właściciel grupy może edytować.
  * `IsRoomCreator` – tylko twórca pokoju może modyfikować.
* Uprawnienia egzekwowane w widokach i formularzach.

#### 8.2.6 Testy modułu `dash`

* Testy w `dash/tests.py`:

  * Sprawdzają dostęp do widoków z różnymi rolami.
  * Walidację formularzy.
  * Prawidłowe generowanie kodów grup.

---
