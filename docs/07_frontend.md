## 7. Frontend

W tym rozdziale opisujemy strukturę projektu frontendowego, integrację z Excalidraw oraz mechanizmy synchronizacji stanu.

### 7.1 Struktura projektu `client/`

```
client/
├── public/               # Pliki statyczne (index.html, favicon)
├── src/
│   ├── components/       # Wspólne komponenty UI
│   ├── hooks/            # Niestandardowe hooki React
│   ├── contexts/         # Kontekst aplikacji (autoryzacja, socket)
│   ├── pages/            # Strony (RoomView, Dashboard, Login)
│   ├── services/         # Warstwa komunikacji HTTP i WS
│   ├── styles/           # Style globalne i zmienne SCSS
│   ├── App.tsx           # Główny komponent aplikacji
│   ├── index.tsx         # Punkt wejścia
│   └── routes.tsx        # Definicje tras React Router
├── package.json
├── tsconfig.json
└── .eslintrc.js
```

### 7.2 Integracja z Excalidraw

* Korzystamy z paczki `@excalidraw/excalidraw`
* Komponent `ExcalidrawWrapper`:

  * Przekazuje stan elementów do Excalidraw
  * Nasłuchuje zdarzeń `onChange` i serializuje nowe elementy
  * Udostępnia funkcje `exportToBlob`, `getScene` itp.

### 7.3 Synchronizacja stanu przez WebSocket

* Hook `useRoomSocket(roomName: string)`:

  * Łączy się z `ws://<host>/ws/rooms/${roomName}/collaborate/`
  * Wysyła wiadomości `update_elements` po każdej zmianie
  * Odbiera `full_sync` i `update_elements`, aktualizuje lokalny stan

Przykład użycia w `RoomPage`:

```tsx
const { elements, sendUpdate } = useRoomSocket(roomName);
return (
  <ExcalidrawWrapper
    initialData={elements}
    onChange={(changedElements) => sendUpdate(changedElements)}
  />
);
```

### 7.4 Komponenty kluczowe

* **`LoginForm`**: obsługa logowania (JWT / cookies)
* **`RoomList`**: lista dostępnych pokoi, odświeżana przez REST API
* **`RoomPage`**: widok edycji tablicy, integruje Excalidraw i socket
* **`GroupDashboard`**: zarządzanie grupami i pokojami

### 7.5 Stylowanie i zasoby statyczne

* SCSS + CSS Modules dla izolacji stylów
* Zmienne kolorów i mixiny w `styles/variables.scss`
* Obrazy i ikony w `public/assets/`

### 7.6 Testy frontendowe

* Testy jednostkowe z `Jest` i `React Testing Library`
* Przykład testu komponentu:

```tsx
it('renders login form', () => {
  render(<LoginForm />);
  expect(screen.getByLabelText('Email')).toBeInTheDocument();
});
```

---
