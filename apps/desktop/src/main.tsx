import React from "react";
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

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
