import { useState } from "react";

/** Secuencia de entrada deliberada, separada de la carga de datos. */
export default function StartupExperience() {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  return (
    <div
      aria-hidden="true"
      className="app-launch-stage"
      onAnimationEnd={(event) => {
        if (event.target === event.currentTarget) setVisible(false);
      }}
    >
      <div className="app-launch-card">
        <span className="app-launch-glyph">
          <span className="app-launch-bar app-launch-bar-jade" />
          <span className="app-launch-bar app-launch-bar-blue" />
          <span className="app-launch-bar app-launch-bar-garnet" />
          <span className="app-launch-trace" />
        </span>
        <span className="app-launch-copy">
          <span className="app-launch-title">Financial OS</span>
          <span className="app-launch-subtitle">Tu espacio financiero</span>
        </span>
      </div>
    </div>
  );
}
