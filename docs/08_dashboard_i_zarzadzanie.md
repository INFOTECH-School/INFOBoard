## 8. Dashboard i zarządzanie

Ten rozdział opisuje moduł `dash/` odpowiedzialny za panel administracyjny i funkcje zarządzania użytkownikami, grupami oraz pokojami.

### 8.1 Struktura modułu `dash/`

```
dash/
├── templates/               # Szablony HTML (Django).
│   ├── dash/dashboard.html  # Strona główna dashboardu.
│   ├── dash/groups.html     # Lista grup.
│   └── dash/rooms.html      # Lista pokoi.
├── views.py                 # Widoki Django.
├── urls.py                  # Definicje tras modułu.
├── forms.py                 # Formularze (tworzenie/edycja group, room).
└── permissions.py           # Niestandardowe uprawnienia.
```

### 8.2 Routing i dostęp

* `dash/urls.py` zawiera ścieżki:

  * `/dash/` – dashboard główny
  * `/dash/groups/` – zarządzanie grupami
  * `/dash/groups/<uuid:group_id>/` – szczegóły grupy
  * `/dash/rooms/` – zarządzanie pokojami
  * `/dash/rooms/<uuid:room_name>/` – szczegóły pokoju
* Wszystkie widoki chronione są dekoratorem `@login_required` i sprawdzają uprawnienia w `permissions.py`.

### 8.3 Zarządzanie grupami

* Widok listy grup: paginacja, wyszukiwanie po nazwie klasy lub roku.
* Formularze dodawania/edycji grup zawierają pola:

  * `class_name`, `class_year`, `category`, `code`, `owner`, `users`.
* Możliwość resetowania kodu dostępu generowanego losowo.

### 8.4 Zarządzanie pokojami

* Widok listy pokoi: filtrowanie po grupie, właścicielu i statusie (`active`, `archived`).
* Formularze tworzenia/edycji pokoju z polami:

  * `user_room_name`, `room_created_by`, `tracking_enabled`, `is_public`.
* Akcje masowe: archiwizacja lub usuwanie wybranych pokoi.

### 8.5 Uprawnienia i role

* Plik `permissions.py` definiuje klasy:

  * `IsGroupOwner` – tylko właściciel grupy może edytować.
  * `IsRoomCreator` – tylko twórca pokoju może modyfikować ustawienia.
* W widokach Django używane są mixiny:

  * `UserPassesTestMixin`, `PermissionRequiredMixin`.

### 8.6 Styl i UX

* Szablony oparte na Bootstrap 5.
* Responsywne tabele z paginacją.
* Komponenty JS do potwierdzania akcji (usuwanie, reset kodu).

### 8.7 Testy modułu Dashboard

* Testy jednostkowe widoków w `dash/tests.py`.
* Mockowanie uprawnień i formularzy przy użyciu `django.test`.

---
