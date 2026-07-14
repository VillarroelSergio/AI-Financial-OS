import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { preloadSettingsOverview } from "./features/settings/settingsOverview";
import "./index.css";

// Aplicar tema antes del primer render para evitar flash
const savedTheme = localStorage.getItem("theme") || "dark";
document.documentElement.setAttribute("data-theme", savedTheme);

// Las preferencias y el estado local se preparan durante el arranque para que Ajustes abra sin espera.
void preloadSettingsOverview();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
