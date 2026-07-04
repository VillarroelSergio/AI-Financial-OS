import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { shouldShowWelcome } from "./welcomeVersion";

/** Redirige el dashboard a la guía inicial en el primer arranque o tras una actualización. */
export default function WelcomeGate({ children }: { children: ReactNode }) {
  if (shouldShowWelcome()) return <Navigate to="/welcome" replace />;
  return <>{children}</>;
}
