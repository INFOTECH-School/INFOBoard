import React from "react"
import type { ConfigProps } from "../types"

export default function TopRightUI(config: ConfigProps) {

  return () => (
    <div className="topright Island App-toolbar" style={{ "--padding": 1 } as any}>
      <label
        title="Wróć"
        onClick={() => window.history.back()}
        className="zen-mode-transition"
      >
        {/* Ukryty checkbox, aby zachować styl Excalidraw */}
        <input
          className="ToolIcon_type_checkbox"
          type="checkbox"
          aria-label="Wróć"
          aria-keyshortcuts="0"
        />

        {/*
          Nadpisujemy styl, aby usunąć tło (background, boxShadow, border).
          Dzięki temu przycisk będzie wyglądał podobnie do "Library",
          ale bez wypełnionego tła.
        */}
        <div
          className="sidebar-trigger default-sidebar-trigger"
          style={{
            background: "none",
            boxShadow: "none",
            border: "none",
          }}
        >
          {/*
            .sidebar-trigger__label – tekst i/lub ikona.
            Dodajemy styl, żeby ikona i napis były obok siebie (inline-flex).
          */}
          <div
            className="sidebar-trigger__label"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            {/* Ikona strzałki (SVG), którą podałeś */}
            <svg
              aria-hidden="true"
              focusable="false"
              role="img"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="1.25"
              width="20"
              height="20"
            >
              <path d="M7.5 10.833 4.167 7.5 7.5 4.167M4.167 7.5h9.166a3.333 3.333 0 0 1 0 6.667H12.5"></path>
            </svg>

            {/* Napis "Wróć" */}
            <span>Wróć</span>
          </div>
        </div>
      </label>
    </div>
  )
}
