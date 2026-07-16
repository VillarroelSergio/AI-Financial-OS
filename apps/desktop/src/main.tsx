import React from "react";
import { isTauri } from "@tauri-apps/api/core";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { flushSync } from "react-dom";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { preloadAppData } from "./app/preloadAppData";
import { preloadSettingsOverview } from "./features/settings/settingsOverview";
import "./index.css";

// Aplicar tema antes del primer render para evitar flash
const savedTheme = localStorage.getItem("theme") || "dark";
document.documentElement.setAttribute("data-theme", savedTheme);

void preloadSettingsOverview();
void preloadAppData();

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

// Tauri crea la ventana oculta para que Windows no muestre el WebView blanco.
// El render sincronico garantiza que la experiencia de inicio ya existe al revelarla.
flushSync(() => {
  root.render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>
  );
});

if (isTauri()) {
  void getCurrentWindow().show();
}
