import pkg from "../../../package.json";

export const APP_VERSION: string = pkg.version;
export const WELCOME_SEEN_KEY = "welcome-seen-version";

/** La guía se muestra en el primer arranque (app vacía) y tras cada cambio de versión. */
export const shouldShowWelcome = () => localStorage.getItem(WELCOME_SEEN_KEY) !== APP_VERSION;

export const markWelcomeSeen = () => localStorage.setItem(WELCOME_SEEN_KEY, APP_VERSION);
